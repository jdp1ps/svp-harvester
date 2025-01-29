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

    first_name: str | None = None

    last_name: str | None = None

    name_variants: list[str] = []

    structured_name_variants: list[dict] = []

    identifiers: list[ContributorIdentifier] = []
