
from test_accounts_database import core, user
import pytest

def test_quantity_roundtrip_and_owner_update(core):
    _, alice = user(core.client)
    _, bob = user(core.client, 'bob@example.test')
    response = core.client.post('/inventory', headers=alice, json={'name':'Tomato','quantity':0.5,'unit':'kg'})
    assert response.status_code == 201
    item = response.json()
    assert item['quantity'] == 0.5 and item['unit'] == 'kg'
    assert core.client.get('/inventory', headers=alice).json() == [item]
    path = '/inventory/' + item['id']
    assert core.client.patch(path, headers=bob, json={'quantity':2,'unit':'pcs'}).status_code == 404
    updated = core.client.patch(path, headers=alice, json={'quantity':2,'unit':'pcs'})
    assert updated.status_code == 200
    assert updated.json() == {**item,'quantity':2,'unit':'pcs'}
    assert core.client.get('/inventory', headers=alice).json() == [updated.json()]

@pytest.mark.parametrize('quantity,unit', [(0,'kg'),(-1,'kg'),(1,'bad'),(True,'pcs'),(1.5,'pcs'),(1,None)])
def test_invalid_quantity(core, quantity, unit):
    _, headers = user(core.client)
    assert core.client.post('/inventory', headers=headers, json={'name':'Tomato','quantity':quantity,'unit':unit}).status_code == 400
    assert core.client.get('/inventory', headers=headers).json() == []
