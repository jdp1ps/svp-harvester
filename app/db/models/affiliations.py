from sqlalchemy import Column, ForeignKey, Table

from app.db.session import Base

affiliations_table = Table(
    "affiliations_table",
    Base.metadata,
    Column("contribution_id", ForeignKey("contributions.id"), index=True),
    Column("organization_id", ForeignKey("organizations.id"), index=True),
)
