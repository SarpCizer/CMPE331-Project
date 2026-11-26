"""Add owner/week/slot plans without changing recipes or existing collections."""
from alembic import op
import sqlalchemy as sa

revision = '0007_weekly_meal_plans'
down_revision = '0006_shopping_quantities'


def upgrade():
    op.create_table('weekly_meals',
        sa.Column('owner_id', sa.String(128), primary_key=True),
        sa.Column('week_start', sa.Date(), primary_key=True),
        sa.Column('day', sa.Integer(), primary_key=True),
        sa.Column('meal', sa.String(12), primary_key=True),
        sa.Column('recipe_id', sa.String(128), nullable=True),
        sa.Column('servings', sa.Integer(), nullable=True),
        sa.Column('revision', sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id', 'recipe_id'], ['recipes.owner_id', 'recipes.id'], ondelete='CASCADE'),
        sa.CheckConstraint('(recipe_id IS NULL AND servings IS NULL) OR (recipe_id IS NOT NULL AND servings IS NOT NULL AND servings >= 1 AND servings <= 20)', name='ck_weekly_servings'),
        sa.CheckConstraint('day >= 0 AND day <= 6', name='ck_weekly_day'),
        sa.CheckConstraint("meal IN (" + ",".join(f"'dish-{i}'" for i in range(1,21)) + ")", name='ck_weekly_meal'))


def downgrade():
    op.drop_table('weekly_meals')
