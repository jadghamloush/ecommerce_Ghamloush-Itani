import pytest
import os
import sqlite3
from service2 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_inventory_database.db'

    def connect_to_db_override():
        conn = sqlite3.connect(app.config['DATABASE'])
        return conn

    import service2
    service2.connect_to_db = connect_to_db_override

    create_db_table()

    with app.test_client() as client:
        yield client

    os.remove(app.config['DATABASE'])

def test_add_good(client):
    new_good = {
        'name': 'Laptop',
        'category': 'electronics',
        'price': 999.99,
        'description': 'High-end gaming laptop',
        'stock_count': 10
    }
    response = client.post('/api/goods/add', json=new_good)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Laptop'

def test_get_all_goods(client):
    response = client.get('/api/goods')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_good_by_id(client):
    # Add a good to retrieve
    new_good = {
        'name': 'Smartphone',
        'category': 'electronics',
        'price': 499.99,
        'description': 'Latest model smartphone',
        'stock_count': 20
    }
    add_response = client.post('/api/goods/add', json=new_good)
    good_id = add_response.get_json()['good_id']

    response = client.get(f'/api/goods/{good_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Smartphone'

def test_update_good(client):
    # Add a good to update
    new_good = {
        'name': 'Headphones',
        'category': 'accessories',
        'price': 199.99,
        'description': 'Noise-cancelling headphones',
        'stock_count': 15
    }
    add_response = client.post('/api/goods/add', json=new_good)
    good_id = add_response.get_json()['good_id']

    # Update the good's information
    updated_fields = {
        'price': 149.99,
        'stock_count': 10
    }
    response = client.put(f'/api/goods/update/{good_id}', json=updated_fields)
    assert response.status_code == 200
    data = response.get_json()
    assert data['price'] == 149.99
    assert data['stock_count'] == 10

def test_deduct_good(client):
    # Add a good to deduct stock from
    new_good = {
        'name': 'Tablet',
        'category': 'electronics',
        'price': 299.99,
        'description': '10-inch tablet',
        'stock_count': 5
    }
    add_response = client.post('/api/goods/add', json=new_good)
    good_id = add_response.get_json()['good_id']

    # Deduct stock
    deduct_data = {'quantity': 2}
    response = client.put(f'/api/goods/deduct/{good_id}', json=deduct_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Stock deducted successfully.'

    # Verify stock count
    get_response = client.get(f'/api/goods/{good_id}')
    good_data = get_response.get_json()
    assert good_data['stock_count'] == 3
