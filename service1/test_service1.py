import pytest
import os
import sqlite3
from service1 import app, create_db_table, connect_to_db

"""
Test Suite for Customer Management API using pytest.

This module contains unit tests for the Customer Management API implemented in `service1.py`.
It tests various endpoints related to adding, retrieving, updating, and deleting customer records.
A separate test database is used to ensure that tests do not interfere with the production database.

Dependencies:
    - pytest: Framework for writing and running tests.
    - sqlite3: Database engine for setting up the test database.
    - service1: The module containing the Flask application and related functions to be tested.
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
    app.config['DATABASE'] = 'test_customer_database.db'

    def connect_to_db_override():
        """
        Overrides the default database connection to use the test database.

        Returns:
            sqlite3.Connection: A connection object to the test SQLite database.
        """
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

    # Override the connect_to_db function in service1 with the test database connection
    import service1
    service1.connect_to_db = connect_to_db_override

    # Create the necessary database tables in the test database
    create_db_table()

    # Provide the test client to the tests
    with app.test_client() as client:
        yield client

    # Clean up by removing the test database file after tests are done
    os.remove(app.config['DATABASE'])


def test_add_customer(client):
    """
    Test the API endpoint for adding a new customer.

    This test sends a POST request to the `/api/customers/add` endpoint with valid customer data
    and verifies that the customer is added successfully by checking the response status code
    and the returned customer's username.

    Args:
        client (FlaskClient): The test client fixture.
    """
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
    assert response.status_code == 200, "Expected status code 200 for successful customer addition."
    data = response.get_json()
    assert data['username'] == 'johndoe', "Returned username should be 'johndoe'."


def test_get_customers(client):
    """
    Test the API endpoint for retrieving all customers.

    This test sends a GET request to the `/api/customers` endpoint and verifies that the response
    status code is 200 and that the returned data is a list.

    Args:
        client (FlaskClient): The test client fixture.
    """
    # Test retrieving all customers
    response = client.get('/api/customers')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of customers."
    data = response.get_json()
    assert isinstance(data, list), "Response should be a list of customers."


def test_get_customer_by_id(client):
    """
    Test the API endpoint for retrieving a specific customer by their ID.

    This test adds a customer to the test database, retrieves it via a GET request to the `/api/customers/<customer_id>` endpoint,
    and verifies that the retrieved customer's username matches the expected value.

    Args:
        client (FlaskClient): The test client fixture.
    """
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
    assert add_response.status_code == 200, "Expected status code 200 for successful customer addition."
    data = add_response.get_json()
    customer_id = data.get('customer_id')
    assert customer_id is not None, "Customer ID should be present in the response."

    # Test retrieving the customer by ID
    response = client.get(f'/api/customers/{customer_id}')
    assert response.status_code == 200, "Expected status code 200 for successful retrieval of the customer."
    data = response.get_json()
    assert data['username'] == 'janesmith', "Retrieved username should be 'janesmith'."


def test_update_customer(client):
    """
    Test the API endpoint for updating an existing customer's information.

    This test adds a customer to the test database, updates the customer's information via a PUT request
    to the `/api/customers/update` endpoint, and verifies that the updates are reflected correctly.

    Args:
        client (FlaskClient): The test client fixture.
    """
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
    add_response = client.post('/api/customers/add', json=new_customer)
    assert add_response.status_code == 200, "Expected status code 200 for successful customer addition."

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
    assert response.status_code == 200, "Expected status code 200 for successful customer update."
    data = response.get_json()
    assert data['full_name'] == 'Michael Johnson', "Customer full name should be updated to 'Michael Johnson'."
    assert data['age'] == 36, "Customer age should be updated to 36."


def test_delete_customer(client):
    """
    Test the API endpoint for deleting a customer.

    This test adds a customer to the test database, deletes the customer via a DELETE request
    to the `/api/customers/delete/<username>` endpoint, and verifies that the deletion is successful.

    Args:
        client (FlaskClient): The test client fixture.
    """
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
    add_response = client.post('/api/customers/add', json=new_customer)
    assert add_response.status_code == 200, "Expected status code 200 for successful customer addition."

    # Delete the customer
    response = client.delete('/api/customers/delete/emilydavis')
    assert response.status_code == 200, "Expected status code 200 for successful customer deletion."
    data = response.get_json()
    assert data['status'] == 'Customer deleted successfully', "Deletion status should indicate success."

    # Verify the customer is deleted
    get_response = client.get('/api/customers')
    assert get_response.status_code == 200, "Expected status code 200 for successful retrieval of customers."
    customers = get_response.get_json()
    usernames = [customer['username'] for customer in customers]
    assert 'emilydavis' not in usernames, "Deleted customer 'emilydavis' should not be present in the customers list."
