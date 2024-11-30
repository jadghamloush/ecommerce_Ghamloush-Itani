# test_service1.py

import os
import pytest
import sqlite3
import shutil
import json
from service1 import app, create_db_table, connect_to_db

TEST_DB = 'test_customer_database.db'

@pytest.fixture(scope='module')
def test_client():
    # Backup original database if it exists
    if os.path.exists('customer_database.db'):
        shutil.copy('customer_database.db', 'customer_database_backup.db')
        os.remove('customer_database.db')
    
    # Use test database
    def override_connect_to_db():
        conn = sqlite3.connect(TEST_DB)
        return conn
    
    # Override the connect_to_db function in service1
    service1_module = app.import_name
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
    if os.path.exists('customer_database_backup.db'):
        shutil.move('customer_database_backup.db', 'customer_database.db')

def test_add_customer(test_client):
    # Add a new customer
    customer = {
        "full_name": "John Doe",
        "username": "johndoe",
        "password": "password123",
        "age": 30,
        "address": "123 Main St",
        "gender": "Male",
        "marital_status": "Single"
    }
    response = test_client.post('/api/customers/add', json=customer)
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == "johndoe"
    assert data['wallet_balance'] == 0.0

def test_add_duplicate_username(test_client):
    # Attempt to add a customer with the same username
    customer = {
        "full_name": "Jane Smith",
        "username": "johndoe",  # Duplicate username
        "password": "password456",
        "age": 25,
        "address": "456 Elm St",
        "gender": "Female",
        "marital_status": "Married"
    }
    response = test_client.post('/api/customers/add', json=customer)
    assert response.status_code == 200
    data = response.get_json()
    assert data == {}  # Expecting empty due to IntegrityError

def test_get_customers(test_client):
    # Retrieve all customers
    response = test_client.get('/api/customers')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['username'] == "johndoe"

def test_get_customer_by_id(test_client):
    # Retrieve customer by ID
    response = test_client.get('/api/customers/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == "johndoe"

def test_update_customer(test_client):
    # Update existing customer
    updated_customer = {
        "full_name": "John Doe Jr.",
        "username": "johndoe",
        "password": "newpassword123",
        "age": 31,
        "address": "789 Oak St",
        "gender": "Male",
        "marital_status": "Married"
    }
    response = test_client.put('/api/customers/update', json=updated_customer)
    assert response.status_code == 200
    data = response.get_json()
    assert data['full_name'] == "John Doe Jr."
    assert data['age'] == 31
    assert data['address'] == "789 Oak St"
    assert data['marital_status'] == "Married"

def test_delete_customer(test_client):
    # Delete existing customer
    response = test_client.delete('/api/customers/delete/johndoe')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Customer deleted successfully"

def test_get_deleted_customer(test_client):
    # Attempt to retrieve deleted customer
    response = test_client.get('/api/customers/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data == {}  # Customer no longer exists
