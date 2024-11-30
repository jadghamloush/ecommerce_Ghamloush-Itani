# test_service2.py

import os
import pytest
import sqlite3
import shutil
import json
from service2 import app, create_db_table, connect_to_db

TEST_DB = 'test_inventory_database.db'

@pytest.fixture(scope='module')
def test_client():
    # Backup original database if it exists
    if os.path.exists('inventory_database.db'):
        shutil.copy('inventory_database.db', 'inventory_database_backup.db')
        os.remove('inventory_database.db')
    
    # Use test database
    def override_connect_to_db():
        conn = sqlite3.connect(TEST_DB)
        return conn
    
    # Override the connect_to_db function in service2
    service2_module = app.import_name
    app.config['TESTING'] = True
    with app.test_client() as testing_client:
        with app.app_context():
            # Initialize test database
            global connect_to_db
            connect_to_db = override_connect_to_db
            create_db_table()
        yield testing_client
    
    # Teardown: remove test database and restore original
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    if os.path.exists('inventory_database_backup.db'):
        shutil.move('inventory_database_backup.db', 'inventory_database.db')

def test_add_good(test_client):
    # Add a new good
    good = {
        "name": "Laptop",
        "category": "electronics",
        "price": 999.99,
        "description": "A high-performance laptop.",
        "stock_count": 10
    }
    response = test_client.post('/api/goods/add', json=good)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == "Laptop"
    assert data['stock_count'] == 10

def test_add_good_invalid_category(test_client):
    # Attempt to add a good with invalid category
    good = {
        "name": "Mystery Box",
        "category": "unknown",
        "price": 49.99,
        "description": "A box of mystery items.",
        "stock_count": 5
    }
    response = test_client.post('/api/goods/add', json=good)
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Invalid category"

def test_add_good_missing_field(test_client):
    # Attempt to add a good missing required fields
    good = {
        "name": "T-Shirt",
        "price": 19.99,
        # Missing 'category' and 'stock_count'
    }
    response = test_client.post('/api/goods/add', json=good)
    assert response.status_code == 400
    data = response.get_json()
    assert "Missing field" in data['error']

def test_get_all_goods(test_client):
    # Retrieve all goods
    response = test_client.get('/api/goods')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == "Laptop"

def test_get_good_by_id(test_client):
    # Retrieve good by ID
    response = test_client.get('/api/goods/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == "Laptop"

def test_get_good_by_invalid_id(test_client):
    # Attempt to retrieve a non-existent good
    response = test_client.get('/api/goods/999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Good not found"

def test_deduct_good_success(test_client):
    # Deduct stock successfully
    payload = {"quantity": 2}
    response = test_client.put('/api/goods/deduct/1', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Stock deducted successfully."
    
    # Verify stock count
    response = test_client.get('/api/goods/1')
    data = response.get_json()
    assert data['stock_count'] == 8

def test_deduct_good_insufficient_stock(test_client):
    # Attempt to deduct more stock than available
    payload = {"quantity": 20}
    response = test_client.put('/api/goods/deduct/1', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == "Insufficient stock to deduct."

def test_update_good(test_client):
    # Update existing good
    updated_fields = {
        "price": 899.99,
        "stock_count": 15
    }
    response = test_client.put('/api/goods/update/1', json=updated_fields)
    assert response.status_code == 200
    data = response.get_json()
    assert data['price'] == 899.99
    assert data['stock_count'] == 15

def test_update_good_invalid_field(test_client):
    # Attempt to update with invalid category
    updated_fields = {
        "category": "invalid_category"
    }
    response = test_client.put('/api/goods/update/1', json=updated_fields)
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Invalid category"

def test_update_nonexistent_good(test_client):
    # Attempt to update a non-existent good
    updated_fields = {
        "price": 59.99
    }
    response = test_client.put('/api/goods/update/999', json=updated_fields)
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Good not found or failed to update"

def test_add_another_good(test_client):
    # Add another good
    good = {
        "name": "Jeans",
        "category": "clothes",
        "price": 49.99,
        "description": "Comfortable denim jeans.",
        "stock_count": 25
    }
    response = test_client.post('/api/goods/add', json=good)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == "Jeans"
    assert data['stock_count'] == 25

def test_get_all_goods_after_adding(test_client):
    # Retrieve all goods after adding another
    response = test_client.get('/api/goods')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
