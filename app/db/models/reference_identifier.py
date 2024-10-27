from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.session import Base


class ReferenceIdentifier(Base):
    """
    Model for persistence of reference identifiers
    """

    __tablename__ = "reference_identifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    value: Mapped[str] = mapped_column(nullable=False, index=True)

    reference: Mapped["app.db.models.reference.Reference"] = relationship(
        "app.db.models.reference.Reference", back_populates="identifiers", lazy="raise"
    )
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id"), index=True)
