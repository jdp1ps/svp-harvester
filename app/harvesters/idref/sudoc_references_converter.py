import re

import rdflib
from loguru import logger
from rdflib import DC, DCTERMS, Graph, Literal, Namespace, URIRef
from semver import Version

from app.db.models.book import Book
from app.db.models.issue import Issue
from app.db.models.journal import Journal
from app.db.models.reference import Reference
from app.db.models.reference_identifier import ReferenceIdentifier
from app.db.models.reference_manifestation import ReferenceManifestation
from app.db.models.title import Title
from app.harvesters.abstract_references_converter import AbstractReferencesConverter
from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.idref.abes_rdf_references_converter import (
    AbesRDFReferencesConverter,
)
from app.harvesters.idref.rdf_resolver import RdfResolver
from app.harvesters.idref.sudoc_document_type_converter import (
    SudocDocumentTypeConverter,
)
from app.harvesters.idref.sudoc_roles_converter import SudocRolesConverter
from app.harvesters.rdf_harvester_raw_result import RdfHarvesterRawResult
from app.services.book.book_data_class import BookInformations
from app.services.concepts.concept_informations import ConceptInformations
from app.services.hash.hash_key import HashKey
from app.services.issue.issue_data_class import IssueInformations
from app.services.journal.journal_data_class import JournalInformations
from app.utilities.date_utilities import check_valid_iso8601_date
from app.utilities.execution_timer_wrapper import execution_timer
from app.utilities.isbn_utilities import get_isbns
from app.utilities.string_utilities import normalize_string, remove_after_separator


class SudocReferencesConverter(AbesRDFReferencesConverter):
    """
    Converts raw data from Sudoc to a normalised Reference object
    """

    RDF_BIBO = Namespace("http://purl.org/ontology/bibo/")
    FABIO_NAMESPACE = Namespace("http://purl.org/spar/fabio/")
    RDAU = Namespace("http://rdaregistry.info/Elements/u/")
    RDAM = Namespace("http://rdaregistry.info/Elements/m/")
    RDAC = Namespace("http://rdaregistry.info/Elements/c/")

    @AbesRDFReferencesConverter.validate_reference
    async def convert(
        self, raw_data: RdfHarvesterRawResult, new_ref: Reference
    ) -> None:
        await super().convert(raw_data=raw_data, new_ref=new_ref)
        if not new_ref.titles:
            raise UnexpectedFormatException(
                f"Sudoc reference without title: {new_ref.source_identifier}"
            )

        self._add_created_date(raw_data.payload, raw_data.source_identifier, new_ref)
        self._add_issued_date(raw_data.payload, raw_data.source_identifier, new_ref)

        self._add_manifestations(raw_data.payload, raw_data.source_identifier, new_ref)

        await self._get_subjects(raw_data.payload, raw_data.source_identifier, new_ref)

        # If we have an article, we need to get the journal and issue
        if "Article" in [dc.label for dc in new_ref.document_type]:
            async for biblio_graph, uri in self._get_bibliographic_resource(
                pub_graph=raw_data.payload, uri=raw_data.source_identifier
            ):
                journal = await self._get_journal(biblio_graph, uri)
                issue = await self._get_issue(
                    journal=journal, biblio_graph=biblio_graph, uri=uri
                )
                new_ref.issue = issue

    @execution_timer
    async def _get_subjects(self, pub_graph, uri, new_ref):
        for subject in pub_graph.objects(rdflib.term.URIRef(uri), DCTERMS.subject):
            concept_uri = str(subject)
            db_concept = await self._get_or_create_concept_by_uri(
                ConceptInformations(
                    uri=concept_uri,
                )
            )
            new_ref.subjects.append(db_concept)

    def _harvester(self) -> str:
        return "Idref"

    async def _get_book(self, pub_graph, uri) -> Book | None:
        isbn10 = None
        isbn13_from_isbn10 = None
        for isbn10 in pub_graph.objects(rdflib.term.URIRef(uri), self.RDF_BIBO.isbn10):
            isbn10 = isbn10.value
        if isbn10:
            isbn10, isbn13_from_isbn10 = get_isbns(isbn10)
        isbn13 = None
        for isbn13 in pub_graph.objects(rdflib.term.URIRef(uri), self.RDF_BIBO.isbn13):
            isbn13 = isbn13.value
        if not isbn13 and isbn13_from_isbn10:
            isbn13 = isbn13_from_isbn10
        else:
            _, isbn13 = get_isbns(isbn13)

        publisher: Literal
        for publisher in pub_graph.objects(rdflib.term.URIRef(uri), DC.publisher):
            publisher = publisher.value
        title = None
        for title in pub_graph.objects(rdflib.term.URIRef(uri), DC.title):
            title = title.value
        return await self._get_or_create_book(
            BookInformations(
                title=title,
                source="sudoc",
                isbn10=isbn10,
                isbn13=isbn13,
                publisher=publisher,
            )
        )

    async def _get_bibliographic_resource(self, pub_graph, uri) -> Graph:
        document: Literal
        for document in pub_graph.objects(rdflib.term.URIRef(uri), DCTERMS.isPartOf):
            document_uri = str(document)
            document = str(document).replace("/id", ".rdf")
            document = document.replace("http", "https")
            document_graph = await RdfResolver().fetch(document)
            yield document_graph, document_uri
            # We only want the first appearance.
            break

    async def _get_issue(self, biblio_graph, uri, journal) -> Issue:
        source_identifier = normalize_string("-".join(journal.titles)) + "-sudoc"
        return await self._get_or_create_issue(
            IssueInformations(
                source="sudoc", source_identifier=source_identifier, journal=journal
            )
        )

    async def _get_journal(self, biblio_graph, uri) -> Journal:
        titles = []
        issn_value = []
        for issn in biblio_graph.objects(rdflib.term.URIRef(uri), self.RDF_BIBO.issn):
            issn_value.append(issn.value)
        issn_l_value = None
        for issn_l in biblio_graph.objects(
            rdflib.term.URIRef(uri), self.FABIO_NAMESPACE.hasIssnL
        ):
            issn_l_value = issn_l.value
        title_value = None
        for title in biblio_graph.objects(rdflib.term.URIRef(uri), DC.title):
            title_value = title.value
        if title_value is not None:
            titles.append(title_value)
        title_key_value = None
        for title_key in biblio_graph.objects(
            rdflib.term.URIRef(uri), self.RDAU.P60597
        ):
            title_key_value = title_key.value
        if title_key_value is not None:
            titles.append(title_key_value)
        publisher_value = None
        for publisher in biblio_graph.objects(rdflib.term.URIRef(uri), DC.publisher):
            publisher_value = publisher.value
            # We only want the first appearance.
            break
        return await self._get_or_create_journal(
            JournalInformations(
                source="sudoc",
                source_identifier=uri,
                issn=issn_value,
                issn_l=issn_l_value,
                publisher=publisher_value,
                titles=titles,
            )
        )

    def _titles(self, pub_graph, uri):
        title: Literal
        for title in pub_graph.objects(rdflib.term.URIRef(uri), DC.title):
            yield Title(
                value=remove_after_separator(title.value, "/"), language=title.language
            )

    def _add_created_date(self, pub_graph, uri, new_ref):
        if uri.endswith("/id"):
            uri = uri[:-3]
        for created in pub_graph.objects(rdflib.term.URIRef(uri), DCTERMS.created):
            try:
                new_ref.created = check_valid_iso8601_date(created.value)
            except UnexpectedFormatException as error:
                logger.error(
                    f"Sudoc reference converter cannot create created date from DCTERMS.created in"
                    f" {uri}: {error}"
                )

    def _add_issued_date(self, pub_graph, uri, new_ref):
        # we fecth the cd:date field if present : it may occur multiple times and the date is
        # often limited to the year
        for issued in pub_graph.objects(rdflib.term.URIRef(uri), DC.date):
            # date is in the form of "yyyy"
            year_date_string = issued.value
            try:
                new_ref.raw_issued = year_date_string
                # isodate will convert it to "yyyy-01-01"
                new_ref.issued = check_valid_iso8601_date(year_date_string)
            except UnexpectedFormatException as error:
                logger.error(
                    f"Sudoc reference converter cannot create issued date from"
                    f" dateOfPrintPublication in {uri}: {error}"
                )

    async def _document_type(self, pub_graph, uri):
        for document_type in pub_graph.objects(
            rdflib.term.URIRef(uri), rdflib.RDF.type
        ):
            uri, label = SudocDocumentTypeConverter().convert(str(document_type))
            yield await self._get_or_create_document_type_by_uri(uri, label)

    async def _add_contributions(self, pub_graph, uri):
        contribution_informations = []
        query = """
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                    PREFIX marcrel: <http://id.loc.gov/vocabulary/relators/>

                    SELECT DISTINCT ?role ?person ?name
                    WHERE {
                        ?work ?role ?person .
                        ?person a foaf:Person .
                        ?person foaf:name ?name .
                        FILTER(STRSTARTS(STR(?role), STR(marcrel:)))
                    }
                """

        results = pub_graph.query(query)
        for role, identifier, name in results:
            role = role.split("/")[-1]
            contribution_informations.append(
                AbstractReferencesConverter.ContributionInformations(
                    role=self._convert_role(role),
                    identifier=str(identifier),
                    name=str(name),
                    rank=None,
                )
            )

        async for contribution in self._contributions(
            contribution_informations=contribution_informations,
            source=self._get_source(),
        ):
            yield contribution

    def _add_manifestations(self, pub_graph, uri, new_ref):
        for raw_uri in pub_graph.subjects(predicate=None, object=URIRef(uri)):
            new_ref.manifestations.append(ReferenceManifestation(page=str(raw_uri)))
        nnt_found = False
        for theses_fr_uri in pub_graph.objects(
            rdflib.term.URIRef(uri), self.RDF_BIBO.uri
        ):
            # the uri finishing by /document redirects to hal.science
            if not theses_fr_uri.value.endswith("/document"):
                try:
                    new_ref.manifestations.append(
                        ReferenceManifestation(page=theses_fr_uri.value)
                    )
                except ValueError as e:
                    logger.error(
                        "Unable to register theses.fr URI  for SUDOC "
                        f"URI {uri} : {theses_fr_uri.value} {e}"
                    )
            if not nnt_found:
                nnt = re.search(
                    r"^https?://www.theses.fr/([^/]+)/.+", theses_fr_uri.value
                )
                if nnt:
                    new_ref.identifiers.append(
                        ReferenceIdentifier(value=nnt.groups()[0], type="nnt")
                    )
                    nnt_found = True

        # take rdam:P30135 as another manifestation
        for uri1 in pub_graph.objects(rdflib.term.URIRef(uri), self.RDAM.P30135):
            try:
                new_ref.manifestations.append(ReferenceManifestation(page=str(uri1)))
            except ValueError as e:
                logger.error(
                    f"Unable to register alternative URI: {uri1} for SUDOC URI {uri} : {e}"
                )

    def _get_source(self):
        return "sudoc"

    def _resolve_contributor(self, identifier):
        pass

    def _convert_role(self, role):
        return SudocRolesConverter.convert(role)

    def hash_keys(self, harvester_version: Version) -> list[HashKey]:
        return [
            HashKey(DC.title),
            HashKey(DC.type),
            HashKey(DCTERMS.abstract),
        ]
