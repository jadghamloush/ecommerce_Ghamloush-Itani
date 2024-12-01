import pytest
import os
import sqlite3
from service2 import app, create_db_table, connect_to_db

"""
Test Suite for Inventory Management API using pytest.

This module contains unit tests for the Inventory Management API implemented in `service2.py`.
It tests various endpoints related to adding goods, retrieving all goods, fetching good details,
updating goods, and deducting stock from goods. A separate test database is used to ensure that
tests do not interfere with the production database.

Dependencies:
    - pytest: Framework for writing and running tests.
    - sqlite3: Database engine for setting up the test database.
    - service2: The module containing the Flask application and related functions to be tested.
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
    app.config['DATABASE'] = 'test_inventory_database.db'

    def connect_to_db_override():
        """
        Overrides the default database connection to use the test database.

        Returns:
            sqlite3.Connection: A connection object to the test SQLite database.
        """
        conn = sqlite3.connect(app.config['DATABASE'])
        return conn

    # Override the connect_to_db function in service2 with the test database connection
    import service2
    service2.connect_to_db = connect_to_db_override

    # Create the necessary database tables in the test database
    create_tables_for_test()

    # Provide the test client to the tests
    with app.test_client() as client:
        yield client

    # Clean up by removing the test database file after tests are done
    os.remove(app.config['DATABASE'])


def create_tables_for_test():
    """
    Creates necessary tables in the test SQLite database for testing purposes.

    This function sets up the 'goods' table with appropriate schema to facilitate testing
    of the Inventory Management API.

    Returns:
        None
    """
    conn = sqlite3.connect('test_inventory_database.db')
    try:
        # Create 'goods' table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goods (
                good_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name TEXT NOT NULL,
                category TEXT CHECK( category IN ('food', 'clothes', 'accessories', 'electronics') ) NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                stock_count INTEGER NOT NULL CHECK(stock_count >= 0)
            );
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables for testing: {e}")
    finally:
        conn.close()


def test_add_good(client):
    """
    Test the API endpoint for adding a new good.

    This test sends a POST request to the `/api/goods/add` endpoint with valid good data
    and verifies that the good is added successfully by checking the response status code
    and the returned good's name.

    Args:
        client (FlaskClient): The test client fixture.
    """
    new_good = {
        'name': 'Laptop',
        'category': 'electronics',
        'price': 999.99,
        'description': 'High-end gaming laptop',
        'stock_count': 10
    }
    response = client.post('/api/goods/add', json=new_good)
    assert response.status_code == 201, "Expected status code 201 for successful good addition."
    data = response.get_json()
    assert data['name'] == 'Laptop', "The good name should be 'Laptop'."


def test_get_all_goods(client):
    """
    Test the API endpoint for retrieving all goods.

    This test sends a GET request to the `/api/goods` endpoint and verifies that the response
    status code is 200 and that the returned data is a list.

    Args:
        client (FlaskClient): The test client fixture.
    """
    response = client.get('/api/goods')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of all goods."
    data = response.get_json()
    assert isinstance(data, list), "Response should be a list of goods."


def test_get_good_by_id(client):
    """
    Test the API endpoint for retrieving a specific good by its ID.

    This test adds a good to the test database, retrieves it via a GET request to the `/api/goods/<good_id>` endpoint,
    and verifies that the retrieved good's name matches the expected value.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a good to retrieve
    new_good = {
        'name': 'Smartphone',
        'category': 'electronics',
        'price': 499.99,
        'description': 'Latest model smartphone',
        'stock_count': 20
    }
    add_response = client.post('/api/goods/add', json=new_good)
    assert add_response.status_code == 201, "Expected status code 201 for successful good addition."
    good_id = add_response.get_json().get('good_id')
    assert good_id is not None, "Good ID should be present in the response."

    # Retrieve the good by ID
    response = client.get(f'/api/goods/{good_id}')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of the good."
    data = response.get_json()
    assert data['name'] == 'Smartphone', "The good name should be 'Smartphone'."


def test_update_good(client):
    """
    Test the API endpoint for updating an existing good.

    This test adds a good to the test database, updates its price and stock count via a PUT request
    to the `/api/goods/update/<good_id>` endpoint, and verifies that the updates are reflected correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a good to update
    new_good = {
        'name': 'Headphones',
        'category': 'accessories',
        'price': 199.99,
        'description': 'Noise-cancelling headphones',
        'stock_count': 15
    }
    add_response = client.post('/api/goods/add', json=new_good)
    assert add_response.status_code == 201, "Expected status code 201 for successful good addition."
    good_id = add_response.get_json().get('good_id')
    assert good_id is not None, "Good ID should be present in the response."

    # Update the good's information
    updated_fields = {
        'price': 149.99,
        'stock_count': 10
    }
    response = client.put(f'/api/goods/update/{good_id}', json=updated_fields)
    assert response.status_code == 200, "Expected status code 200 for successful good update."
    data = response.get_json()
    assert data['price'] == 149.99, "Good price should be updated to 149.99."
    assert data['stock_count'] == 10, "Good stock count should be updated to 10."


def test_deduct_good(client):
    """
    Test the API endpoint for deducting stock from a good.

    This test adds a good with a specific stock count to the test database, deducts a quantity via a PUT request
    to the `/api/goods/deduct/<good_id>` endpoint, and verifies that the stock count is updated correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a good to deduct stock from
    new_good = {
        'name': 'Tablet',
        'category': 'electronics',
        'price': 299.99,
        'description': '10-inch tablet',
        'stock_count': 5
    }
    add_response = client.post('/api/goods/add', json=new_good)
    assert add_response.status_code == 201, "Expected status code 201 for successful good addition."
    good_id = add_response.get_json().get('good_id')
    assert good_id is not None, "Good ID should be present in the response."

    # Deduct stock
    deduct_data = {'quantity': 2}
    response = client.put(f'/api/goods/deduct/{good_id}', json=deduct_data)
    assert response.status_code == 200, "Expected status code 200 for successful stock deduction."
    data = response.get_json()
    assert data['status'] == 'Stock deducted successfully.', "Stock should be deducted successfully."

    # Verify stock count
    get_response = client.get(f'/api/goods/{good_id}')
    assert get_response.status_code == 200, "Expected status code 200 for successful retrieval of the good."
    good_data = get_response.get_json()
    assert good_data['stock_count'] == 3, "Good stock count should be reduced to 3."
