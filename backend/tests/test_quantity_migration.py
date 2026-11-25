"""Existing rows retain identity and unknown amounts through the new migration."""
import json
from sqlalchemy import text

from fridgely_app.database import make_engine, migrate
from fridgely_recipes.provider import recipe_input
from fridgely_recipes.service import GenerationInput


def test_quantity_upgrade_preserves_existing_inventory_and_preferences(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    try:
        migrate(engine, '0002_ordered_preferences')
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO accounts (id,email,password_hash,created_at) VALUES ('legacy','legacy@example.test','synthetic-hash',CURRENT_TIMESTAMP)"))
            connection.execute(text("INSERT INTO account_preferences (owner_id) VALUES ('legacy')"))
            connection.execute(text("INSERT INTO dietary_preferences (owner_id,position,display_value,value_key) VALUES ('legacy',0,' Vegan ','vegan')"))
            connection.execute(text("INSERT INTO inventory_entries (id,owner_id,name,added_at) VALUES ('rice-id','legacy','rice',CURRENT_TIMESTAMP)"))
            before = tuple(connection.execute(text('SELECT id,owner_id,name,added_at FROM inventory_entries')).one())
        migrate(engine)
        migrate(engine)
        with engine.connect() as connection:
            after = tuple(connection.execute(text('SELECT id,owner_id,name,added_at,quantity,unit FROM inventory_entries')).one())
            assert after == (*before, None, None)
            assert connection.execute(text('SELECT owner_id,position,display_value,value_key FROM dietary_preferences')).one() == ('legacy', 0, ' Vegan ', 'vegan')
    finally:
        engine.dispose()


def test_provider_serializes_known_amounts_without_changing_ingredient_names():
    data = GenerationInput(('rice', 'tomato'), ('vegan',), ('peanut',),
        (('rice', 0.5, 'kg'), ('tomato', None, None)))
    payload = json.loads(recipe_input(data))
    assert payload == {'ingredients': ['rice', 'tomato'], 'dietary': ['vegan'],
        'allergens': ['peanut'], 'availableAmounts': [{'name': 'rice', 'quantity': 0.5, 'unit': 'kg'}]}
