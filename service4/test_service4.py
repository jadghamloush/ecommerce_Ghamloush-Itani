import pytest
import os
import sqlite3
from service4 import app, create_db_table, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_reviews_database.db'

    def connect_to_db_override():
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

    import service4
    service4.connect_to_db = connect_to_db_override

    create_db_table()

    with app.test_client() as client:
        yield client

    os.remove(app.config['DATABASE'])

def test_add_review(client):
    new_review = {
        'product_name': 'ProductX',
        'customer_username': 'user1',
        'rating': 5,
        'comment': 'Great product!'
    }
    response = client.post('/api/reviews', json=new_review)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Review added successfully'

def test_get_product_reviews(client):
    # Add a review to retrieve
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute("INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES ('ProductY', 'user2', 4, 'Good product')")
    conn.commit()
    conn.close()

    response = client.get('/api/reviews/product/ProductY')
    assert response.status_code == 200
    data = response.get_json()
    assert any(review['product_name'] == 'ProductY' for review in data)

def test_update_review(client):
    # Add a review to update
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute("INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES ('ProductZ', 'user3', 3, 'Average')")
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    updated_review = {
        'rating': 4,
        'comment': 'Above average'
    }
    response = client.put(f'/api/reviews/{review_id}', json=updated_review)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Review updated successfully'

def test_delete_review(client):
    # Add a review to delete
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute("INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES ('ProductA', 'user4', 2, 'Not great')")
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    response = client.delete(f'/api/reviews/{review_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Review deleted successfully'

def test_moderate_review(client):
    # Add a review to moderate
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute("INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES ('ProductB', 'user5', 1, 'Bad product')")
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    response = client.post(f'/api/reviews/moderate/{review_id}', json={'action': 'approve'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Review moderated successfully'

    # Verify moderation
    conn = sqlite3.connect('test_reviews_database.db')
    cur = conn.cursor()
    cur.execute("SELECT moderated FROM reviews WHERE review_id = ?", (review_id,))
    moderated_status = cur.fetchone()[0]
    conn.close()
    assert moderated_status == 1
