"""
Identifiers model
"""

from pydantic import BaseModel, ConfigDict


class ExternalPersonIdentifier(BaseModel):
    """External person identifier model"""

    model_config = ConfigDict(from_attributes=True)

    source: str
    type: str
    value: str
