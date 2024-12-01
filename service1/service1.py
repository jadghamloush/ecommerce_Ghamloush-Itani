#!/usr/bin/python
"""
Customer Management API using Flask and SQLite.

This module provides a RESTful API for managing customer data, including operations
such as creating, reading, updating, and deleting customer records. It also includes
functions to manage customer wallet balances.

Dependencies:
    - Flask: Web framework for creating the API.
    - Flask-CORS: Handling Cross-Origin Resource Sharing (CORS).
    - sqlite3: Database engine for storing customer data.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import cProfile
import pstats
def connect_to_db():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the 'customer_database.db' SQLite database.
    """
    conn = sqlite3.connect('customer_database.db')
    return conn

def create_db_table():
    """
    Creates the 'customers' table in the SQLite database.

    The table includes fields for customer ID, full name, username, password, age,
    address, gender, marital status, and wallet balance. If the table already exists,
    an error message is printed.

    Returns:
        None
    """
    try:
        conn = connect_to_db()
        conn.execute('''
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY NOT NULL,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                age INTEGER NOT NULL,
                address TEXT NOT NULL,
                gender TEXT NOT NULL,
                marital_status TEXT NOT NULL,
                wallet_balance REAL DEFAULT 0
            );
        ''')
        conn.commit()
        print("Customer table created successfully")
    except sqlite3.OperationalError:
        print("Customer table creation failed - Maybe table already exists")
    finally:
        conn.close()

def insert_customer(customer):
    """
    Inserts a new customer into the 'customers' table.

    Args:
        customer (dict): A dictionary containing customer details with keys:
            - 'full_name' (str): Full name of the customer.
            - 'username' (str): Unique username.
            - 'password' (str): Password for the account.
            - 'age' (int): Age of the customer.
            - 'address' (str): Address of the customer.
            - 'gender' (str): Gender of the customer.
            - 'marital_status' (str): Marital status of the customer.

    Returns:
        dict: The inserted customer data retrieved by ID, or an empty dictionary if insertion fails.
    """
    inserted_customer = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO customers (
                full_name, username, password, age, address, gender, marital_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer['full_name'],
            customer['username'],
            customer['password'],
            customer['age'],
            customer['address'],
            customer['gender'],
            customer['marital_status']
        ))
        conn.commit()
        inserted_customer = get_customer_by_id(cur.lastrowid)
    except sqlite3.IntegrityError:
        conn.rollback()
        print("Error: Username already taken")
    finally:
        conn.close()
    return inserted_customer

def get_customers():
    """
    Retrieves all customers from the 'customers' table.

    Returns:
        list: A list of dictionaries, each representing a customer. Returns an empty list if an error occurs.
    """
    customers = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers")
        rows = cur.fetchall()
        for row in rows:
            customer = dict(row)
            customers.append(customer)
    except sqlite3.Error as e:
        print(f"Error retrieving customers: {e}")
        customers = []
    finally:
        conn.close()
    return customers

def get_customer_by_id(customer_id):
    """
    Retrieves a single customer by their ID.

    Args:
        customer_id (int): The unique ID of the customer.

    Returns:
        dict: A dictionary representing the customer if found, otherwise an empty dictionary.
    """
    customer = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cur.fetchone()
        if row:
            customer = dict(row)
    except sqlite3.Error as e:
        print(f"Error retrieving customer by ID: {e}")
        customer = {}
    finally:
        conn.close()
    return customer

def get_customer_by_username(username):
    """
    Retrieves a single customer by their username.

    Args:
        username (str): The unique username of the customer.

    Returns:
        dict: A dictionary representing the customer if found, otherwise an empty dictionary.
    """
    customer = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            customer = dict(row)
    except sqlite3.Error as e:
        print(f"Error retrieving customer by username: {e}")
        customer = {}
    finally:
        conn.close()
    return customer

def update_customer(customer):
    """
    Updates an existing customer's information based on their username.

    Args:
        customer (dict): A dictionary containing updated customer details with keys:
            - 'full_name' (str): Updated full name.
            - 'password' (str): Updated password.
            - 'age' (int): Updated age.
            - 'address' (str): Updated address.
            - 'gender' (str): Updated gender.
            - 'marital_status' (str): Updated marital status.
            - 'username' (str): Username of the customer to update.

    Returns:
        dict: The updated customer data if successful, otherwise an empty dictionary.
    """
    updated_customer = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE customers
            SET full_name = ?, password = ?, age = ?, address = ?, gender = ?, marital_status = ?
            WHERE username = ?
        """, (
            customer["full_name"],
            customer["password"],
            customer["age"],
            customer["address"],
            customer["gender"],
            customer["marital_status"],
            customer["username"]
        ))
        conn.commit()
        updated_customer = get_customer_by_username(customer["username"])
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error updating customer: {e}")
        updated_customer = {}
    finally:
        conn.close()
    return updated_customer

def delete_customer(username):
    """
    Deletes a customer from the 'customers' table based on their username.

    Args:
        username (str): The unique username of the customer to delete.

    Returns:
        dict: A message indicating the result of the deletion operation.
    """
    message = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE username = ?", (username,))
        if cur.rowcount > 0:
            conn.commit()
            message["status"] = "Customer deleted successfully"
        else:
            message["status"] = "Customer not found"
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error deleting customer: {e}")
        message["status"] = "Cannot delete customer"
    finally:
        conn.close()
    return message

def charge_customer_wallet(username, amount):
    """
    Increases a customer's wallet balance by a specified amount.

    Args:
        username (str): The unique username of the customer.
        amount (float): The amount to add to the wallet balance.

    Returns:
        None
    """
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE customers
            SET wallet_balance = wallet_balance + ?
            WHERE username = ?
        """, (amount, username))
        if cur.rowcount > 0:
            conn.commit()
        else:
            print("Customer not found for wallet charge")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error charging wallet: {e}")
    finally:
        conn.close()

def deduct_from_customer_wallet(username, amount):
    """
    Decreases a customer's wallet balance by a specified amount.

    Args:
        username (str): The unique username of the customer.
        amount (float): The amount to deduct from the wallet balance.

    Returns:
        None
    """
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE customers
            SET wallet_balance = wallet_balance - ?
            WHERE username = ?
        """, (amount, username))
        if cur.rowcount > 0:
            conn.commit()
        else:
            print("Customer not found for wallet deduction")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error deducting from wallet: {e}")
    finally:
        conn.close()

# Initialize Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/customers', methods=['GET'])
def api_get_customers():
    """
    API Endpoint to retrieve all customers.

    Method:
        GET

    URL:
        /api/customers

    Success Response:
        Code: 200
        Content: List of customer dictionaries in JSON format.

    Example:
        GET /api/customers
    """
    return jsonify(get_customers())

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    """
    API Endpoint to retrieve a specific customer by ID.

    Method:
        GET

    URL:
        /api/customers/<customer_id>

    URL Parameters:
        customer_id (int): The unique ID of the customer.

    Success Response:
        Code: 200
        Content: Customer dictionary in JSON format.

    Example:
        GET /api/customers/1
    """
    return jsonify(get_customer_by_id(customer_id))

@app.route('/api/customers/add', methods=['POST'])
def api_add_customer():
    """
    API Endpoint to add a new customer.

    Method:
        POST

    URL:
        /api/customers/add

    Request Body:
        JSON object containing customer details:
            - 'full_name' (str)
            - 'username' (str)
            - 'password' (str)
            - 'age' (int)
            - 'address' (str)
            - 'gender' (str)
            - 'marital_status' (str)

    Success Response:
        Code: 201
        Content: Inserted customer dictionary in JSON format.

    Error Response:
        Code: 400
        Content: Empty dictionary if insertion fails.

    Example:
        POST /api/customers/add
        {
            "full_name": "John Doe",
            "username": "johndoe",
            "password": "securepassword",
            "age": 30,
            "address": "123 Main St",
            "gender": "Male",
            "marital_status": "Single"
        }
    """
    customer = request.get_json()
    inserted_customer = insert_customer(customer)
    if inserted_customer:
        return jsonify(inserted_customer), 200
    else:
        return jsonify({}), 400

@app.route('/api/customers/update', methods=['PUT'])
def api_update_customer():
    """
    API Endpoint to update an existing customer's information.

    Method:
        PUT

    URL:
        /api/customers/update

    Request Body:
        JSON object containing updated customer details:
            - 'full_name' (str)
            - 'username' (str)
            - 'password' (str)
            - 'age' (int)
            - 'address' (str)
            - 'gender' (str)
            - 'marital_status' (str)

    Success Response:
        Code: 200
        Content: Updated customer dictionary in JSON format.

    Error Response:
        Code: 400
        Content: Empty dictionary if update fails.

    Example:
        PUT /api/customers/update
        {
            "full_name": "John Doe Jr.",
            "username": "johndoe",
            "password": "newpassword",
            "age": 31,
            "address": "456 Elm St",
            "gender": "Male",
            "marital_status": "Married"
        }
    """
    customer = request.get_json()
    updated_customer = update_customer(customer)
    if updated_customer:
        return jsonify(updated_customer), 200
    else:
        return jsonify({}), 400

@app.route('/api/customers/delete/<username>', methods=['DELETE'])
def api_delete_customer(username):
    """
    API Endpoint to delete a customer by username.

    Method:
        DELETE

    URL:
        /api/customers/delete/<username>

    URL Parameters:
        username (str): The unique username of the customer to delete.

    Success Response:
        Code: 200
        Content: Message indicating the result of the deletion.

    Example:
        DELETE /api/customers/delete/johndoe
    """
    message = delete_customer(username)
    return jsonify(message), 200

if __name__ == "__main__":
    # Optionally, create the database table if it doesn't exist
    create_db_table()
    app.run(host='0.0.0.0', port=5000, debug=True)
