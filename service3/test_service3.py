import pytest
from service3 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    create_db_table()
    yield client

def test_display_goods(client):
    response = client.get('/api/display_goods')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_make_sale(client):
    response = client.post('/api/make_sale', json={
        "customer_username": "johndoe",
        "good_name": "Laptop"
    })
    assert response.status_code == 200
    assert response.json['status'] == "Sale successful"

def test_customer_sales(client):
    response = client.get('/api/customer_sales/johndoe')
    assert response.status_code == 200
    assert isinstance(response.json, list)
