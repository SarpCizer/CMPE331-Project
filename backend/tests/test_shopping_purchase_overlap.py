from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Event

import pytest
from sqlalchemy import event, select

from fridgely_app.database import make_engine, migrate, session_factory
from fridgely_app.models import Account, InventoryEntry, PurchaseConfirmation
from fridgely_app.purchases import PurchaseCommand, _purchase
from fridgely_collections.errors import CollectionError
from fridgely_collections.models import ShoppingItem


@pytest.mark.parametrize('overlap_quantity, expected_result', [(2, (200, True)), (3, (409, None))])
def test_overlap_reconciles_a_committed_purchase_receipt(tmp_path, overlap_quantity, expected_result):
    engine = make_engine(f'sqlite:///{tmp_path / "purchase.db"}')
    migrate(engine)
    sessions = session_factory(engine)
    now = datetime.now(UTC)
    with sessions.begin() as session:
        session.add(Account(id='owner', email='owner@example.test', password_hash='fixture', created_at=now))
        session.add(ShoppingItem(id='list-item', owner_id='owner', name='egg', name_key='egg'))

    reading_item = Event()
    committed = Event()

    def hold_first_item_select(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith('SELECT shopping_items.') and not reading_item.is_set():
            reading_item.set()
            assert committed.wait(10), 'Winning purchase never committed'

    def attempt(quantity):
        try:
            with sessions.begin() as session:
                result = _purchase(session, 'owner', 'list-item', PurchaseCommand(quantity=quantity, unit='pcs'),
                                   str(quantity), lambda: now)
            return 200, result['replayed']
        except CollectionError as error:
            return error.status, None

    event.listen(engine, 'before_cursor_execute', hold_first_item_select)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(attempt, overlap_quantity)
            try:
                assert reading_item.wait(10), 'Overlapping purchase never reached the shopping item'
                assert attempt(2) == (200, False)
            finally:
                committed.set()
            observed = pending.result(timeout=10)
        assert attempt(2) == (200, True)
        with sessions() as session:
            assert session.scalars(select(InventoryEntry.quantity)).all() == [2]
            assert session.get(ShoppingItem, 'list-item') is None
            assert session.get(PurchaseConfirmation, ('owner', 'list-item')) is not None
        assert observed == expected_result
    finally:
        engine.dispose()
