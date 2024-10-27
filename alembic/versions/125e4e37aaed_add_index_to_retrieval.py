"""Add index to retrieval

Revision ID: 125e4e37aaed
Revises: db578ca5aed2
Create Date: 2024-10-27 14:01:59.932927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '125e4e37aaed'
down_revision: Union[str, None] = 'db578ca5aed2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_retrievals_entity_id'), 'retrievals', ['entity_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_retrievals_entity_id'), table_name='retrievals')
    # ### end Alembic commands ###
