import pytest
from service2 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    create_db_table()
    yield client

def test_add_good(client):
    response = client.post('/api/goods/add', json={
        "name": "Laptop",
        "category": "electronics",
        "price": 999.99,
        "description": "High-end gaming laptop",
        "stock_count": 10
    })
    assert response.status_code == 201
    assert response.json['name'] == "Laptop"

def test_get_good(client):
    response = client.get('/api/goods/1')
    assert response.status_code == 200
    assert response.json['name'] == "Laptop"

def test_update_good(client):
    response = client.put('/api/goods/update/1', json={
        "price": 899.99,
        "stock_count": 8
    })
    assert response.status_code == 200
    assert response.json['price'] == 899.99

def test_deduct_good(client):
    response = client.put('/api/goods/deduct/1', json={"quantity": 2})
    assert response.status_code == 200
    assert response.json['status'] == "Stock deducted successfully."
