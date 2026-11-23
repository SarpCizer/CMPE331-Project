"""Issue #34 / #30: dependency faults must not bypass the owned-detail boundary."""
from datetime import datetime

import pytest

from test_collections_api import call


@pytest.mark.parametrize("recipe_id", ["missing-recipe", "bob-recipe"])
def test_unavailable_clock_cannot_mask_missing_or_foreign_recipe(h, recipe_id):
    calls = []

    def unavailable_clock():
        calls.append("called")
        raise RuntimeError("CLOCK_SECRET must never appear in the API")

    h.app.state.collections.clock = unavailable_clock
    response = call(h, "GET", f"/recipes/{recipe_id}")

    assert response.status_code == 404
    assert calls == [], "A denied/missing recipe must not request a view timestamp"
    assert call(h, "GET", "/history").json() == []


@pytest.mark.parametrize("recipe_id", ["missing-recipe", "bob-recipe"])
def test_invalid_clock_cannot_mask_missing_or_foreign_recipe(h, recipe_id):
    h.clock.now = datetime(2026, 11, 23)  # Deliberately invalid, timezone-less dependency.
    response = call(h, "GET", f"/recipes/{recipe_id}")

    assert response.status_code == 404
    assert call(h, "GET", "/history").json() == []


def test_clock_outage_is_retryable_service_failure_and_preserves_existing_history(h):
    assert call(h, "GET", "/recipes/recipe-a").status_code == 200
    before = call(h, "GET", "/history").json()
    inventory = h.snapshot()

    def unavailable_clock():
        raise RuntimeError("CLOCK_SECRET must never appear in the API")

    h.app.state.collections.clock = unavailable_clock
    response = call(h, "GET", "/recipes/recipe-b")

    assert response.status_code == 503, "Unavailable view clock cannot produce HTTP success"
    assert set(response.json()) == {"error"}
    assert "CLOCK_SECRET" not in response.text
    assert call(h, "GET", "/history").json() == before
    assert h.snapshot() == inventory
