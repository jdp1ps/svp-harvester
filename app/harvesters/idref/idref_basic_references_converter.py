from loguru import logger
from rdflib import FOAF, URIRef
from semver import Version

from app.db.models.abstract import Abstract
from app.db.models.reference import Reference
from app.db.models.reference_identifier import ReferenceIdentifier
from app.db.models.subtitle import Subtitle
from app.db.models.title import Title
from app.harvesters.abstract_references_converter import AbstractReferencesConverter
from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.idref.idref_document_type_converter import (
    IdrefDocumentTypeConverter,
)
from app.harvesters.idref.idref_roles_converter import IdrefRolesConverter
from app.harvesters.idref.rdf_resolver import RdfResolver
from app.harvesters.sparql_harvester_raw_result import (
    SparqlHarvesterRawResult as SparqlRawResult,
)
from app.services.concepts.concept_informations import ConceptInformations
from app.services.hash.hash_key import HashKey
from app.utilities.date_utilities import check_valid_iso8601_date


class IdrefBasicReferencesConverter(AbstractReferencesConverter):
    """
    Converts raw data from IdRef to a normalised Reference object
    when data delivered by Idref Sparql endpoint are not enough to create
    a complete Reference object without the help of a secondary converter
    """

    def _harvester(self) -> str:
        return "Idref"

    @AbstractReferencesConverter.validate_reference
    async def convert(self, raw_data: SparqlRawResult, new_ref: Reference) -> None:
        dict_payload: dict = raw_data.payload
        uri = raw_data.source_identifier
        self._fetch_issued_date(new_ref, dict_payload, uri)
        for title in dict_payload["title"]:
            new_ref.titles.append(Title(value=title, language="fr"))
        for subtitle in dict_payload["altLabel"]:
            new_ref.subtitles.append(Subtitle(value=subtitle, language="fr"))
        for abstract in dict_payload["note"]:
            new_ref.abstracts.append(Abstract(value=abstract, language="fr"))
        concept_informations = [
            ConceptInformations(
                uri=subject.get("uri"), label=subject.get("label"), language="fr"
            )
            for subject in dict_payload["subject"].values()
        ]
        new_ref.subjects.extend(
            await self._get_or_create_concepts_by_uri(concept_informations)
        )

        for document_type in dict_payload["type"]:
            uri_type, label = IdrefDocumentTypeConverter().convert(document_type)
            new_ref.document_type.append(
                await self._get_or_create_document_type_by_uri(uri_type, label)
            )

        async for contribution in self._contributions(
            contribution_informations=await self.get_contributors(dict_payload),
            source="idref",
        ):
            new_ref.contributions.append(contribution)

        new_ref.identifiers.append(ReferenceIdentifier(value=uri, type="uri"))
        for equivalent in dict_payload.get("equivalent", []):
            new_ref.identifiers.append(
                ReferenceIdentifier(value=equivalent, type="uri")
            )

    def _fetch_issued_date(self, new_ref, dict_payload, uri):
        issued_date = dict_payload.get("date", None)
        if issued_date is not None:
            try:
                new_ref.issued = check_valid_iso8601_date(issued_date)
            except UnexpectedFormatException:
                logger.error(
                    f"Idref reference converter cannot create issued date from"
                    f" {issued_date} for reference {uri}"
                )

    def hash_keys(self, harvester_version: Version) -> list[HashKey]:
        return [
            HashKey("uri"),
            HashKey("role"),
            HashKey("title"),
            HashKey("type"),
            HashKey("altLabel"),
            HashKey("subject"),
        ]

    async def get_contributors(self, dict_payload):
        """
        Retrieves contributor information from the given dictionary payload.

        :params dict_payload: The dictionary payload containing contributor and role information.

        :return: A list of ContributionInformations objects.
        """
        contributor_informations = []
        contributors = dict_payload.get("contributors", {})

        for contributor_uri, contributor_data in contributors.items():
            if not contributor_uri:
                continue

            name, family_name, given_name = await self._fetch_and_update_names(
                contributor_uri, contributor_data
            )

            roles = contributor_data.get("roles", [])
            contributor_informations.extend(
                self._create_contribution_information(
                    contributor_uri, name, family_name, given_name, roles
                )
            )

        return contributor_informations

    async def _fetch_and_update_names(self, contributor_uri, contributor_data):
        """
        Fetches and updates contributor names using RDF data.

        :param contributor_uri: The URI of the contributor.
        :param contributor_data: The dictionary containing initial contributor data.

        :return: A tuple of (name, family_name, given_name).
        """
        contributor_url = contributor_uri.replace("/id", ".rdf").replace(
            "http://", "https://"
        )
        graph = await RdfResolver().fetch(contributor_url)

        family_name = contributor_data.get("familyName", "")
        given_name = contributor_data.get("givenName", "")
        name = contributor_data.get("name", "")

        for rdf_family_name in graph.objects(URIRef(contributor_uri), FOAF.familyName):
            family_name = rdf_family_name.value
        for rdf_given_name in graph.objects(URIRef(contributor_uri), FOAF.givenName):
            given_name = rdf_given_name.value

        if not family_name or not given_name:
            for rdf_name in graph.objects(URIRef(contributor_uri), FOAF.name):
                name = rdf_name.value
        else:
            name = f"{given_name} {family_name}"

        return name, family_name, given_name

    @staticmethod
    def _create_contribution_information(
        contributor_uri, name, family_name, given_name, roles
    ):
        """
        Creates ContributionInformations objects for each role.

        :param contributor_uri: The URI of the contributor.
        :param name: The full name of the contributor.
        :param roles: A list of roles associated with the contributor.

        :return: A list of ContributionInformations objects.
        """
        contribution_informations = []
        for role_uri in roles:
            role = role_uri.split("/")[-1]
            contribution_informations.append(
                AbstractReferencesConverter.ContributionInformations(
                    role=IdrefRolesConverter.convert(role),
                    identifier=contributor_uri,
                    name=name,
                    last_name=family_name,
                    first_name=given_name,
                    rank=None,
                )
            )
        return contribution_informations
