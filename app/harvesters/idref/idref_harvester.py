import asyncio
import re
import urllib
from enum import Enum
from typing import AsyncGenerator

import uritools
from loguru import logger
from rdflib import URIRef
from semver import VersionInfo, Version

from app.config import get_app_settings
from app.harvesters.abstract_harvester import AbstractHarvester
from app.harvesters.exceptions.external_endpoint_failure import ExternalEndpointFailure
from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.idref.idref_sparql_client import IdrefSparqlClient
from app.harvesters.idref.idref_sparql_query_builder import (
    IdrefSparqlQueryBuilder as QueryBuilder,
)
from app.harvesters.idref.open_edition_resolver import OpenEditionResolver
from app.harvesters.idref.rdf_resolver import RdfResolver
from app.harvesters.rdf_harvester_raw_result import (
    AbstractHarvesterRawResult as RawResult,
)
from app.harvesters.rdf_harvester_raw_result import RdfHarvesterRawResult as RdfResult
from app.harvesters.sparql_harvester_raw_result import (
    SparqlHarvesterRawResult as SparqlResult,
)
from app.harvesters.xml_harvester_raw_result import (
    XMLHarvesterRawResult as XmlResult,
)
from app.services.cache.third_api_cache import ThirdApiCache
from app.utilities.execution_timer_wrapper import execution_timer


class IdrefHarvester(AbstractHarvester):
    """
    Harvester for data.idref.fl
    """

    SUDOC_URL_SUFFIX = "http://www.sudoc.fr/"
    # It can be journals or books
    OPEN_EDITION_SUFFIX = re.compile(
        r"https?://(?:journals|books)\.openedition\.org/.*"
    )
    SCIENCE_PLUS_URL_SUFFIX = "http://hub.abes.fr/"
    SCIENCE_PLUS_QUERY_SUFFIX = "https://scienceplus.abes.fr/sparql"
    PERSEE_URL_SUFFIX = "http://data.persee.fr/"
    MAX_SUDOC_PARALLELISM = 3
    SUDOC_ENABLED = True

    supported_identifier_types = ["idref", "orcid"]

    VERSION: Version = VersionInfo.parse("1.6.0")

    class Formatters(Enum):
        """
        Source identifiers for idref, including secondary sources
        """

        SUDOC_RDF = "SUDOC_RDF"
        SCIENCE_PLUS_RDF = "SCIENCE_PLUS_RDF"
        HAL_JSON = "HAL_JSON"
        IDREF_SPARQL = "IDREF_SPARQL"
        OPEN_EDITION = "OPEN_EDITION"
        PERSEE_RDF = "PERSEE_RDF"

    async def fetch_results(self) -> AsyncGenerator[RawResult, None]:
        # pylint: disable=too-many-branches, too-many-statements
        settings = get_app_settings()
        builder = QueryBuilder()
        if (await self._get_entity_class_name()) == "Person":
            idref: str = (await self._get_entity()).get_identifier("idref")
            orcid: str = (await self._get_entity()).get_identifier("orcid")
            assert (
                idref is not None or orcid is not None
            ), "Idref or Orcid identifier required when harvesting publications from data.idref.fr"
            if idref is not None and re.fullmatch(r"\d{8}[\dX]|", idref):
                builder.set_subject_type(QueryBuilder.SubjectType.PERSON).set_idref_id(
                    idref
                )
            else:
                logger.warning(f"Unexpected idref format detected: '{idref}', for entity type "
                               f"{self.entity.type} named {self.entity.name}")
            if orcid is not None:
                builder.set_subject_type(QueryBuilder.SubjectType.PERSON).set_orcid(
                    orcid
                )
        pending_queries = set()
        num_sudoc_waiting_queries = 0

        if self.SUDOC_ENABLED:
            async for doc in IdrefSparqlClient(
                timeout=settings.idref_sparql_timeout
            ).fetch_publications(builder.build()):
                coro = self._secondary_query_process(doc)
                # Temporary semi-sequential implementation
                # Sudoc server does not support parallel querying beyond 5 parallel requests
                # See issue #251
                pending_queries.add(asyncio.create_task(coro))
                if doc["secondary_source"] == "SUDOC":
                    num_sudoc_waiting_queries += 1
                if num_sudoc_waiting_queries >= self.MAX_SUDOC_PARALLELISM:
                    num_sudoc_waiting_queries = 0
                    while pending_queries:
                        done_queries, pending_queries = await asyncio.wait(
                            pending_queries, return_when=asyncio.ALL_COMPLETED
                        )
                        for query in done_queries:
                            pub = None
                            exception = query.exception()
                            if isinstance(
                                exception,
                                (ExternalEndpointFailure, UnexpectedFormatException),
                            ):
                                await self.handle_error(exception)
                            else:
                                pub = query.result()
                            if pub:
                                yield pub
            # process remaining queries
            while pending_queries:
                pub = None
                done_queries, pending_queries = await asyncio.wait(
                    pending_queries, return_when=asyncio.FIRST_COMPLETED
                )
                for query in done_queries:
                    exception = query.exception()
                    if isinstance(
                        exception,
                        (ExternalEndpointFailure, UnexpectedFormatException),
                    ):
                        await self.handle_error(exception)
                    else:
                        pub = query.result()
                    if pub:
                        yield pub
        else:
            async for doc in IdrefSparqlClient(
                timeout=settings.idref_sparql_timeout
            ).fetch_publications(builder.build()):
                if doc["secondary_source"] == "SUDOC":
                    continue
                coro = self._secondary_query_process(doc)
                pending_queries.add(asyncio.create_task(coro))
                while pending_queries:
                    pub = None
                    done_queries, pending_queries = await asyncio.wait(
                        pending_queries, return_when=asyncio.FIRST_COMPLETED
                    )
                    for query in done_queries:
                        exception = query.exception()
                        if isinstance(
                            exception,
                            (ExternalEndpointFailure, UnexpectedFormatException),
                        ):
                            await self.handle_error(exception)
                        else:
                            pub = query.result()
                        if pub:
                            yield pub

    def _secondary_query_process(self, doc: dict):
        coro = None
        if doc["secondary_source"] == "IDREF":
            coro = self._convert_publication_from_idref_endpoint(doc)
        elif doc["secondary_source"] == "SUDOC":
            coro = self._query_publication_from_sudoc_endpoint(doc)
        elif doc["secondary_source"] == "HAL":
            coro = self._query_publication_from_hal_endpoint(doc)
        elif doc["secondary_source"] == "SCIENCE_PLUS":
            coro = self._query_publication_from_science_plus_endpoint(doc)
        elif doc["secondary_source"] == "OPEN_EDITION":
            coro = self._query_publication_from_openedition_endpoint(doc)
        elif doc["secondary_source"] == "PERSEE":
            coro = self._query_publication_from_persee_endpoint(doc)
        else:
            logger.info(f"Unknown source {doc['secondary_source']}")
        return coro

    @execution_timer
    async def _query_publication_from_persee_endpoint(self, doc: dict) -> RdfResult:
        uri: str | None = doc.get("uri", "")
        if not uritools.isuri(uri):
            raise UnexpectedFormatException(
                f"Invalid Persee URI from Idref SPARQL endpoint: {uri}"
            )
        assert uri.startswith(self.PERSEE_URL_SUFFIX), "Invalid Persee Id"
        assert uri.endswith("#Web"), "Provided Persee URI should end with #Web"

        document_uri = re.sub(r"#Web$", "", uri)
        document_uri = re.sub(r"^http://", "https://", document_uri)
        pub = await ThirdApiCache.get("persee_publications", document_uri)
        if pub is None:
            pub = await RdfResolver().fetch(document_uri, output_format="xml")
            await ThirdApiCache.set("persee_publications", uri, pub)
        return RdfResult(
            payload=pub,
            source_identifier=URIRef(uri),
            formatter_name=self.Formatters.PERSEE_RDF.value,
        )

    @execution_timer
    async def _query_publication_from_openedition_endpoint(self, doc: dict):
        """
        Query the publications from the OpenEdition API
        :param doc: the publication doc as result of the SPARQL query to data.idref.fr with the uri
        :return: the publication details
        """

        uri: str | None = doc.get("uri", "")
        if (uri is None) or not uritools.isuri(uri):
            raise UnexpectedFormatException(
                f"Invalid OpenEdition URI from Idref SPARQL endpoint: {uri}"
            )
        assert self.OPEN_EDITION_SUFFIX.match(uri), f"Invalid OpenEdition Id {uri}"
        pub = await ThirdApiCache.get("open_edition_publications", uri)
        if pub is None:
            pub = await OpenEditionResolver().fetch(uri)
            await ThirdApiCache.set("open_edition_publications", uri, pub)
        return XmlResult(
            payload=pub,
            source_identifier=URIRef(uri),
            formatter_name=self.Formatters.OPEN_EDITION.value,
        )

    @execution_timer
    async def _query_publication_from_sudoc_endpoint(self, doc: dict) -> RdfResult:
        """
        Query the details of a publication from the SUDOC API

        :param doc: the publication doc as result of the SPARQL query to data.idref.fr
        :return: the publication details
        """
        uri: str | None = doc.get("uri", "")
        if not uritools.isuri(uri):
            raise UnexpectedFormatException(
                f"Invalid SUDOC URI from Idref SPARQL endpoint: {uri}"
            )
        assert uri.startswith(self.SUDOC_URL_SUFFIX), "Invalid Sudoc Id"
        assert uri.endswith("/id"), "Provided Sudoc URI should end with /id"
        # with regular expression, replace trailing "/id" by '.rdf' in document_uri
        document_uri = re.sub(r"/id$", ".rdf", uri)
        # with regular expression, replace "http://" by "https://" in document_uri
        document_uri = re.sub(r"^http://", "https://", document_uri)
        settings = get_app_settings()
        pub = await ThirdApiCache.get("sudoc_publications", document_uri)
        if pub is None:
            pub = await RdfResolver(timeout=settings.idref_sudoc_timeout).fetch(
                document_uri, output_format="xml"
            )
            await ThirdApiCache.set("sudoc_publications", document_uri, pub)
        return RdfResult(
            payload=pub,
            source_identifier=URIRef(uri),
            formatter_name=self.Formatters.SUDOC_RDF.value,
        )

    @execution_timer
    async def _convert_publication_from_idref_endpoint(self, doc: dict) -> SparqlResult:
        """
        Query the details of a publication from the IDREF API

        :param doc: the publication doc
        :return: the publication details
        """
        return SparqlResult(
            payload=doc,
            source_identifier=URIRef(doc.get("uri")),
            formatter_name=self.Formatters.IDREF_SPARQL.value,
        )

    @execution_timer
    async def _query_publication_from_hal_endpoint(
        self, doc: dict  # pylint: disable=unused-argument
    ) -> RawResult:
        """
        Query the details of a publication from the HAL API

        :param doc: the publication doc
        :return: the publication details
        """
        return {}

    @execution_timer
    async def _query_publication_from_science_plus_endpoint(
        self, doc: dict  # pylint: disable=unused-argument
    ) -> RawResult:
        """
        Query the details of a publication from the Science+ API

        :param doc: the publication doc
        :return: the publication details
        """
        uri: str | None = doc.get("uri", "")
        assert uri.startswith(self.SCIENCE_PLUS_URL_SUFFIX), "Invalid SciencePlus Id"
        if not uritools.isuri(uri):
            raise UnexpectedFormatException(
                f"Invalid SUDOC URI from Idref SPARQL endpoint: {uri}"
            )
        params = {
            "query": f'define sql:describe-mode "CBD"  DESCRIBE <{uri}>',
            "output": "application/rdf+xml",
        }
        # concatenate encoded params to query suffix
        query_uri = f"{self.SCIENCE_PLUS_QUERY_SUFFIX}?{urllib.parse.urlencode(params)}"
        pub = None
        settings = get_app_settings()
        if settings.third_api_caching_enabled:
            pub = await ThirdApiCache.get("science_plus_publications", query_uri)
        if pub is None:
            client = RdfResolver(timeout=settings.idref_science_plus_timeout)
            pub = await client.fetch(query_uri, output_format="xml")
            await ThirdApiCache.set("science_plus_publications", query_uri, pub)

        doi = doc.get("doi", None)
        return RdfResult(
            payload=pub,
            source_identifier=URIRef(uri),
            formatter_name=self.Formatters.SCIENCE_PLUS_RDF.value,
            doi=doi,
        )
