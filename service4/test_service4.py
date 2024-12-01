import pytest
import os
import sqlite3
from service4 import app, create_db_table, connect_to_db

"""
Test Suite for Reviews Management API using pytest.

This module contains unit tests for the Reviews Management API implemented in `service4.py`.
It tests various endpoints related to adding, retrieving, updating, deleting, and moderating reviews.
A separate test database is used to ensure that tests do not interfere with the production database.

Dependencies:
    - pytest: Framework for writing and running tests.
    - sqlite3: Database engine for setting up the test database.
    - service4: The module containing the Flask application and related functions to be tested.
"""

@pytest.fixture
def client():
    """
    Pytest fixture to set up a test client and initialize a test database.

    This fixture configures the Flask application for testing, overrides the database connection
    to use a test-specific database, creates the necessary database tables, and provides a test client
    for making API requests. After the tests are completed, it cleans up by removing the test database file.

    Yields:
        FlaskClient: A test client for the Flask application.
    """
    # Configure the Flask application for testing
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_reviews_database.db'

    def connect_to_db_override():
        """
        Overrides the default database connection to use the test database.

        Returns:
            sqlite3.Connection: A connection object to the test SQLite database.
        """
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

    # Override the connect_to_db function in service4 with the test database connection
    import service4
    service4.connect_to_db = connect_to_db_override

    # Create the necessary database tables in the test database
    create_db_table()

    # Provide the test client to the tests
    with app.test_client() as client:
        yield client

    # Clean up by removing the test database file after tests are done
    os.remove(app.config['DATABASE'])


def test_add_review(client):
    """
    Test the API endpoint for adding a new review.

    This test sends a POST request to the `/api/reviews` endpoint with valid review data
    and verifies that the review is added successfully.

    Args:
        client (FlaskClient): The test client fixture.
    """
    new_review = {
        'product_name': 'ProductX',
        'customer_username': 'user1',
        'rating': 5,
        'comment': 'Great product!'
    }
    response = client.post('/api/reviews', json=new_review)
    assert response.status_code == 200, "Expected status code 200 for successful review addition."
    data = response.get_json()
    assert data['status'] == 'Review added successfully', "Review should be added successfully."


def test_get_product_reviews(client):
    """
    Test the API endpoint for retrieving all reviews of a specific product.

    This test inserts a review directly into the test database and then sends a GET request
    to the `/api/reviews/product/<product_name>` endpoint to verify that the review is retrieved correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a review to retrieve
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute(
        "INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES (?, ?, ?, ?)",
        ('ProductY', 'user2', 4, 'Good product')
    )
    conn.commit()
    conn.close()

    # Retrieve the reviews for ProductY
    response = client.get('/api/reviews/product/ProductY')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of product reviews."
    data = response.get_json()
    assert isinstance(data, list), "Response should be a list of reviews."
    assert any(review['product_name'] == 'ProductY' for review in data), "Review for 'ProductY' should be present."


def test_update_review(client):
    """
    Test the API endpoint for updating an existing review.

    This test inserts a review directly into the test database, updates it via a PUT request,
    and verifies that the update is successful.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a review to update
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute(
        "INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES (?, ?, ?, ?)",
        ('ProductZ', 'user3', 3, 'Average')
    )
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # Update the review
    updated_review = {
        'rating': 4,
        'comment': 'Above average'
    }
    response = client.put(f'/api/reviews/{review_id}', json=updated_review)
    assert response.status_code == 200, "Expected status code 200 for successful review update."
    data = response.get_json()
    assert data['status'] == 'Review updated successfully', "Review should be updated successfully."


def test_delete_review(client):
    """
    Test the API endpoint for deleting a review.

    This test inserts a review directly into the test database, deletes it via a DELETE request,
    and verifies that the deletion is successful.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a review to delete
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute(
        "INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES (?, ?, ?, ?)",
        ('ProductA', 'user4', 2, 'Not great')
    )
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # Delete the review
    response = client.delete(f'/api/reviews/{review_id}')
    assert response.status_code == 200, "Expected status code 200 for successful review deletion."
    data = response.get_json()
    assert data['status'] == 'Review deleted successfully', "Review should be deleted successfully."


def test_moderate_review(client):
    """
    Test the API endpoint for moderating a review.

    This test inserts a review directly into the test database, moderates it via a POST request,
    and verifies that the moderation status is updated correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a review to moderate
    conn = sqlite3.connect('test_reviews_database.db')
    conn.execute(
        "INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES (?, ?, ?, ?)",
        ('ProductB', 'user5', 1, 'Bad product')
    )
    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # Moderate the review by approving it
    response = client.post(f'/api/reviews/moderate/{review_id}', json={'action': 'approve'})
    assert response.status_code == 200, "Expected status code 200 for successful review moderation."
    data = response.get_json()
    assert data['status'] == 'Review moderated successfully', "Review should be moderated successfully."

    # Verify moderation status in the database
    conn = sqlite3.connect('test_reviews_database.db')
    cur = conn.cursor()
    cur.execute("SELECT moderated FROM reviews WHERE review_id = ?", (review_id,))
    moderated_status = cur.fetchone()[0]
    conn.close()
    assert moderated_status == 1, "Review should be marked as moderated (approved)."
