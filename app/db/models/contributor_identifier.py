from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from app.db.session import Base


class ContributorIdentifier(Base):
    """
    Model for persistence of identifiers
    """

    class IdentifierType(Enum):
        """Enum for identifier types"""

        ORCID = "orcid"
        OPEN_ALEX = "open_alex"
        IDHAL = "idhal"
        IDREF = "idref"
        SCOPUS = "scopus"
        GOOGLE_SCHOLAR = "google_scholar"
        VIAF = "viaf"
        ISNI = "isni"

    __tablename__ = "contributor_identifier"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    value: Mapped[str] = mapped_column(nullable=False, index=True)
    source: Mapped[str] = mapped_column(nullable=False, index=True)

    contributor_id: Mapped[int] = mapped_column(
        ForeignKey("contributors.id"), nullable=False, index=True
    )
    contributor: Mapped["app.db.models.contributor.Contributor"] = relationship(
        "app.db.models.contributor.Contributor",
        back_populates="identifiers",
        lazy="joined",
        cascade="all",
    )

    @validates("type", include_removes=False, include_backrefs=True)
    def _valid_identifier_is_among_supported_types(self, _, new_type):
        """
        Validate that the identifier is among the supported types
        """
        if new_type not in [identifier.value for identifier in self.IdentifierType]:
            raise ValueError(f"Identifier type {new_type} is not supported")
        return new_type

    @validates("value")
    def _validate_orcid_value(self, _, new_value):
        """
        If type is ORCID, ensure value begins with https://orcid.org/
        """
        if self.type == self.IdentifierType.ORCID.value:
            orcid_prefix = "https://orcid.org/"
            if not new_value.startswith(orcid_prefix):
                new_value = orcid_prefix + new_value
        return new_value
