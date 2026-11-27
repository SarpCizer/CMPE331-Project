"""Invalidate earlier sessions after explicit password rotation; preserve accounts."""
from alembic import op
import sqlalchemy as sa

revision = '0008_account_security'
down_revision = '0007_weekly_meal_plans'


def upgrade():
    op.add_column('accounts', sa.Column('auth_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('accounts', 'auth_version')
