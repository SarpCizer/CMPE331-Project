"""Move JSON preference lists to ordered, owner-qualified relations without data loss."""
from alembic import op
import sqlalchemy as sa

revision = '0002_ordered_preferences'
down_revision = '0001_owned_schema'


def upgrade():
    connection = op.get_bind()
    op.create_index('uq_accounts_normalized_email','accounts',[sa.text('lower(email)')],unique=True)
    old = sa.Table('account_preferences',sa.MetaData(),autoload_with=connection,resolve_fks=False)
    saved = list(connection.execute(sa.select(old.c.owner_id,old.c.dietary,old.c.allergens)))
    for table_name,attribute in [('dietary_preferences','dietary'),('allergen_exclusions','allergens')]:
        table = op.create_table(table_name,
            sa.Column('owner_id',sa.String(128),sa.ForeignKey('account_preferences.owner_id',ondelete='CASCADE'),primary_key=True),
            sa.Column('position',sa.Integer(),primary_key=True),
            sa.Column('display_value',sa.String(128),nullable=False),
            sa.Column('value_key',sa.String(384),nullable=False),
            sa.CheckConstraint('position >= 0',name=f'ck_{table_name}_position'),
            sa.CheckConstraint('length(trim(display_value)) > 0',name=f'ck_{table_name}_value'))
        for row in saved:
            values = getattr(row,attribute)
            if values:
                connection.execute(table.insert(),[{'owner_id':row.owner_id,'position':index,
                    'display_value':value,'value_key':value.strip().casefold()}
                    for index,value in enumerate(values)])
    # Direct DROP COLUMN works on PostgreSQL and supported SQLite >= 3.35,
    # avoiding a parent-table rebuild that could cascade-delete the new rows.
    op.drop_column('account_preferences','dietary')
    op.drop_column('account_preferences','allergens')


def downgrade():
    connection = op.get_bind()
    op.add_column('account_preferences',sa.Column('dietary',sa.JSON(),nullable=False,server_default='[]'))
    op.add_column('account_preferences',sa.Column('allergens',sa.JSON(),nullable=False,server_default='[]'))
    old = sa.Table('account_preferences',sa.MetaData(),autoload_with=connection,resolve_fks=False)
    for owner in connection.scalars(sa.select(old.c.owner_id)):
        lists = {}
        for name,attribute in [('dietary_preferences','dietary'),('allergen_exclusions','allergens')]:
            source = sa.Table(name,sa.MetaData(),autoload_with=connection,resolve_fks=False)
            lists[attribute] = list(connection.scalars(sa.select(source.c.display_value)
                .where(source.c.owner_id == owner).order_by(source.c.position)))
        connection.execute(old.update().where(old.c.owner_id == owner).values(**lists))
    op.drop_table('allergen_exclusions')
    op.drop_table('dietary_preferences')
    op.drop_index('uq_accounts_normalized_email',table_name='accounts')
