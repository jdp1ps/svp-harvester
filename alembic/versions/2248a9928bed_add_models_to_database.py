"""Add models to database

Revision ID: 2248a9928bed
Revises: 
Create Date: 2023-10-10 17:53:38.286498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2248a9928bed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('concepts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uri', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uri')
    )
    op.create_index(op.f('ix_concepts_id'), 'concepts', ['id'], unique=False)
    op.create_table('entities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('literal_fields',
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('language', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_literal_fields_id'), 'literal_fields', ['id'], unique=False)
    op.create_index(op.f('ix_literal_fields_language'), 'literal_fields', ['language'], unique=False)
    op.create_table('references',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_identifier', sa.String(), nullable=False),
    sa.Column('hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_references_hash'), 'references', ['hash'], unique=False)
    op.create_index(op.f('ix_references_id'), 'references', ['id'], unique=False)
    op.create_index(op.f('ix_references_source_identifier'), 'references', ['source_identifier'], unique=False)
    op.create_table('identifiers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_identifiers_id'), 'identifiers', ['id'], unique=False)
    op.create_index(op.f('ix_identifiers_type'), 'identifiers', ['type'], unique=False)
    op.create_index(op.f('ix_identifiers_value'), 'identifiers', ['value'], unique=False)
    op.create_table('labels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ),
    sa.ForeignKeyConstraint(['id'], ['literal_fields.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('people',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['entities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('references_subjects_table',
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('concept_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], )
    )
    op.create_table('retrievals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retrievals_id'), 'retrievals', ['id'], unique=False)
    op.create_table('subtitles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['literal_fields.id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('titles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['literal_fields.id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('harvestings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('harvester', sa.String(), nullable=False),
    sa.Column('retrieval_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['retrieval_id'], ['retrievals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_harvestings_harvester'), 'harvestings', ['harvester'], unique=False)
    op.create_index(op.f('ix_harvestings_id'), 'harvestings', ['id'], unique=False)
    op.create_index(op.f('ix_harvestings_state'), 'harvestings', ['state'], unique=False)
    op.create_table('reference_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.Column('harvesting_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['harvesting_id'], ['harvestings.id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reference_events_id'), 'reference_events', ['id'], unique=False)
    op.create_index(op.f('ix_reference_events_type'), 'reference_events', ['type'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_reference_events_type'), table_name='reference_events')
    op.drop_index(op.f('ix_reference_events_id'), table_name='reference_events')
    op.drop_table('reference_events')
    op.drop_index(op.f('ix_harvestings_state'), table_name='harvestings')
    op.drop_index(op.f('ix_harvestings_id'), table_name='harvestings')
    op.drop_index(op.f('ix_harvestings_harvester'), table_name='harvestings')
    op.drop_table('harvestings')
    op.drop_table('titles')
    op.drop_table('subtitles')
    op.drop_index(op.f('ix_retrievals_id'), table_name='retrievals')
    op.drop_table('retrievals')
    op.drop_table('references_subjects_table')
    op.drop_table('people')
    op.drop_table('labels')
    op.drop_index(op.f('ix_identifiers_value'), table_name='identifiers')
    op.drop_index(op.f('ix_identifiers_type'), table_name='identifiers')
    op.drop_index(op.f('ix_identifiers_id'), table_name='identifiers')
    op.drop_table('identifiers')
    op.drop_index(op.f('ix_references_source_identifier'), table_name='references')
    op.drop_index(op.f('ix_references_id'), table_name='references')
    op.drop_index(op.f('ix_references_hash'), table_name='references')
    op.drop_table('references')
    op.drop_index(op.f('ix_literal_fields_language'), table_name='literal_fields')
    op.drop_index(op.f('ix_literal_fields_id'), table_name='literal_fields')
    op.drop_table('literal_fields')
    op.drop_table('entities')
    op.drop_index(op.f('ix_concepts_id'), table_name='concepts')
    op.drop_table('concepts')
    # ### end Alembic commands ###
