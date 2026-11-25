from alembic import context

connection = context.config.attributes.get('connection')
if connection is None:
    raise RuntimeError('Use python -m fridgely_app migrate with DATABASE_URL')
context.configure(connection=connection)
with context.begin_transaction():
    context.run_migrations()
