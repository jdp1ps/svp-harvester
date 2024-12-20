from enum import Enum

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.session import Base


class ExternalPersonIdentifier(Base):
    """
    Model for persistence of identifiers
    """

    class IdentifierType(Enum):
        """Enum for identifier types"""

        ORCID = "orcid"
        IDHAL = "id_hal"
        IDREF = "idref"
        SCOPUS = "scopus"

    __tablename__ = "external_person_identifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    value: Mapped[str] = mapped_column(nullable=False, index=True)
    source: Mapped[str] = mapped_column(nullable=False, index=True)

    __table_args__ = (UniqueConstraint("source", "type", "value"),)

    @validates("type", include_removes=False, include_backrefs=True)
    def _valid_identifier_is_among_supported_types(self, _, new_type):
        """
        Validate that the identifier is among the supported types
        """
        if new_type not in [identifier.value for identifier in self.IdentifierType]:
            raise ValueError("Identifier type is not among the supported types")
        return new_type
