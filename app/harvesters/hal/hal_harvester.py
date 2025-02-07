from typing import AsyncGenerator

from semver import VersionInfo, Version

from app.harvesters.abstract_harvester import AbstractHarvester
from app.harvesters.hal.hal_api_client import HalApiClient
from app.harvesters.hal.hal_api_query_builder import HalApiQueryBuilder
from app.harvesters.json_harvester_raw_result import (
    JsonHarvesterRawResult as JsonRawResult,
)


class HalHarvester(AbstractHarvester):
    """
    Harvester for data.idref.fl
    """

    FORMATTER_NAME = "HAL"

    IDENTIFIERS_BY_ENTITIES = {
        "Person": [
            (HalApiQueryBuilder.QueryParameters.AUTH_ID_HAL_I, "id_hal_i"),
            (HalApiQueryBuilder.QueryParameters.AUTH_ID_HAL_S, "id_hal_s"),
            (HalApiQueryBuilder.QueryParameters.AUTH_ORCID_ID_EXT_ID, "orcid"),
        ]
    }

    supported_identifier_types = ["id_hal_i", "id_hal_s", "orcid"]

    VERSION: Version = VersionInfo.parse("1.6.0")

    async def _get_hal_query_parameters(self, entity_class: str):
        """
        Set the query parameters for an entity
        """
        entity = await self._get_entity()

        query_parameters = self.IDENTIFIERS_BY_ENTITIES.get(entity_class)
        # List convenient query parameters for this entity class
        # and choose the first one for which value is provided

        for hal_query_parameter, identifier_key in query_parameters:
            identifier_value = entity.get_identifier(identifier_key)
            if identifier_value is not None:
                return hal_query_parameter, identifier_value

        assert (
            False
        ), "Unable to run hal harvester for a person without id_hal_i, id_hal_s or ORCID"

    async def fetch_results(self) -> AsyncGenerator[JsonRawResult, None]:
        """
        Fetch results from the HAL API.
        It is an asynchronous generator that yields JsonRawResult objects.
        """
        builder = HalApiQueryBuilder()

        identifier_type, identifier_value = await self._get_hal_query_parameters(
            await self._get_entity_class_name()
        )

        builder.set_query(
            identifier_type=identifier_type,
            identifier_value=identifier_value,
        )
        async for doc in HalApiClient().fetch(builder.build()):
            yield JsonRawResult(
                payload=doc,
                source_identifier=doc.get("halId_s"),
                formatter_name=HalHarvester.FORMATTER_NAME,
            )
