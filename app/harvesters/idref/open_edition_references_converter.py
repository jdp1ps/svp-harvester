from typing import Generator
from xml.etree import ElementTree

import rdflib
from loguru import logger
from semver import Version

from app.db.models.abstract import Abstract
from app.db.models.issue import Issue
from app.db.models.journal import Journal
from app.db.models.reference import Reference
from app.db.models.reference_identifier import ReferenceIdentifier
from app.db.models.title import Title
from app.harvesters.abstract_references_converter import AbstractReferencesConverter
from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.idref.open_edition_document_type_converter import (
    OpenEditionDocumentTypeConverter,
)
from app.harvesters.idref.open_edition_roles_converter import (
    OpenEditionRolesConverter,
)
from app.harvesters.xml_harvester_raw_result import XMLHarvesterRawResult
from app.services.concepts.concept_informations import ConceptInformations
from app.services.hash.hash_key import HashKey
from app.services.hash.hash_key_xml import HashKeyXML
from app.services.issue.issue_data_class import IssueInformations
from app.services.journal.journal_data_class import JournalInformations
from app.utilities.date_utilities import check_valid_iso8601_date
from app.utilities.string_utilities import normalize_string


class OpenEditionReferencesConverter(AbstractReferencesConverter):
    """
    Convert the publication from the OpenEdition to a normalised Reference object
    """

    NAMESPACES = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": rdflib.DCTERMS,
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "qdc": "http://www.bl.uk/namespaces/oai_dcq/",
    }

    def __init__(self):
        self.tree_root: ElementTree = None

    def _harvester(self) -> str:
        return "Idref"

    @AbstractReferencesConverter.validate_reference
    async def convert(
        self, raw_data: XMLHarvesterRawResult, new_ref: Reference
    ) -> None:
        new_ref.titles.append(self._title(self._get_root(raw_data)))
        for abstract in self._abstracts(self._get_root(raw_data)):
            new_ref.abstracts.append(abstract)

        async for subject in self._subjects(self._get_root(raw_data)):
            if subject.id is None or subject.id not in list(
                map(lambda s: s.id, new_ref.subjects)
            ):
                new_ref.subjects.append(subject)

        for identifier in self._reference_identifier(self._get_root(raw_data)):
            new_ref.identifiers.append(identifier)

        new_ref.document_type.append(
            await self._document_type(self._get_root(raw_data))
        )

        self._get_issued_date(self._get_root(raw_data), new_ref)
        self._get_created_date(self._get_root(raw_data), new_ref)

        journal = await self._get_journal(self._get_root(raw_data))
        if journal is not None:
            issue = await self._get_issue(self._get_root(raw_data), journal)
            new_ref.issue = issue

        await self._add_contributions(new_ref, self._get_root(raw_data))

    async def _get_journal(self, root: ElementTree) -> Journal | None:
        publishers = [publisher for publisher, _ in self._get_terms(root, "publisher")]
        logger.debug(f"Publishers: {publishers}")
        if len(publishers) == 0:
            return None
        return await self._get_or_create_journal(
            journal_informations=JournalInformations(
                source="openedition",
                source_identifier=f"{normalize_string('-'.join(publishers))}-openedition",
                titles=publishers[:-1],
                publisher=publishers[-1],
            )
        )

    async def _get_issue(self, root: ElementTree, journal: Journal) -> Issue:
        rights = self._get_term(root, "rights")
        logger.debug(f"Rights: {rights}")
        return await self._get_or_create_issue(
            issue_informations=IssueInformations(
                source="openedition",
                source_identifier=(
                    f"{journal.source_identifier}"
                    f"-{normalize_string(rights)}-openedition"
                ),
                rights=rights,
                journal=journal,
            )
        )

    def _reference_identifier(
        self, root: ElementTree
    ) -> Generator[ReferenceIdentifier, None, None]:
        for identifier in self._get_terms(root, "identifier"):
            if identifier[1]["scheme"] == "URI":
                yield ReferenceIdentifier(
                    value=identifier[0],
                    type="uri",
                )
            elif identifier[1]["scheme"] == "URN" and "urn:doi:" in identifier[0]:
                yield ReferenceIdentifier(
                    value=identifier[0].replace("urn:doi:", ""),
                    type="doi",
                )

    async def _add_contributions(self, new_ref: Reference, root: ElementTree) -> None:
        contribution_informations = []
        for open_edition_quality, contributors in [
            (open_edition_role, self._get_terms(root, open_edition_role))
            for open_edition_role in OpenEditionRolesConverter.ROLES_MAPPING
        ]:
            if len(contributors) == 0:
                continue
            for contributor_name, _ in contributors:
                contribution_informations.append(
                    AbstractReferencesConverter.ContributionInformations(
                        role=OpenEditionRolesConverter.convert(open_edition_quality),
                        identifier=None,
                        name=contributor_name,
                        rank=None,
                    )
                )
        async for contribution in self._contributions(
            contribution_informations=contribution_informations, source="openedition"
        ):
            new_ref.contributions.append(contribution)

    def _get_term(self, root: ElementTree, term: str):
        return (
            root.find(f"{{{rdflib.DCTERMS}}}{term}").text
            if root.find(f"{{{rdflib.DCTERMS}}}{term}") is not None
            else None
        )

    def _get_terms(self, root: ElementTree, term: str):
        return [
            (term.text, term.attrib)
            for term in root.findall(f"{{{rdflib.DCTERMS}}}{term}")
        ]

    def _get_root(self, raw_data: XMLHarvesterRawResult):
        if self.tree_root is None:
            try:
                root = raw_data.payload
                return (
                    root.find(f"{{{self.NAMESPACES['oai']}}}GetRecord")
                    .find(f"{{{self.NAMESPACES['oai']}}}record")
                    .find(f"{{{self.NAMESPACES['oai']}}}metadata")
                    .find(f"{{{self.NAMESPACES['qdc']}}}qualifieddc")
                )
            except AttributeError as error:
                raise UnexpectedFormatException(
                    "Unexpected format for OAI Open Edition response "
                    f"for {raw_data.source_identifier}"
                ) from error
        return self.tree_root

    def _title(self, root: ElementTree):
        title = self._get_term(root, "title")
        language = self._language(root)
        return Title(value=title, language=language)

    def _language(self, root: ElementTree):
        return self._get_term(root, "language")

    def _abstracts(self, root: ElementTree):
        # Sometimes we have abstract or description.
        # Is the same ? In Dublic Core, Abstract is a sub property of Description
        abstract = self._get_terms(root, "abstract")
        if len(abstract) == 0:
            abstract = self._get_terms(root, "description")
            if len(abstract) != 0:
                logger.debug("Description found instead of abstract")
        if len(abstract) == 0:
            yield
        for value, attrib in abstract:
            language = attrib.get(f"{{{rdflib.XMLNS}}}lang", self._language(root))
            yield Abstract(value=value, language=language)

    async def _subjects(self, root: ElementTree):
        subjects = self._get_terms(root, "subject")
        language = self._language(root)
        for subject in subjects:
            label, attrib = subject
            language = attrib.get(f"{{{rdflib.XMLNS}}}lang", None)
            yield await self._get_or_create_concept_by_label(
                ConceptInformations(
                    label=label,
                    language=language,
                )
            )

    async def _document_type(self, root: ElementTree):
        document_type = self._get_term(root, "type")
        uri, label = OpenEditionDocumentTypeConverter().convert(
            document_type=document_type
        )
        return await self._get_or_create_document_type_by_uri(uri=uri, label=label)

    def _get_issued_date(self, root: ElementTree, new_ref: Reference):
        issued = self._get_term(root, "issued")
        try:
            new_ref.raw_issued = issued
            new_ref.issued = check_valid_iso8601_date(issued)
        except UnexpectedFormatException as error:
            logger.error(
                f"OpenEdition reference converter cannot create issued date from issued in {root}"
                f": {error}"
            )

    def _get_created_date(self, root: ElementTree, new_ref: Reference):
        created = self._get_term(root, "created")
        try:
            new_ref.created = check_valid_iso8601_date(created)
        except UnexpectedFormatException as error:
            logger.error(
                f"OpenEdition reference converter cannot create created date from created in {root}"
                f": {error}"
            )

    def hash_keys(self, harvester_version: Version) -> list[HashKey]:
        return [
            HashKeyXML("dcterms:title", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:abstract", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:type", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:language", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:identifier", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:subject", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:type", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:issued", namespace=self.NAMESPACES),
            HashKeyXML("dcterms:created", namespace=self.NAMESPACES),
        ]
