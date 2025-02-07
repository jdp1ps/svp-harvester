from typing import AsyncGenerator

from semver import VersionInfo, Version

from app.harvesters.abstract_harvester import AbstractHarvester
from app.harvesters.scopus.scopus_api_query_builder import ScopusQueryBuilder
from app.harvesters.scopus.scopus_client import ScopusClient
from app.harvesters.xml_harvester_raw_result import XMLHarvesterRawResult


class ScopusHarvester(AbstractHarvester):
    """
    Harvester for Scopus
    """

    FORMATTER_NAME = "SCOPUS"

    IDENTIFIERS_BY_ENTITIES = {
        "Person": [(ScopusQueryBuilder.QueryParameters.SCOPUS_EID, "scopus_eid")]
    }

    SUBJECT_BY_ENTITIES = {"Person": ScopusQueryBuilder.SubjectType.PERSON}

    supported_identifier_types = ["scopus_eid"]

    VERSION: Version = VersionInfo.parse("1.6.0")

    async def _get_scopus_query_parameters(self, entity_class: str):
        """
        Set the query parameter for an entity
        """

        entity = await self._get_entity()

        query_parameters = self.IDENTIFIERS_BY_ENTITIES.get(entity_class)

        for scopus_query_parameter, identifier_key in query_parameters:
            identifier_value = entity.get_identifier(identifier_key)
            if identifier_value is not None:
                return scopus_query_parameter, identifier_value

        assert False, "Unable to run scopus harverster for a person without ScopusEID"

    async def fetch_results(self) -> AsyncGenerator[XMLHarvesterRawResult, None]:
        """
        Fetch results from the Scopus API
        """
        builder = ScopusQueryBuilder()

        identifier_type, identifier_value = await self._get_scopus_query_parameters(
            await self._get_entity_class_name()
        )

        builder.set_subject_type(
            self.SUBJECT_BY_ENTITIES[await self._get_entity_class_name()]
        )

        builder.set_query(identifier_type, identifier_value)
        async for doc in ScopusClient().fetch(builder.build()):
            if doc is None:
                continue
            source_identifier = doc.find(
                "dc:identifier", ScopusClient.NAMESPACE
            ).text.split(":")[-1]
            yield XMLHarvesterRawResult(
                payload=doc,
                source_identifier=source_identifier,
                formatter_name=ScopusHarvester.FORMATTER_NAME,
            )
