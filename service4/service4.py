#!/usr/bin/python
"""
Sales Management API using Flask and SQLite.

This module provides a RESTful API for managing sales transactions in an inventory system.
It includes functionalities such as displaying available goods, retrieving good details,
processing sales, and fetching customer-specific sales records.

Dependencies:
    - Flask: Web framework for creating the API.
    - Flask-CORS: Handling Cross-Origin Resource Sharing (CORS).
    - sqlite3: Database engine for storing sales and goods data.
"""

import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

def connect_to_db():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the 'sales_database.db' SQLite database.
    """
    conn = sqlite3.connect('sales_database.db')
    return conn

def create_db_table():
    """
    Creates the 'sales' table in the SQLite database.

    The table includes fields for sale ID, customer username, good name, sale date, and sale amount.
    If the table already exists, an error message is printed.

    Returns:
        None
    """
    try:
        conn = connect_to_db()
        
        conn.execute('''
            CREATE TABLE sales (
                sale_id INTEGER PRIMARY KEY NOT NULL,
                customer_username TEXT NOT NULL,
                good_name TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                sale_amount REAL NOT NULL
            );
        ''')
        conn.commit()
        print("Sales table created successfully")
    except sqlite3.OperationalError:
        print("Sales table creation failed - Maybe table already exists")
    finally:
        conn.close()

def display_available_goods():
    """
    Retrieves all available goods with stock greater than zero.

    Returns:
        list: A list of dictionaries, each containing the 'name' and 'price_per_item' of a good.
              Returns an empty list if an error occurs.
    """
    goods = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name, price_per_item FROM goods WHERE count_in_stock > 0")
        rows = cur.fetchall()
        for i in rows:
            good = dict(i)
            goods.append(good)
    except sqlite3.Error as e:
        print(f"Error fetching available goods: {e}")
        goods = []
    finally:
        conn.close()
    return goods

def get_good_details(good_name):
    """
    Retrieves detailed information about a specific good by its name.

    Args:
        good_name (str): The name of the good to retrieve details for.

    Returns:
        dict: A dictionary containing all details of the good if found, otherwise an empty dictionary.
    """
    good = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM goods WHERE name = ?", (good_name,))
        row = cur.fetchone()
        if row:
            good = dict(row)
    except sqlite3.Error as e:
        print(f"Error fetching good details for '{good_name}': {e}")
        good = {}
    finally:
        conn.close()
    return good

def make_sale(customer_username, good_name):
    """
    Processes a sale by deducting the item's price from the customer's wallet and decreasing the stock count.

    Args:
        customer_username (str): The username of the customer making the purchase.
        good_name (str): The name of the good being purchased.

    Returns:
        dict: A message indicating the result of the sale operation.
    """
    sale_result = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Check if the customer has enough money in the wallet
        cur.execute("SELECT wallet_balance FROM customers WHERE username = ?", (customer_username,))
        wallet_row = cur.fetchone()
        if not wallet_row:
            sale_result["status"] = "Customer not found."
            return sale_result
        wallet_balance = wallet_row["wallet_balance"]

        # Check if the good exists and has sufficient stock
        cur.execute("SELECT price_per_item, count_in_stock FROM goods WHERE name = ?", (good_name,))
        good_row = cur.fetchone()
        if not good_row:
            sale_result["status"] = "Good not found."
            return sale_result

        price = good_row["price_per_item"]
        stock = good_row["count_in_stock"]

        if wallet_balance >= price and stock > 0:
            # Deduct money from the customer's wallet
            cur.execute("UPDATE customers SET wallet_balance = wallet_balance - ? WHERE username = ?", (price, customer_username))
            # Decrease the count of the purchased good from the database
            cur.execute("UPDATE goods SET count_in_stock = count_in_stock - 1 WHERE name = ?", (good_name,))
            # Record the sale in the sales table
            cur.execute("""
                INSERT INTO sales (customer_username, good_name, sale_date, sale_amount)
                VALUES (?, ?, datetime('now'), ?)
            """, (customer_username, good_name, price))
            conn.commit()
            sale_result["status"] = "Sale successful"
        else:
            sale_result["status"] = "Insufficient funds or item not available for sale"
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error processing sale for '{customer_username}' and '{good_name}': {e}")
        sale_result["status"] = "Sale failed"
    finally:
        conn.close()
    return sale_result

def get_customer_sales(customer_username):
    """
    Retrieves all sales made by a specific customer.

    Args:
        customer_username (str): The username of the customer whose sales records are to be retrieved.

    Returns:
        list: A list of dictionaries, each representing a sale made by the customer.
              Returns an empty list if an error occurs or no sales are found.
    """
    sales = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sales WHERE customer_username = ?", (customer_username,))
        rows = cur.fetchall()
        for i in rows:
            sale = dict(i)
            sales.append(sale)
    except sqlite3.Error as e:
        print(f"Error fetching sales for customer '{customer_username}': {e}")
        sales = []
    finally:
        conn.close()
    return sales

# Initialize Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/display_goods', methods=['GET'])
def api_display_goods():
    """
    API Endpoint to retrieve all available goods with stock greater than zero.

    Method:
        GET

    URL:
        /api/display_goods

    Success Response:
        Code: 200
        Content: List of goods dictionaries in JSON format.

    Example:
        GET /api/display_goods
    """
    return jsonify(display_available_goods()), 200

@app.route('/api/goods_details/<good_name>', methods=['GET'])
def api_get_good_details(good_name):
    """
    API Endpoint to retrieve detailed information about a specific good by its name.

    Method:
        GET

    URL:
        /api/goods_details/<good_name>

    URL Parameters:
        good_name (str): The name of the good to retrieve details for.

    Success Response:
        Code: 200
        Content: Good details dictionary in JSON format.

    Error Response:
        Code: 404
        Content: Error message indicating the good was not found.

    Example:
        GET /api/goods_details/Laptop
    """
    good = get_good_details(good_name)
    if good:
        return jsonify(good), 200
    else:
        return jsonify({"error": "Good not found"}), 404

@app.route('/api/make_sale', methods=['POST'])
def api_make_sale():
    """
    API Endpoint to process a sale transaction.

    Method:
        POST

    URL:
        /api/make_sale

    Request Body:
        JSON object containing sale details:
            - 'customer_username' (str): Username of the customer making the purchase.
            - 'good_name' (str): Name of the good being purchased.

    Success Response:
        Code: 200
        Content: Message indicating the result of the sale operation.

    Error Response:
        Code: 400
        Content: Error message indicating missing fields or invalid data.
        Code: 500
        Content: Error message indicating server-side failure.

    Example:
        POST /api/make_sale
        {
            "customer_username": "johndoe",
            "good_name": "Laptop"
        }
    """
    try:
        sale_data = request.get_json()
        required_fields = ['customer_username', 'good_name']
        for field in required_fields:
            if field not in sale_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        customer_username = sale_data['customer_username']
        good_name = sale_data['good_name']
        sale_result = make_sale(customer_username, good_name)

        if sale_result["status"] == "Sale successful":
            return jsonify(sale_result), 200
        elif sale_result["status"] == "Insufficient funds or item not available for sale":
            return jsonify(sale_result), 400
        elif sale_result["status"] == "Customer not found." or sale_result["status"] == "Good not found.":
            return jsonify(sale_result), 404
        else:
            return jsonify(sale_result), 500
    except Exception as e:
        return jsonify({"error": f"Invalid request: {e}"}), 400

@app.route('/api/customer_sales/<customer_username>', methods=['GET'])
def api_get_customer_sales(customer_username):
    """
    API Endpoint to retrieve all sales made by a specific customer.

    Method:
        GET

    URL:
        /api/customer_sales/<customer_username>

    URL Parameters:
        customer_username (str): The username of the customer whose sales records are to be retrieved.

    Success Response:
        Code: 200
        Content: List of sales dictionaries in JSON format.

    Error Response:
        Code: 404
        Content: Error message indicating the customer was not found or has no sales.

    Example:
        GET /api/customer_sales/johndoe
    """
    sales = get_customer_sales(customer_username)
    if sales:
        return jsonify(sales), 200
    else:
        return jsonify({"error": "No sales found for the customer"}), 404

if __name__ == "__main__":
    create_db_table()
    app.run(debug=True, port=5002)
