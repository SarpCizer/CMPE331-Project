"""Add optional amounts without inventing quantities for existing ingredients."""
from alembic import op
import sqlalchemy as sa

revision = '0003_inventory_quantities'
down_revision = '0002_ordered_preferences'

def upgrade():
    op.add_column('inventory_entries', sa.Column('quantity', sa.Float(), nullable=True))
    op.add_column('inventory_entries', sa.Column('unit', sa.String(8), nullable=True))

def downgrade():
    op.drop_column('inventory_entries', 'unit')
    op.drop_column('inventory_entries', 'quantity')
