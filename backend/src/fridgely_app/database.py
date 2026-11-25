from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def make_engine(url: str):
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    options = {'pool_pre_ping': True}
    if url.startswith('sqlite:'):
        options['connect_args'] = {'check_same_thread': False, 'timeout': 15}
    else:
        options.update(pool_size=10, max_overflow=20)
    engine = create_engine(url, **options)
    if engine.dialect.name not in {'sqlite', 'postgresql'}:
        engine.dispose()
        raise ValueError('Use PostgreSQL or SQLite')
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def sqlite_settings(connection, _record):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=15000')
    return engine


def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)


def migrate(engine, revision='head'):
    """Explicit release/setup operation; never called by application import/startup."""
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parent / 'migrations'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, revision)
