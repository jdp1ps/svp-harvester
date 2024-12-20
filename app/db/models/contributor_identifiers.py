from sqlalchemy import Column, ForeignKey, Table

from app.db.session import Base

contributor_identifiers_table = Table(
    "contributor_identifiers_table",
    Base.metadata,
    Column("contributor_id", ForeignKey("contributors.id"), index=True),
    Column(
        "external_person_identifier_id",
        ForeignKey("external_person_identifiers.id"),
        index=True,
    ),
)
