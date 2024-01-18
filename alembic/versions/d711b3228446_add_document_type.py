"""Add Document Type

Revision ID: d711b3228446
Revises: a0fb77b73783
Create Date: 2024-01-17 14:09:11.840765

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd711b3228446'
down_revision: Union[str, None] = 'a0fb77b73783'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('document_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uri', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uri')
    )
    op.create_index(op.f('ix_document_types_id'), 'document_types', ['id'], unique=False)
    op.create_table('references_document_types_table',
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('document_type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], )
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('references_document_types_table')
    op.drop_index(op.f('ix_document_types_id'), table_name='document_types')
    op.drop_table('document_types')
    # ### end Alembic commands ###
