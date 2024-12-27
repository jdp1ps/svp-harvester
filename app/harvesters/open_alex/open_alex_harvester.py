from typing import AsyncGenerator

from semver import VersionInfo, Version

from app.harvesters.abstract_harvester import AbstractHarvester
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult
from app.harvesters.open_alex.open_alex_api_query_builder import OpenAlexQueryBuilder
from app.harvesters.open_alex.open_alex_client import OpenAlexClient


class OpenAlexHarvester(AbstractHarvester):
    """
    Harvester for api.openalex.org
    """

    FORMATTER_NAME = "OPEN_ALEX"

    IDENTIFIERS_BY_ENTITIES = {
        "Person": [(OpenAlexQueryBuilder.QueryParameters.AUTH_ORCID, "orcid")]
    }

    SUBJECT_BY_ENTITIES = {"Person": OpenAlexQueryBuilder.SubjectType.PERSON}

    supported_identifier_types = ["orcid"]
    # 1.3.1 : fix [None] issue number issue https://github.com/CRISalid-esr/svp-harvester/issues/623
    VERSION: Version = VersionInfo.parse("1.4.0")

    async def _get_open_alex_query_parameters(self, entity_class: str):
        """
        Set the query parameters for an entity
        """

        entity = await self._get_entity()

        query_parameters = self.IDENTIFIERS_BY_ENTITIES.get(entity_class)

        for open_alex_query_parameter, identifier_key in query_parameters:
            identifier_value = entity.get_identifier(identifier_key)
            if identifier_value is not None:
                return open_alex_query_parameter, identifier_value

        assert False, "Unable to run open alex harvester for a person without ORCID"

    async def fetch_results(self) -> AsyncGenerator[JsonHarvesterRawResult, None]:
        """
        Fetch results from the OpenAlex API.
        It is an asynchronous generator that yields JsonHarvesterRawResult objects.
        """
        builder = OpenAlexQueryBuilder()

        identifier_type, identifier_value = await self._get_open_alex_query_parameters(
            await self._get_entity_class_name()
        )

        builder.set_subject_type(
            self.SUBJECT_BY_ENTITIES[await self._get_entity_class_name()]
        )

        builder.set_query(
            identifier_type=identifier_type, identifier_value=identifier_value
        )

        async for doc in OpenAlexClient().fetch(builder.build()):
            yield JsonHarvesterRawResult(
                payload=doc,
                source_identifier=doc.get("id"),
                formatter_name=OpenAlexHarvester.FORMATTER_NAME,
            )
