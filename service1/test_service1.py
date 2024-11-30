import pytest
import os
import sqlite3
from service1 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    # Configure the app for testing
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_customer_database.db'

    # Override the connect_to_db function to use the test database
    def connect_to_db_override():
        conn = sqlite3.connect(app.config['DATABASE'])
        return conn

    # Monkey-patch the connect_to_db function
    import service1
    service1.connect_to_db = connect_to_db_override

    # Create the test database table
    create_db_table()

    with app.test_client() as client:
        yield client

    # Clean up: remove the test database file
    os.remove(app.config['DATABASE'])

def test_add_customer(client):
    # Test adding a new customer
    new_customer = {
        'full_name': 'John Doe',
        'username': 'johndoe',
        'password': 'password123',
        'age': 30,
        'address': '123 Main St',
        'gender': 'Male',
        'marital_status': 'Single'
    }
    response = client.post('/api/customers/add', json=new_customer)
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'johndoe'

def test_get_customers(client):
    # Test retrieving all customers
    response = client.get('/api/customers')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_customer_by_id(client):
    # Add a customer to get by ID
    new_customer = {
        'full_name': 'Jane Smith',
        'username': 'janesmith',
        'password': 'password123',
        'age': 28,
        'address': '456 Elm St',
        'gender': 'Female',
        'marital_status': 'Married'
    }
    add_response = client.post('/api/customers/add', json=new_customer)
    customer_id = add_response.get_json()['customer_id']

    # Test retrieving the customer by ID
    response = client.get(f'/api/customers/{customer_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'janesmith'

def test_update_customer(client):
    # Add a customer to update
    new_customer = {
        'full_name': 'Mike Johnson',
        'username': 'mikejohnson',
        'password': 'password123',
        'age': 35,
        'address': '789 Oak St',
        'gender': 'Male',
        'marital_status': 'Single'
    }
    client.post('/api/customers/add', json=new_customer)

    # Update the customer's information
    updated_customer = {
        'full_name': 'Michael Johnson',
        'username': 'mikejohnson',
        'password': 'newpassword',
        'age': 36,
        'address': '789 Oak St',
        'gender': 'Male',
        'marital_status': 'Married'
    }
    response = client.put('/api/customers/update', json=updated_customer)
    assert response.status_code == 200
    data = response.get_json()
    assert data['full_name'] == 'Michael Johnson'
    assert data['age'] == 36

def test_delete_customer(client):
    # Add a customer to delete
    new_customer = {
        'full_name': 'Emily Davis',
        'username': 'emilydavis',
        'password': 'password123',
        'age': 29,
        'address': '321 Pine St',
        'gender': 'Female',
        'marital_status': 'Single'
    }
    client.post('/api/customers/add', json=new_customer)

    # Delete the customer
    response = client.delete('/api/customers/delete/emilydavis')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Customer deleted successfully'

    # Verify the customer is deleted
    get_response = client.get('/api/customers')
    customers = get_response.get_json()
    usernames = [customer['username'] for customer in customers]
    assert 'emilydavis' not in usernames
