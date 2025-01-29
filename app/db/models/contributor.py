from typing import List

from sqlalchemy import String, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Contributor(Base):
    """
    Model for persistence of contributors
    """

    __tablename__ = "contributors"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(nullable=False, index=True)
    source_identifier: Mapped[str] = mapped_column(nullable=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)

    contributions: Mapped[
        List["app.db.models.contribution.Contribution"]
    ] = relationship(
        "app.db.models.contribution.Contribution",
        back_populates="contributor",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    identifiers: Mapped[
        List["app.db.models.contributor_identifier.ContributorIdentifier"]
    ] = relationship(
        "app.db.models.contributor_identifier.ContributorIdentifier",
        back_populates="contributor",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    name_variants: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=[]
    )
    structured_name_variants: Mapped[List[dict]] = mapped_column(
        JSONB, nullable=False, default=[]
    )

    # partial unique index on source and name when source_identifier is null
    # partial unique index on source and source_identifier when source_identifier is not null
    __table_args__ = (
        Index(
            "unique_name_per_source_if_no_identifier",
            "source",
            "name",
            unique=True,
            postgresql_where=(source_identifier.is_(None)),
        ),
        Index(
            "unique_source_identifier_per_source",
            "source",
            "source_identifier",
            unique=True,
            postgresql_where=(source_identifier.isnot(None)),
        ),
    )
