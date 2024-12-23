from pydantic import BaseModel, ConfigDict

from app.models.contributor_identifier import ContributorIdentifier


class Contributor(BaseModel):
    """
    Pydantic model matching Contributor sql_alchemy model
    """

    model_config = ConfigDict(from_attributes=True)

    source: str

    source_identifier: str | None

    name: str

    name_variants: list[str] = []

    identifiers: list[ContributorIdentifier] = []
