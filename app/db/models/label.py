from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Label(Base):
    """
    Model for persistence of keyword labels
    """

    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(nullable=False, index=True)
    language: Mapped[str] = mapped_column(nullable=True, index=True)

    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    concept: Mapped["app.db.models.concept.Concept"] = relationship(
        "app.db.models.concept.Concept", back_populates="labels", lazy="raise"
    )

    preferred: Mapped[bool] = mapped_column(nullable=False, index=True, default=True)
