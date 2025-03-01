"""Add index to identifiers reference to entity

Revision ID: e77d3d377958
Revises: 3c097a1d478b
Create Date: 2024-10-27 10:05:41.102815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e77d3d377958'
down_revision: Union[str, None] = '3c097a1d478b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_identifiers_entity_id'), 'identifiers', ['entity_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_identifiers_entity_id'), table_name='identifiers')
    # ### end Alembic commands ###
