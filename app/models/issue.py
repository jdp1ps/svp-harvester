from pydantic import BaseModel, ConfigDict, field_validator

from app.models.journal import Journal


class Issue(BaseModel):
    """
    Pydantic model matching Issue sql_alchemy model
    """

    model_config = ConfigDict(from_attributes=True)

    source: str
    source_identifier: str

    titles: list[str] = []
    volume: str | None = None
    number: list[str] = []

    rights: str | None = None
    date: str | None = None

    journal: Journal

    @field_validator("number", mode="before")
    @classmethod
    def _filter_none_values(cls, v):
        return [num for num in v if num is not None]
