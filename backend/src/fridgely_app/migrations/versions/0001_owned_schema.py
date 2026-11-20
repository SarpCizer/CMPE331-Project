"""Initial shared schema, with database-enforced personal ownership.

Revision ID: 0001_owned_schema
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_owned_schema'
down_revision = None


def upgrade():
    op.create_table('accounts',
        sa.Column('id',sa.String(128),primary_key=True),
        sa.Column('email',sa.String(254),nullable=False,unique=True),
        sa.Column('password_hash',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('account_preferences',
        sa.Column('owner_id',sa.String(128),sa.ForeignKey('accounts.id',ondelete='CASCADE'),primary_key=True),
        sa.Column('dietary',sa.JSON(),nullable=False), sa.Column('allergens',sa.JSON(),nullable=False))
    op.create_table('inventory_entries',
        sa.Column('id',sa.String(128),primary_key=True),
        sa.Column('owner_id',sa.String(128),sa.ForeignKey('accounts.id',ondelete='CASCADE'),nullable=False),
        sa.Column('name',sa.String(256),nullable=False),
        sa.Column('added_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint('length(trim(name)) > 0',name='ck_inventory_name'))
    op.create_index('ix_inventory_entries_owner_id','inventory_entries',['owner_id'])
    op.create_table('recipes',
        sa.Column('id',sa.String(128),primary_key=True),
        sa.Column('owner_id',sa.String(128),sa.ForeignKey('accounts.id',ondelete='CASCADE'),nullable=False),
        sa.Column('title',sa.Text(),nullable=False),
        sa.Column('cooking_minutes',sa.Float(),nullable=False),
        sa.Column('calories_per_serving',sa.Float(),nullable=False),
        sa.Column('servings',sa.Integer(),nullable=False),
        sa.UniqueConstraint('owner_id','id',name='uq_recipes_owner_id'),
        sa.CheckConstraint('cooking_minutes > 0',name='ck_recipes_cooking_minutes'),
        sa.CheckConstraint('calories_per_serving >= 0',name='ck_recipes_calories'),
        sa.CheckConstraint('servings > 0',name='ck_recipes_servings'))
    op.create_index('ix_recipes_owner','recipes',['owner_id'])
    for table, column in [('recipe_ingredients','name'),('recipe_steps','instruction')]:
        columns = [sa.Column('recipe_id',sa.String(128),sa.ForeignKey('recipes.id',ondelete='CASCADE'),primary_key=True),
            sa.Column('position',sa.Integer(),primary_key=True),sa.Column(column,sa.Text(),nullable=False)]
        if table == 'recipe_ingredients':
            columns.append(sa.Column('name_key',sa.Text(),nullable=False))
        op.create_table(table,*columns)
    op.create_table('shopping_items',
        sa.Column('id',sa.String(128),primary_key=True),
        sa.Column('owner_id',sa.String(128),sa.ForeignKey('accounts.id',ondelete='CASCADE'),nullable=False),
        sa.Column('name',sa.String(256),nullable=False),sa.Column('name_key',sa.String(512),nullable=False),
        sa.UniqueConstraint('owner_id','name_key',name='uq_shopping_owner_name'),
        sa.CheckConstraint('length(name) > 0',name='ck_shopping_name'))
    for table in ['favorites','recipe_views']:
        columns = [sa.Column('owner_id',sa.String(128),primary_key=True),
            sa.Column('recipe_id',sa.String(128),primary_key=True),
            sa.ForeignKeyConstraint(['owner_id','recipe_id'],['recipes.owner_id','recipes.id'],ondelete='CASCADE')]
        if table == 'recipe_views':
            columns.append(sa.Column('last_viewed_at',sa.DateTime(timezone=True),nullable=False))
        op.create_table(table,*columns)
    op.create_index('ix_recipe_views_owner_recent','recipe_views',['owner_id','last_viewed_at'])


def downgrade():
    for table in ['recipe_views','favorites','shopping_items','recipe_steps','recipe_ingredients',
                  'recipes','inventory_entries','account_preferences','accounts']:
        op.drop_table(table)
