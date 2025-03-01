"""Add index to contribution

Revision ID: 9a14bd341cf1
Revises: e66091f3c19c
Create Date: 2024-10-27 10:31:43.400602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a14bd341cf1'
down_revision: Union[str, None] = 'e66091f3c19c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_contributions_contributor_id'), 'contributions', ['contributor_id'], unique=False)
    op.create_index(op.f('ix_contributions_reference_id'), 'contributions', ['reference_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_contributions_reference_id'), table_name='contributions')
    op.drop_index(op.f('ix_contributions_contributor_id'), table_name='contributions')
    # ### end Alembic commands ###
