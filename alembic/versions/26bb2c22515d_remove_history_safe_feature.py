"""Remove 'history safe' feature

Revision ID: 26bb2c22515d
Revises: 5f00ad57e5ed
Create Date: 2024-03-30 11:12:46.251900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26bb2c22515d'
down_revision: Union[str, None] = '5f00ad57e5ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_harvestings_history', table_name='harvestings')
    op.drop_column('harvestings', 'history')
    op.drop_index('ix_reference_events_history', table_name='reference_events')
    op.drop_column('reference_events', 'history')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reference_events', sa.Column('history', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.create_index('ix_reference_events_history', 'reference_events', ['history'], unique=False)
    op.add_column('harvestings', sa.Column('history', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.create_index('ix_harvestings_history', 'harvestings', ['history'], unique=False)
    # ### end Alembic commands ###
