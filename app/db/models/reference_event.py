from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReferenceEvent(Base):
    """
    Model for persistence of events related to references
    """

    __tablename__ = "reference_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)

    enhanced: Mapped[bool] = mapped_column(
        nullable=False, index=False, default=False, server_default="false"
    )

    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id"), index=True)
    reference: Mapped["app.db.models.reference.Reference"] = relationship(
        "app.db.models.reference.Reference",
        back_populates="reference_events",
        lazy="joined",
    )

    harvesting_id: Mapped[int] = mapped_column(ForeignKey("harvestings.id"), index=True)
    harvesting: Mapped["app.db.models.harvesting.Harvesting"] = relationship(
        "app.db.models.harvesting.Harvesting",
        back_populates="reference_events",
        lazy="joined",
    )

    class Type(Enum):
        """Reference events types"""

        CREATED = "created"
        UPDATED = "updated"
        DELETED = "deleted"
        UNCHANGED = "unchanged"
