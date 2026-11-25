"""Preserve existing shopping rows and add durable purchase retry protection."""
from alembic import op
import sqlalchemy as sa

revision = '0006_shopping_quantities'
down_revision = '0005_cooking_confirmations'


def upgrade():
    op.add_column('shopping_items', sa.Column('quantity', sa.Float(), nullable=True))
    op.add_column('shopping_items', sa.Column('unit', sa.String(8), nullable=True))
    op.create_table('purchase_confirmations',
        sa.Column('owner_id', sa.String(128), sa.ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('item_id', sa.String(128), primary_key=True),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('inventory_id', sa.String(128), nullable=False))


def downgrade():
    op.drop_table('purchase_confirmations')
    op.drop_column('shopping_items', 'unit')
    op.drop_column('shopping_items', 'quantity')
