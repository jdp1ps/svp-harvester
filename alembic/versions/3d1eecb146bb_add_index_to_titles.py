"""Add index to titles

Revision ID: 3d1eecb146bb
Revises: 6f89220087a9
Create Date: 2024-10-27 10:20:02.025241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d1eecb146bb'
down_revision: Union[str, None] = '6f89220087a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_titles_reference_id'), 'titles', ['reference_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_titles_reference_id'), table_name='titles')
    # ### end Alembic commands ###
