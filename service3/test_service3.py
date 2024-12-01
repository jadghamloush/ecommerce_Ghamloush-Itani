import pytest
import os
import sqlite3
from service3 import app, connect_to_db

"""
Test Suite for Sales Management API using pytest.

This module contains unit tests for the Sales Management API implemented in `service3.py`.
It tests various endpoints related to making sales, displaying available goods, retrieving
good details, and fetching customer-specific sales records. A separate test database is used
to ensure that tests do not interfere with the production database.

Dependencies:
    - pytest: Framework for writing and running tests.
    - sqlite3: Database engine for setting up the test database.
    - service3: The module containing the Flask application and related functions to be tested.
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
    app.config['DATABASE'] = 'test_sales_database.db'

    def connect_to_db_override():
        """
        Overrides the default database connection to use the test database.

        Returns:
            sqlite3.Connection: A connection object to the test SQLite database.
        """
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

    # Override the connect_to_db function in service3 with the test database connection
    import service3
    service3.connect_to_db = connect_to_db_override

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

    This function sets up the 'customers', 'goods', and 'sales' tables with appropriate
    schemas to facilitate testing of the Sales Management API.

    Returns:
        None
    """
    conn = sqlite3.connect('test_sales_database.db')
    try:
        # Create 'customers' table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                username TEXT PRIMARY KEY,
                wallet_balance REAL DEFAULT 0
            );
        ''')

        # Create 'goods' table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goods (
                name TEXT PRIMARY KEY,
                price_per_item REAL NOT NULL,
                count_in_stock INTEGER NOT NULL
            );
        ''')

        # Create 'sales' table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_username TEXT NOT NULL,
                good_name TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                sale_amount REAL NOT NULL,
                FOREIGN KEY (customer_username) REFERENCES customers(username),
                FOREIGN KEY (good_name) REFERENCES goods(name)
            );
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables for testing: {e}")
    finally:
        conn.close()


def test_make_sale(client):
    """
    Test the API endpoint for making a sale.

    This test sets up a customer with sufficient wallet balance and a good with available stock.
    It sends a POST request to the `/api/make_sale` endpoint with valid sale data and verifies
    that the sale is processed successfully.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Set up customer and good
    conn = sqlite3.connect('test_sales_database.db')
    try:
        conn.execute("INSERT INTO customers (username, wallet_balance) VALUES (?, ?)", ('testuser', 1000.0))
        conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES (?, ?, ?)",
                     ('TestProduct', 100.0, 5))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting up test data for test_make_sale: {e}")
    finally:
        conn.close()

    sale_data = {
        'customer_username': 'testuser',
        'good_name': 'TestProduct'
    }
    response = client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200, "Expected status code 200 for successful sale."
    data = response.get_json()
    assert data['status'] == 'Sale successful', "Sale should be processed successfully."


def test_display_available_goods(client):
    """
    Test the API endpoint for displaying available goods.

    This test adds a good with available stock to the test database and sends a GET request
    to the `/api/display_goods` endpoint to verify that the good is listed as available.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add goods to display
    conn = sqlite3.connect('test_sales_database.db')
    try:
        conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES (?, ?, ?)",
                     ('AvailableProduct', 50.0, 10))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting up test data for test_display_available_goods: {e}")
    finally:
        conn.close()

    response = client.get('/api/display_goods')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of available goods."
    data = response.get_json()
    assert isinstance(data, list), "Response should be a list of goods."
    assert any(good['name'] == 'AvailableProduct' for good in data), "AvailableProduct should be listed as available."


def test_get_good_details(client):
    """
    Test the API endpoint for retrieving details of a specific good.

    This test adds a good to the test database and sends a GET request to the
    `/api/goods_details/<good_name>` endpoint to verify that the correct details are returned.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a good to retrieve details
    conn = sqlite3.connect('test_sales_database.db')
    try:
        conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES (?, ?, ?)",
                     ('DetailProduct', 75.0, 3))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting up test data for test_get_good_details: {e}")
    finally:
        conn.close()

    response = client.get('/api/goods_details/DetailProduct')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of good details."
    data = response.get_json()
    assert data['name'] == 'DetailProduct', "The good name should match the requested product."


def test_get_customer_sales(client):
    """
    Test the API endpoint for retrieving all sales made by a specific customer.

    This test adds a sale record to the test database and sends a GET request to the
    `/api/customer_sales/<customer_username>` endpoint to verify that the sale is retrieved correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Add a sale record
    conn = sqlite3.connect('test_sales_database.db')
    try:
        conn.execute("""
            INSERT INTO sales (customer_username, good_name, sale_date, sale_amount)
            VALUES (?, ?, ?, ?)
        """, ('testuser', 'TestProduct', '2021-01-01', 100.0))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting up test data for test_get_customer_sales: {e}")
    finally:
        conn.close()

    response = client.get('/api/customer_sales/testuser')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of customer sales."
    data = response.get_json()
    assert isinstance(data, list), "Response should be a list of sales."
    assert data[0]['customer_username'] == 'testuser', "Sale should belong to 'testuser'."
