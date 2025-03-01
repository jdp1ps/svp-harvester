"""Add index to harvesting_error

Revision ID: d96ebb9172a3
Revises: e6c4f376a58e
Create Date: 2024-10-27 13:58:21.001378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd96ebb9172a3'
down_revision: Union[str, None] = 'e6c4f376a58e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_harvesting_errors_harvesting_id'), 'harvesting_errors', ['harvesting_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_harvesting_errors_harvesting_id'), table_name='harvesting_errors')
    # ### end Alembic commands ###
