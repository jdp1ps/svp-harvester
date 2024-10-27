from sqlalchemy import Column, ForeignKey, Table

from app.db.session import Base

references_document_type_table = Table(
    "references_document_types_table",
    Base.metadata,
    Column("reference_id", ForeignKey("references.id"), index=True),
    Column("document_type_id", ForeignKey("document_types.id"), index=True),
)
