"""Store optional display measurements alongside ordered recipe ingredients."""
from alembic import op
import sqlalchemy as sa

revision = "0004_recipe_ingredient_amounts"
down_revision = "0003_inventory_quantities"


def upgrade():
    op.add_column("recipe_ingredients", sa.Column("amount", sa.String(64), nullable=True))


def downgrade():
    op.drop_column("recipe_ingredients", "amount")
