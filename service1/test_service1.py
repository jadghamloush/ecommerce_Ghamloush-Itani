import pytest
from service1 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    create_db_table()  # Ensure the table exists
    yield client

def test_add_customer(client):
    response = client.post('/api/customers/add', json={
        "full_name": "John Doe",
        "username": "johndoe",
        "password": "password123",
        "age": 30,
        "address": "123 Main St",
        "gender": "Male",
        "marital_status": "Single"
    })
    assert response.status_code == 200
    assert response.json['username'] == "johndoe"

def test_get_customer(client):
    response = client.get('/api/customers/1')
    assert response.status_code == 200
    assert response.json['full_name'] == "John Doe"

def test_update_customer(client):
    response = client.put('/api/customers/update', json={
        "username": "johndoe",
        "full_name": "John Smith",
        "password": "newpassword123",
        "age": 31,
        "address": "456 Elm St",
        "gender": "Male",
        "marital_status": "Married"
    })
    assert response.status_code == 200
    assert response.json['full_name'] == "John Smith"

def test_delete_customer(client):
    response = client.delete('/api/customers/delete/johndoe')
    assert response.status_code == 200
    assert response.json['status'] == "Customer deleted successfully"
