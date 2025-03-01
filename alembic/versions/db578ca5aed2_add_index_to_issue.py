"""Add index to issue

Revision ID: db578ca5aed2
Revises: d96ebb9172a3
Create Date: 2024-10-27 13:59:27.507771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db578ca5aed2'
down_revision: Union[str, None] = 'd96ebb9172a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_issues_journal_id'), 'issues', ['journal_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_issues_journal_id'), table_name='issues')
    # ### end Alembic commands ###
