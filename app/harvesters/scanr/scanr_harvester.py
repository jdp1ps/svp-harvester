from typing import AsyncGenerator

from semver import VersionInfo, Version

from app.harvesters.abstract_harvester import AbstractHarvester
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult as RawResult
from app.harvesters.scanr.scanr_api_query_builder import (
    ScanRApiQueryBuilder as QueryBuilder,
)
from app.harvesters.scanr.scanr_elastic_client import ScanRElasticClient


class ScanrHarvester(AbstractHarvester):
    """
    Harvester for Scanr API
    """

    FORMATTER_NAME = "SCANR"

    IDENTIFIERS_BY_ENTITIES = {
        "Person": [
            (QueryBuilder.QueryParameters.AUTH_IDREF, "idref"),
            (QueryBuilder.QueryParameters.AUTH_ORCID, "orcid"),
            (QueryBuilder.QueryParameters.AUTH_ID_HAL_S, "id_hal_s"),
        ]
    }

    supported_identifier_types = ["idref", "orcid", "id_hal_s"]

    VERSION: Version = VersionInfo.parse("1.6.0")

    async def _get_scanr_query_parameters(self, entity_class: str):
        """
        Set the query parameters for an entity
        """
        entity = await self._get_entity()

        query_parameters = self.IDENTIFIERS_BY_ENTITIES.get(entity_class)
        # List convenient query parameters for this entity class
        # and choose the first one for which value is provided

        for scanr_query_parameter, identifier_key in query_parameters:
            assert (
                identifier_key in self.supported_identifier_types
            ), "Unable to run Scanr harvester for a person without idref, orcid or id_hal_s"

            identifier_value = entity.get_identifier(identifier_key)
            if identifier_key == "idref" and identifier_value is not None:
                # create a scanr id from idref
                scanr_id = identifier_key + str(identifier_value)
                return scanr_id
            if identifier_value is not None:
                # Search for scanr id from other identifiers on Scanr API Person index
                scanr_id = await self._get_entity_scanr_id(
                    scanr_query_parameter, identifier_value
                )
                if scanr_id:
                    return scanr_id

        return None

    async def fetch_results(self) -> AsyncGenerator[RawResult, None]:
        async with ScanRElasticClient() as client:
            builder = QueryBuilder()

            scanr_id = await self._get_scanr_query_parameters(
                await self._get_entity_class_name()
            )
            if scanr_id is None:
                return
            builder.set_publication_query(scanr_id=scanr_id)

            client.set_query(elastic_query=builder.build())
            async for doc in client.perform_search(client.Indexes.PUBLICATIONS):
                yield RawResult(
                    payload=doc,
                    source_identifier=doc["_source"].get("id"),
                    formatter_name=ScanrHarvester.FORMATTER_NAME,
                )

    @staticmethod
    async def _get_entity_scanr_id(identifier_type, identifier_value: str):
        async with ScanRElasticClient() as client:
            builder = QueryBuilder()
            builder.set_person_query(identifier_type, identifier_value)

            client.set_query(elastic_query=builder.build())
            async for doc in client.perform_search(client.Indexes.PERSONS):
                return doc.get("_source", {}).get("id")
