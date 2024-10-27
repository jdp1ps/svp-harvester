from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.models.reference_literal_field import ReferenceLiteralField


class Title(ReferenceLiteralField):
    """Model for persistence of titles"""

    __tablename__ = "titles"
    __mapper_args__ = {"concrete": True}

    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id"), index=True)

    reference: Mapped["app.db.models.reference.Reference"] = relationship(
        "app.db.models.reference.Reference", back_populates="titles", lazy="raise"
    )
