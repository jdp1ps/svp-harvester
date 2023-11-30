from app.db.models.reference import Reference
from app.harvesters.abstract_harvester_raw_result import AbstractHarvesterRawResult
from app.harvesters.abstract_references_converter import AbstractReferencesConverter
from app.harvesters.json_harvester_raw_result import (
    JsonHarvesterRawResult as JsonRawResult,
)
from app.db.models.abstract import Abstract
from app.db.models.reference import Reference
from app.db.models.title import Title
from app.db.models.subtitle import Subtitle


class ScanrReferencesConverter(AbstractReferencesConverter):
    """
    Converts raw data from ScanR to a normalised Reference object
    """

    async def convert(self, raw_data: JsonRawResult) -> Reference:
        """
        Convert raw data from ScanR to a normalised Reference object
        :param raw_data: raw data from ScanR
        :return: Reference object
        """
        new_ref = Reference()

        json_payload = raw_data.payload

        title = json_payload["_source"].get("title")
        if title:
            new_ref.titles.extend(
                [Title(value=value, language=None if key == "default" else key) for key, value in
                 title.items()])

        summary = json_payload["_source"].get("summary")
        if summary:
            new_ref.abstracts.extend(
                [Abstract(value=value, language=None if key == "default" else key) for key, value in
                 summary.items()])

        new_ref.hash = self._hash(json_payload)
        new_ref.harvester = "scanR"
        new_ref.source_identifier = json_payload["_source"].get("id")
        return new_ref

    def _hash_keys(self):
        return [
            "id",
            "title",
            "summary",
            "type",
            "productionType",
            "publicationDate",
            "domains",
            "affiliations",
            "authors",
            "externalIds"
        ]
