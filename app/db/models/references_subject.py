from sqlalchemy import Column, ForeignKey, Table

from app.db.session import Base

references_subjects_table = Table(
    "references_subjects_table",
    Base.metadata,
    Column("reference_id", ForeignKey("references.id"), index=True),
    Column("concept_id", ForeignKey("concepts.id"), index=True),
)
