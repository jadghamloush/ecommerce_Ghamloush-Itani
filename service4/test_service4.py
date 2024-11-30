# test_service4.py

import os
import pytest
import sqlite3
import shutil
import json
from service4 import app, create_db_table, connect_to_db

TEST_DB = 'test_reviews_database.db'

@pytest.fixture(scope='module')
def test_client():
    # Backup original database if it exists
    if os.path.exists('reviews_database.db'):
        shutil.copy('reviews_database.db', 'reviews_database_backup.db')
        os.remove('reviews_database.db')
    
    # Use test database
    def override_connect_to_db():
        conn = sqlite3.connect(TEST_DB)
        return conn
    
    # Override the connect_to_db function in service4
    app.config['TESTING'] = True
    with app.test_client() as testing_client:
        with app.app_context():
            global connect_to_db
            connect_to_db = override_connect_to_db
            create_db_table()
        yield testing_client
    
    # Teardown: remove test database and restore original
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    if os.path.exists('reviews_database_backup.db'):
        shutil.move('reviews_database_backup.db', 'reviews_database.db')

def test_add_review(test_client):
    # Add a new review
    review = {
        "product_name": "Laptop",
        "customer_username": "john_doe",
        "rating": 5,
        "comment": "Excellent product!"
    }
    response = test_client.post('/api/reviews', json=review)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review added successfully"

def test_add_review_invalid_rating(test_client):
    # Attempt to add a review with invalid rating
    review = {
        "product_name": "Laptop",
        "customer_username": "jane_doe",
        "rating": 6,  # Invalid rating
        "comment": "Too good!"
    }
    response = test_client.post('/api/reviews', json=review)
    assert response.status_code == 200
    data = response.get_json()
    assert "Error" in data['status']

def test_get_product_reviews(test_client):
    # Retrieve reviews for a product
    response = test_client.get('/api/reviews/product/Laptop')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['product_name'] == "Laptop"
    assert data[0]['rating'] == 5

def test_update_review(test_client):
    # Update an existing review
    updated_review = {
        "rating": 4,
        "comment": "Good product."
    }
    response = test_client.put('/api/reviews/1', json=updated_review)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review updated successfully"
    
    # Verify the update
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT rating, comment FROM reviews WHERE review_id = 1")
    review = cur.fetchone()
    assert review['rating'] == 4
    assert review['comment'] == "Good product."
    conn.close()

def test_update_nonexistent_review(test_client):
    # Attempt to update a non-existent review
    updated_review = {
        "rating": 3,
        "comment": "Average product."
    }
    response = test_client.put('/api/reviews/999', json=updated_review)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Error: ..."

def test_delete_review(test_client):
    # Delete an existing review
    response = test_client.delete('/api/reviews/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review deleted successfully"
    
    # Verify deletion
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM reviews WHERE review_id = 1")
    review = cur.fetchone()
    assert review is None
    conn.close()

def test_delete_nonexistent_review(test_client):
    # Attempt to delete a non-existent review
    response = test_client.delete('/api/reviews/999')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Error: ..."  # Depending on implementation

def test_moderate_review_approve(test_client):
    # Add a review to moderate
    review = {
        "product_name": "Smartphone",
        "customer_username": "alice",
        "rating": 4,
        "comment": "Pretty good phone."
    }
    response = test_client.post('/api/reviews', json=review)
    assert response.status_code == 200
    
    # Approve the review
    response = test_client.post('/api/reviews/moderate/2', json={"action": "approve"})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review moderated successfully"
    
    # Verify moderation
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT moderated FROM reviews WHERE review_id = 2")
    review = cur.fetchone()
    assert review['moderated'] == 1
    conn.close()

def test_moderate_review_reject(test_client):
    # Add another review to moderate
    review = {
        "product_name": "Headphones",
        "customer_username": "bob",
        "rating": 2,
        "comment": "Not satisfied."
    }
    response = test_client.post('/api/reviews', json=review)
    assert response.status_code == 200
    
    # Reject the review
    response = test_client.post('/api/reviews/moderate/3', json={"action": "reject"})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review moderated successfully"
    
    # Verify moderation
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT moderated FROM reviews WHERE review_id = 3")
    review = cur.fetchone()
    assert review['moderated'] == 0
    conn.close()

def test_get_customer_reviews(test_client):
    # Retrieve reviews by a customer
    response = test_client.get('/api/reviews/customer/alice')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['customer_username'] == "alice"

def test_get_review_details(test_client):
    # Get details of a specific review
    response = test_client.get('/api/reviews/details/2')
    assert response.status_code == 200
    data = response.get_json()
    assert data['product_name'] == "Smartphone"
    assert data['rating'] == 4
    assert data['moderated'] == 1

def test_get_review_details_nonexistent(test_client):
    # Attempt to get details of a non-existent review
    response = test_client.get('/api/reviews/details/999')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Review not found"
