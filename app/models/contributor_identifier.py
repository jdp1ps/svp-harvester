"""
Identifiers model
"""

from pydantic import BaseModel, ConfigDict


class ContributorIdentifier(BaseModel):
    """External person identifier model"""

    model_config = ConfigDict(from_attributes=True)

    source: str
    type: str
    value: str
