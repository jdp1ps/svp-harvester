from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.session import Base


class OrganizationIdentifier(Base):
    """
    Model for persistence of organization identifiers
    """

    __tablename__ = "organization_identifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    value: Mapped[str] = mapped_column(nullable=False, index=True)

    organization: Mapped["app.db.models.organization.Organization"] = relationship(
        "app.db.models.organization.Organization",
        back_populates="identifiers",
        lazy="raise",
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
