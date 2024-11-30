import pytest
from service4 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    create_db_table()
    yield client

def test_add_review(client):
    response = client.post('/api/reviews', json={
        "product_name": "Laptop",
        "customer_username": "johndoe",
        "rating": 5,
        "comment": "Great product!"
    })
    assert response.status_code == 200
    assert response.json['status'] == "Review added successfully"

def test_get_product_reviews(client):
    response = client.get('/api/reviews/product/Laptop')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_update_review(client):
    response = client.put('/api/reviews/1', json={
        "rating": 4,
        "comment": "Good product but expensive"
    })
    assert response.status_code == 200
    assert response.json['status'] == "Review updated successfully"

def test_delete_review(client):
    response = client.delete('/api/reviews/1')
    assert response.status_code == 200
    assert response.json['status'] == "Review deleted successfully"
