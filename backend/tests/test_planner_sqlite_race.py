from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from sqlalchemy import event,select,func
from fridgely_recipes.storage import Recipe
from test_planner_requested_recipes import custom,generate,WEEK


def test_sqlite_generation_first_write_cannot_overwrite_a_newer_committed_edit(custom):
    if custom.database!='sqlite':pytest.skip('SQLite-specific first-write interleaving; PostgreSQL uses owner row locks')
    first=generate(custom,servings=1).json()['entries'][0]['recipe']['id']
    paused,release=Event(),Event()
    engine=custom.client.app.state.engine
    def pause_first_write(_connection,_cursor,statement,_parameters,_context,_many):
        if not paused.is_set() and statement.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')):
            paused.set()
            assert release.wait(10),'Test scheduling timed out'
    event.listen(engine,'before_cursor_execute',pause_first_write)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(generate,custom,'New generated dish',2)
            try:
                assert paused.wait(5),'Generation did not reach its first write'
                saved=custom.client.put('/api/weekly-plan/0/dish-1',headers=custom.headers,
                    json={'weekStart':WEEK,'recipeId':first,'servings':3})
                assert saved.status_code==200
            finally:release.set()
            assert pending.result(timeout=10).status_code==409
    finally:
        release.set();event.remove(engine,'before_cursor_execute',pause_first_write)
    entry,=custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']
    assert entry['recipe']['id']==first and entry['servings']==3
    with custom.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id==custom.owner))==1
