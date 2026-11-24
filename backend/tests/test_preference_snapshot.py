"""US-03/NFR-03: paired ordered preferences need one owner-scoped SQL snapshot."""
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event

from fridgely_app.core import preference_lists
from fridgely_app.database import make_engine, migrate, session_factory
from fridgely_app.models import Account, Preferences


@pytest.mark.parametrize("database", ["sqlite", "postgresql"])
def test_paired_preference_lists_use_one_owned_snapshot_query(tmp_path, database):
    url = (f"sqlite:///{tmp_path / 'snapshot.db'}" if database == "sqlite"
           else os.getenv("TEST_DATABASE_URL"))
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for the PostgreSQL snapshot check")
    engine = make_engine(url)
    try:
        migrate(engine)
        sessions = session_factory(engine)
        alice, bob = uuid4().hex, uuid4().hex
        expected = ([" Vegan ", "low,sodium", "Vegan", "Vegan"], [" Peanut ", "peanut"])
        with sessions.begin() as session:
            for owner in [alice, bob]:
                session.add(Account(id=owner, email=f"snapshot-{owner}@example.test",
                    password_hash="not-used-by-this-storage-test", created_at=datetime.now(timezone.utc)))
            session.flush()
            session.add_all([
                Preferences(owner_id=alice, dietary=expected[0], allergens=expected[1]),
                Preferences(owner_id=bob, dietary=["other-owner"], allergens=[]),
            ])

        statements = []

        def capture(_connection, _cursor, statement, _parameters, _context, _many):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", capture)
        try:
            with sessions() as session:
                assert preference_lists(session, alice) == expected
            assert len(statements) == 1, "Both ordered lists must share one SQL snapshot, not lazy per-list reads"
            statements.clear()
            with sessions() as session:
                assert preference_lists(session, bob) == (["other-owner"], [])
            assert len(statements) == 1
            statements.clear()
            with sessions() as session:
                assert preference_lists(session, uuid4().hex) == ([], [])
            assert len(statements) == 1
        finally:
            event.remove(engine, "before_cursor_execute", capture)
    finally:
        engine.dispose()
