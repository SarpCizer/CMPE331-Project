"""Persist owner-scoped cooking request IDs without changing existing stock."""
from alembic import op
import sqlalchemy as sa

revision = '0005_cooking_confirmations'
down_revision = '0004_recipe_ingredient_amounts'


def upgrade():
    op.create_table('cooking_confirmations',
        sa.Column('owner_id', sa.String(128), sa.ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('request_id', sa.String(64), primary_key=True),
        sa.Column('recipe_id', sa.String(128), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False))


def downgrade():
    op.drop_table('cooking_confirmations')
