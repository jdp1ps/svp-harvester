from datetime import datetime
from typing import List

from semver import VersionInfo
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.models.abstract import Abstract
from app.db.models.references_subject import references_subjects_table
from app.db.models.references_document_type import references_document_type_table
from app.db.models.versioned_record import VersionedRecord
from app.db.session import Base

# temporary imports
from app.db.models.contribution import Contribution  # pylint: disable=unused-import
from app.db.models.contributor import Contributor  # pylint: disable=unused-import
from app.db.models.issue import Issue  # pylint: disable=unused-import
from app.db.models.organization import Organization  # pylint: disable=unused-import
from app.db.models.title import Title  # pylint: disable=unused-import
from app.db.models.subtitle import Subtitle  # pylint: disable=unused-import
from app.db.models.document_type import DocumentType  # pylint: disable=unused-import
from app.db.models.reference_identifier import (  # pylint: disable=unused-import
    ReferenceIdentifier,
)
from app.db.models.reference_manifestation import (  # pylint: disable=unused-import
    ReferenceManifestation,
)
from app.db.models.book import Book  # pylint: disable=unused-import
from app.db.models.contributor_identifier import (  # pylint: disable=unused-import
    ContributorIdentifier,
)


class Reference(Base, VersionedRecord):
    """
    Model for persistence of references
    """

    __tablename__ = "references"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_identifier: Mapped[str] = mapped_column(nullable=False, index=True)

    # The reference should stay traceable to the harvester that created it
    # even if the harvesting history is cleaned up
    harvester: Mapped[str] = mapped_column(nullable=False, index=True)

    harvester_version: Mapped[str] = mapped_column(
        nullable=False, index=False, server_default="0.0.0"
    )

    identifiers: Mapped[
        List["app.db.models.reference_identifier.ReferenceIdentifier"]
    ] = relationship(
        "app.db.models.reference_identifier.ReferenceIdentifier",
        back_populates="reference",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    manifestations: Mapped[
        List["app.db.models.reference_manifestation.ReferenceManifestation"]
    ] = relationship(
        "app.db.models.reference_manifestation.ReferenceManifestation",
        back_populates="reference",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    titles: Mapped[List["app.db.models.title.Title"]] = relationship(
        "app.db.models.title.Title",
        back_populates="reference",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    subtitles: Mapped[List["app.db.models.subtitle.Subtitle"]] = relationship(
        "app.db.models.subtitle.Subtitle",
        back_populates="reference",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    abstracts: Mapped[List[Abstract]] = relationship(
        "app.db.models.abstract.Abstract",
        back_populates="reference",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    subjects: Mapped[List["app.db.models.concept.Concept"]] = relationship(
        "app.db.models.concept.Concept",
        secondary=references_subjects_table,
        lazy="noload",
    )

    document_type: Mapped[
        List["app.db.models.document_type.DocumentType"]
    ] = relationship(
        "app.db.models.document_type.DocumentType",
        secondary=references_document_type_table,
        lazy="joined",
    )

    reference_events: Mapped[
        List["app.db.models.reference_event.ReferenceEvent"]
    ] = relationship(
        "app.db.models.reference_event.ReferenceEvent",
        back_populates="reference",
        cascade="all, delete",
        lazy="raise",
    )

    contributions: Mapped[
        List["app.db.models.contribution.Contribution"]
    ] = relationship(
        "app.db.models.contribution.Contribution",
        back_populates="reference",
        cascade="all, delete",
        lazy="joined",
    )

    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id"), nullable=True, index=True
    )
    issue: Mapped["app.db.models.issue.Issue"] = relationship(
        "app.db.models.issue.Issue",
        back_populates="references",
        lazy="noload",
    )

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=True, index=True
    )
    book: Mapped["app.db.models.book.Book"] = relationship(
        "app.db.models.book.Book",
        back_populates="references",
        lazy="noload",
    )

    page: Mapped[str] = mapped_column(nullable=True, index=True)

    issued: Mapped[datetime] = mapped_column(nullable=True, index=True)
    # raw_issued preserves original date as string
    raw_issued: Mapped[str] = mapped_column(nullable=True)
    created: Mapped[datetime] = mapped_column(nullable=True, index=True)

    @validates("harvester_version")
    def _validate_version(self, key, version):
        try:
            parsed_version = VersionInfo.parse(version)
            return str(parsed_version)
        except ValueError as exc:
            raise ValueError(
                f"Invalid semantic version: {version} for field {key}"
            ) from exc
