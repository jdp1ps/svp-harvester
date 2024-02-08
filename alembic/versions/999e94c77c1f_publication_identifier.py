"""Publication Identifier

Revision ID: 999e94c77c1f
Revises: 447f9ad2f529
Create Date: 2024-02-08 17:33:57.983687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '999e94c77c1f'
down_revision: Union[str, None] = '447f9ad2f529'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('publication_identifiers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_publication_identifiers_type'), 'publication_identifiers', ['type'], unique=False)
    op.create_index(op.f('ix_publication_identifiers_value'), 'publication_identifiers', ['value'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_publication_identifiers_value'), table_name='publication_identifiers')
    op.drop_index(op.f('ix_publication_identifiers_type'), table_name='publication_identifiers')
    op.drop_table('publication_identifiers')
    # ### end Alembic commands ###
