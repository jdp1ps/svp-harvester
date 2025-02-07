from loguru import logger
from semver import Version
from similarity.jarowinkler import JaroWinkler
from similarity.normalized_levenshtein import NormalizedLevenshtein

from app.config import get_app_settings
from app.db.models.abstract import Abstract
from app.db.models.contributor_identifier import ContributorIdentifier
from app.db.models.issue import Issue
from app.db.models.journal import Journal
from app.db.models.reference import Reference
from app.db.models.reference_identifier import ReferenceIdentifier
from app.db.models.title import Title
from app.harvesters.abstract_references_converter import AbstractReferencesConverter
from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.json_harvester_raw_result import (
    JsonHarvesterRawResult as JsonRawResult,
)
from app.harvesters.scanr.scanr_document_type_converter import (
    ScanrDocumentTypeConverter,
)
from app.harvesters.scanr.scanr_roles_converter import ScanrRolesConverter
from app.services.book.book_data_class import BookInformations
from app.services.concepts.concept_informations import ConceptInformations
from app.services.hash.hash_key import HashKey
from app.services.issue.issue_data_class import IssueInformations
from app.services.journal.journal_data_class import JournalInformations
from app.utilities.date_utilities import check_valid_iso8601_date
from app.utilities.string_utilities import normalize_string

LEVENSHTEIN_CONCEPT_LABELS_SIMILARITY_THRESHOLD = 0.3
JARO_WINKLER_CONCEPT_LABELS_SIMILARITY_THRESHOLD = 0.16


class ScanrReferencesConverter(AbstractReferencesConverter):
    """
    Converts raw data from ScanR to a normalised Reference object
    """

    PREFERRED_LANGUAGE = "fr"

    IDENTIFIERS_TO_IGNORE = ["scanr"]

    CONTRIBUTORS_IDENTIFIERS_TYPE_MAPPING = {
        "idref": ContributorIdentifier.IdentifierType.IDREF.value,
        "orcid": ContributorIdentifier.IdentifierType.ORCID.value,
        "id_hal": ContributorIdentifier.IdentifierType.IDHAL_S.value,
    }

    SOURCE_MAPPING = {
        "wikidata": ConceptInformations.ConceptSources.WIKIDATA,
        "sudoc": ConceptInformations.ConceptSources.IDREF,
        "keyword": None,
    }

    def __init__(self):
        super().__init__()
        self.normalized_levenstein = NormalizedLevenshtein()
        self.jaro_winkler = JaroWinkler()

    @AbstractReferencesConverter.validate_reference
    async def convert(self, raw_data: JsonRawResult, new_ref: Reference) -> None:
        """
        Convert raw data from Scanr to a normalised Reference object
        :param raw_data: raw data from Scanr
        :param new_ref: Reference object
        :return: None
        """
        json_payload = raw_data.payload

        title = json_payload["_source"].get("title")
        if title:
            new_ref.titles.extend(
                self._remove_duplicates_from_language_data(title, Title)
            )

        summary = json_payload["_source"].get("summary")
        if summary:
            new_ref.abstracts.extend(
                self._remove_duplicates_from_language_data(summary, Abstract)
            )

        document_type_code = json_payload["_source"].get("type")
        if document_type_code:
            new_ref.document_type.append(await self._document_type(document_type_code))

        domains = json_payload["_source"].get("domains")
        if domains:
            async for subject in self._concepts(domains):
                new_ref.subjects.append(subject)

        await self._add_contributions(json_payload, new_ref)

        issue = json_payload["_source"].get("publicationDate")
        if issue:
            self._add_issued_date(issue, json_payload, new_ref)

        journal = await self._journal(json_payload)

        if journal:
            issue = await self._issue(journal)
            new_ref.issue = issue

        if ("Book" in [dc.label for dc in new_ref.document_type]) or (
            "Chapter" in [dc.label for dc in new_ref.document_type]
        ):
            book = await self._book(json_payload)
            if book:
                new_ref.book = book

        for identifier in self._add_identifiers(json_payload):
            new_ref.identifiers.append(identifier)

    def _add_issued_date(self, issue, json_payload, new_ref):
        new_ref.raw_issued = issue
        try:
            new_ref.issued = check_valid_iso8601_date(new_ref.raw_issued)
        except UnexpectedFormatException as error:
            logger.error(
                f"ScanR reference converter cannot create issued date from publicationDate in"
                f" ScanR reference {json_payload['_id']}: {error}"
            )

    def _harvester(self) -> str:
        return "ScanR"

    async def _book(self, json_payload: dict) -> Journal | None:
        source = json_payload["_source"].get("source", {})
        if not source:
            return None
        title = source.get("title", "")
        publisher = source.get("publisher", "")
        if not title:
            return None
        return await self._get_or_create_book(
            BookInformations(title=title, publisher=publisher, source="scanr")
        )

    async def _issue(self, journal: Journal) -> Issue:
        source_identifier = (
            normalize_string("-".join(journal.titles)) + "-" + self._harvester()
        )
        issue = await self._get_or_create_issue(
            IssueInformations(
                source=self._harvester(),
                journal=journal,
                source_identifier=source_identifier,
            )
        )
        return issue

    async def _journal(self, json_payload: dict) -> Journal | None:
        if json_payload["_source"].get("source") == {}:
            return None
        title = json_payload["_source"].get("source").get("title")
        if not title:
            logger.error(
                "Journal title is missing in the ScanR source field "
                f"for the ScanR reference {json_payload['_id']}"
            )
            title = "Missing ScanR journal title"
        issn = json_payload["_source"].get("source").get("journalIssns", [])
        publisher = json_payload["_source"].get("source").get("publisher")
        journal = await self._get_or_create_journal(
            JournalInformations(
                source=self._harvester(),
                source_identifier="-".join(issn)
                + "-"
                + str(normalize_string(title))
                + "-"
                + str(normalize_string(publisher))
                + "-"
                + self._harvester(),
                issn=issn,
                publisher=publisher,
                titles=[title],
            )
        )
        return journal

    def _add_identifiers(self, json_payload: dict) -> ReferenceIdentifier:
        external_ids = json_payload["_source"].get("externalIds", [])
        for identifier in external_ids:
            if identifier["type"] not in self.IDENTIFIERS_TO_IGNORE:
                yield ReferenceIdentifier(
                    value=identifier["id"], type=identifier["type"]
                )

    async def _add_contributions(self, json_payload: dict, new_ref: Reference) -> None:
        raw_contributions = json_payload["_source"].get("authors")
        contribution_informations = []
        for rank, contribution in enumerate(raw_contributions):
            raw_identifiers = contribution.get("denormalized", {})
            contribution_informations.append(
                AbstractReferencesConverter.ContributionInformations(
                    role=ScanrRolesConverter.convert(
                        role=contribution.get("role"),
                    ),
                    name=contribution.get("fullName"),
                    first_name=contribution.get("firstName"),
                    last_name=contribution.get("lastName"),
                    identifier=contribution.get(
                        "person", contribution.get("toIdentify")
                    ),
                    rank=rank,
                    ext_identifiers=self._convert_external_identifiers(raw_identifiers),
                )
            )
        async for contribution in self._contributions(
            contribution_informations=contribution_informations, source="scanr"
        ):
            new_ref.contributions.append(contribution)

    def _convert_external_identifiers(
        self, raw_identifiers: dict
    ) -> list[dict[str, str]]:
        return [
            {"type": self.CONTRIBUTORS_IDENTIFIERS_TYPE_MAPPING[key], "value": value}
            for key, value in raw_identifiers.items()
            if key in self.CONTRIBUTORS_IDENTIFIERS_TYPE_MAPPING
        ]

    @staticmethod
    def _remove_duplicates_from_language_data(language_data: dict, model_class):
        processed_items = [
            model_class(value=value, language=key)
            for key, value in language_data.items()
            if key != "default"
        ]

        default_item = language_data.get("default")

        if default_item:
            if not any(item for item in processed_items if item.value == default_item):
                processed_items.append(model_class(value=default_item, language=None))

        return processed_items

    async def _document_type(self, code_document_type: str):
        uri, label = ScanrDocumentTypeConverter().convert(
            document_type=code_document_type
        )
        return await self._get_or_create_document_type_by_uri(uri, label)

    async def _concepts(self, domains):
        subjects_with_source = []
        subjects_without_source = []

        for subject in domains:
            if self._get_concept_source(subject.get("type")) is not None:
                subjects_with_source.append(subject)
            else:
                subjects_without_source.append(subject)
        labels_with_source = {}
        for subject in subjects_with_source:
            concept_id = subject.get("code")

            concept_type = subject.get("type")
            concept_source = self._get_concept_source(concept_type)

            label_dict = subject.get("label", {})
            concept_label, concept_language = self._get_concept_label(label_dict)

            db_concept = await self._get_or_create_concept_by_uri(
                ConceptInformations(
                    code=concept_id,
                    label=concept_label,
                    language=concept_language,
                    source=concept_source,
                )
            )
            for label in db_concept.labels:
                labels_with_source.setdefault(label.language, []).append(label.value)
            yield db_concept

        for subject in subjects_without_source:
            label_dict = subject.get("label", {})
            concept_label, concept_language = self._get_concept_label(label_dict)
            labels_to_compare_to = []
            if concept_language is not None and concept_language in labels_with_source:
                labels_to_compare_to = labels_with_source[concept_language]
            else:
                labels_to_compare_to = [
                    label for labels in labels_with_source.values() for label in labels
                ]

            if any(
                self._duplicate_or_almost(concept_label, label_to_compare_to)
                for label_to_compare_to in labels_to_compare_to
            ):
                continue
            labels_with_source.setdefault(concept_language, []).append(concept_label)
            db_concept = await self._get_or_create_concept_by_label(
                ConceptInformations(
                    label=concept_label,
                    language=concept_language,
                )
            )
            yield db_concept

    @staticmethod
    def _get_concept_source(concept_type):
        if concept_type not in ScanrReferencesConverter.SOURCE_MAPPING:
            logger.warning(f"Unknown Scanr subject type: {concept_type}")

        return ScanrReferencesConverter.SOURCE_MAPPING.get(concept_type, None)

    def _get_concept_label(self, label_dict):
        settings = get_app_settings()
        concept_label = None
        concept_language = None
        for langage in settings.concept_languages:
            concept_label = label_dict.get(langage)
            if concept_label is not None:
                concept_language = langage
                break
        if concept_label is None:
            concept_label, concept_language = self._get_non_default_label(label_dict)
        return concept_label, concept_language

    @staticmethod
    def _get_non_default_label(label_dict):
        for language, value in label_dict.items():
            if language != "default":
                return value, language
        return label_dict.get("default"), None

    def hash_keys(self, harvester_version: Version) -> list[HashKey]:
        # This listing is independant of PUBLICATIONS_DEFAULT_FIELDS
        # in ScanRApiQueryBuilder
        # pylint: disable=duplicate-code
        return [
            HashKey("id"),
            HashKey("title"),
            HashKey("summary"),
            HashKey("type"),
            HashKey("productionType"),
            HashKey("publicationDate"),
            HashKey("domains"),
            HashKey("affiliations"),
            HashKey("authors"),
            HashKey("externalIds"),
        ]

    def _duplicate_or_almost(self, compared_label, compared_to_label):
        if compared_label == compared_to_label:
            return True
        compared_label_norm = normalize_string(compared_label)
        compared_to_label_norm = normalize_string(compared_to_label)
        if compared_label_norm == compared_to_label_norm:
            return True

        levenshtein_dist = self.normalized_levenstein.distance(
            compared_label_norm, compared_to_label_norm
        )

        jaro_winkler_dist = self.jaro_winkler.distance(
            compared_label_norm, compared_to_label_norm
        )

        return (
            levenshtein_dist < LEVENSHTEIN_CONCEPT_LABELS_SIMILARITY_THRESHOLD
            and jaro_winkler_dist < JARO_WINKLER_CONCEPT_LABELS_SIMILARITY_THRESHOLD
        )
