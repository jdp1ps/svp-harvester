"""
Person model
"""

from pydantic import ConfigDict, model_validator
from pydantic_core.core_schema import ValidationInfo

from app.config import get_app_settings
from app.models.entities import Entity

BIBLIOGRAPHIC_IDENTIFIERS = ["idref", "id_hal_i", "id_hal_s", "orcid", "scopus_eid"]


class Person(Entity):
    """
    Person identified by at least full name or one of the identifiers
    """

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _check_minimal_information(cls, data: dict, _: ValidationInfo) -> dict:
        settings = get_app_settings()
        if identifier := data.get("identifiers"):
            # check that each identifier is a hash with type and value
            assert all(
                isinstance(i, dict) and i.get("type") and i.get("value")
                for i in identifier
            ), "Each identifier must be a hash with type and value"

        # check that there is at least one identifier
        has_valid_identifier = any(
            # pylint: disable=cell-var-from-loop
            list(
                filter(
                    lambda h: h.get("type", None) == t.get("key"),
                    data.get("identifiers", []) or [],
                )
            )
            for t in settings.identifiers
        )

        # check if full_name is provided
        has_name = "name" in data and data["name"]

        # check that there is at least one identifier
        assert (
            has_valid_identifier or has_name
        ), "At least one identifier or the entire name must be provided"

        return data

    @model_validator(mode="before")
    @classmethod
    def _check_identifiers_referenced_in_settings(
        cls, data: dict, _: ValidationInfo
    ) -> dict:
        settings = get_app_settings()
        # check that all provider identifiers are referenced in settings
        # and list the invalid identifiers in assertion error message
        invalid_identifiers = [
            identifier.get("type")
            for identifier in data.get("identifiers", [])
            if identifier.get("type")
            not in [
                identifier_type.get("key") for identifier_type in settings.identifiers
            ]
        ]
        assert not invalid_identifiers, (
            f"Invalid identifiers: {', '.join(invalid_identifiers)}. "
            "Valid identifiers are:"
            f"{', '.join([identifier_type.get('key') for identifier_type in settings.identifiers])}"
        )
        return data

    def has_no_bibliographic_identifiers(self):
        """
        Check if the person has no bibliographic identifiers
        """
        return not any(
            identifier.type in BIBLIOGRAPHIC_IDENTIFIERS
            for identifier in self.identifiers
        )
