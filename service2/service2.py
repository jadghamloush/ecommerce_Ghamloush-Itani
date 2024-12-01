#!/usr/bin/python3
"""
Inventory Management API using Flask and SQLite.

This module provides a RESTful API for managing goods in an inventory system,
including operations such as adding, retrieving, updating, and deducting stock
for goods. It ensures data integrity through validation and handles various
error scenarios gracefully.

Dependencies:
    - Flask: Web framework for creating the API.
    - Flask-CORS: Handling Cross-Origin Resource Sharing (CORS).
    - sqlite3: Database engine for storing inventory data.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DATABASE = 'inventory_database.db'


def connect_to_db():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the specified SQLite database.
    """
    conn = sqlite3.connect(DATABASE)
    return conn


def create_db_table():
    """
    Creates the 'goods' table in the SQLite database if it does not already exist.

    The table includes fields for good ID, name, category, price, description, and stock count.
    Constraints are applied to ensure data integrity, such as valid categories and non-negative stock counts.

    Returns:
        None
    """
    try:
        conn = connect_to_db()
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
        print("Goods table created successfully or already exists.")
    except Exception as e:
        print(f"Error creating goods table: {e}")
    finally:
        conn.close()


def add_good(good):
    """
    Adds a new good to the 'goods' table.

    Args:
        good (dict): A dictionary containing good details with keys:
            - 'name' (str): Name of the good.
            - 'category' (str): Category of the good. Must be one of ['food', 'clothes', 'accessories', 'electronics'].
            - 'price' (float): Price of the good. Must be non-negative.
            - 'description' (str, optional): Description of the good.
            - 'stock_count' (int): Initial stock count. Must be non-negative.

    Returns:
        dict: The newly added good's data retrieved by ID, or an empty dictionary if addition fails.
    """
    new_good = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO goods (name, category, price, description, stock_count)
            VALUES (?, ?, ?, ?, ?)
        """, (good['name'], good['category'], good['price'], good.get('description', ''), good['stock_count']))
        conn.commit()
        new_good = get_good_by_id(cur.lastrowid)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Integrity Error: {e}")
    except Exception as e:
        conn.rollback()
        print(f"Error adding good: {e}")
    finally:
        conn.close()
    return new_good


def deduct_good(good_id, quantity):
    """
    Deducts a specified quantity from a good's stock count.

    Args:
        good_id (int): The unique ID of the good.
        quantity (int): The quantity to deduct. Must be a positive integer.

    Returns:
        dict: A message indicating the result of the deduction operation.
    """
    message = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        # Check current stock
        cur.execute("SELECT stock_count FROM goods WHERE good_id = ?", (good_id,))
        row = cur.fetchone()
        if row:
            current_stock = row[0]
            if current_stock >= quantity:
                cur.execute("""
                    UPDATE goods
                    SET stock_count = stock_count - ?
                    WHERE good_id = ?
                """, (quantity, good_id))
                conn.commit()
                message["status"] = "Stock deducted successfully."
            else:
                message["status"] = "Insufficient stock to deduct."
        else:
            message["status"] = "Good not found."
    except Exception as e:
        conn.rollback()
        message["status"] = f"Error deducting stock: {e}"
    finally:
        conn.close()
    return message


def update_good(good_id, updated_fields):
    """
    Updates the details of an existing good based on provided fields.

    Args:
        good_id (int): The unique ID of the good to update.
        updated_fields (dict): A dictionary containing fields to update with their new values.
            Valid keys include 'name', 'category', 'price', 'description', and 'stock_count'.

    Returns:
        dict: The updated good's data if successful, otherwise an empty dictionary.
    """
    updated_good = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()

        # Build the update query dynamically based on provided fields
        fields = []
        values = []
        for key, value in updated_fields.items():
            if key in ['name', 'category', 'price', 'description', 'stock_count']:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            print("No valid fields provided for update.")
            return {}

        values.append(good_id)
        set_clause = ", ".join(fields)
        query = f"UPDATE goods SET {set_clause} WHERE good_id = ?"
        cur.execute(query, tuple(values))
        conn.commit()
        updated_good = get_good_by_id(good_id)
    except Exception as e:
        conn.rollback()
        print(f"Error updating good: {e}")
    finally:
        conn.close()
    return updated_good


def get_all_goods():
    """
    Retrieves all goods from the 'goods' table.

    Returns:
        list: A list of dictionaries, each representing a good. Returns an empty list if an error occurs.
    """
    goods = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM goods")
        rows = cur.fetchall()
        for row in rows:
            goods.append(dict(row))
    except Exception as e:
        print(f"Error fetching goods: {e}")
    finally:
        conn.close()
    return goods


def get_good_by_id(good_id):
    """
    Retrieves a single good by its ID.

    Args:
        good_id (int): The unique ID of the good.

    Returns:
        dict: A dictionary representing the good if found, otherwise an empty dictionary.
    """
    good = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM goods WHERE good_id = ?", (good_id,))
        row = cur.fetchone()
        if row:
            good = dict(row)
    except Exception as e:
        print(f"Error fetching good by ID: {e}")
    finally:
        conn.close()
    return good


@app.route('/api/goods', methods=['GET'])
def api_get_goods():
    """
    API Endpoint to retrieve all goods.

    Method:
        GET

    URL:
        /api/goods

    Success Response:
        Code: 200
        Content: List of goods dictionaries in JSON format.

    Example:
        GET /api/goods
    """
    return jsonify(get_all_goods()), 200


@app.route('/api/goods/<int:good_id>', methods=['GET'])
def api_get_good(good_id):
    """
    API Endpoint to retrieve a specific good by ID.

    Method:
        GET

    URL:
        /api/goods/<good_id>

    URL Parameters:
        good_id (int): The unique ID of the good.

    Success Response:
        Code: 200
        Content: Good dictionary in JSON format.

    Error Response:
        Code: 404
        Content: Error message indicating the good was not found.

    Example:
        GET /api/goods/1
    """
    good = get_good_by_id(good_id)
    if good:
        return jsonify(good), 200
    else:
        return jsonify({"error": "Good not found"}), 404


@app.route('/api/goods/add', methods=['POST'])
def api_add_good():
    """
    API Endpoint to add a new good to the inventory.

    Method:
        POST

    URL:
        /api/goods/add

    Request Body:
        JSON object containing good details:
            - 'name' (str): Name of the good.
            - 'category' (str): Category of the good. Must be one of ['food', 'clothes', 'accessories', 'electronics'].
            - 'price' (float): Price of the good. Must be non-negative.
            - 'description' (str, optional): Description of the good.
            - 'stock_count' (int): Initial stock count. Must be non-negative.

    Success Response:
        Code: 201
        Content: Newly added good dictionary in JSON format.

    Error Responses:
        Code: 400
            - Missing required fields.
            - Invalid category, stock_count, or price.
        Code: 500
            - Failed to add good due to server error.

    Example:
        POST /api/goods/add
        {
            "name": "Laptop",
            "category": "electronics",
            "price": 999.99,
            "description": "High-performance laptop",
            "stock_count": 50
        }
    """
    try:
        good = request.get_json()
        required_fields = ['name', 'category', 'price', 'stock_count']
        for field in required_fields:
            if field not in good:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Validate category
        if good['category'] not in ['food', 'clothes', 'accessories', 'electronics']:
            return jsonify({"error": "Invalid category"}), 400

        # Validate stock_count
        if not isinstance(good['stock_count'], int) or good['stock_count'] < 0:
            return jsonify({"error": "Invalid stock_count"}), 400

        # Validate price
        if not isinstance(good['price'], (int, float)) or good['price'] < 0:
            return jsonify({"error": "Invalid price"}), 400

        new_good = add_good(good)
        if new_good:
            return jsonify(new_good), 201
        else:
            return jsonify({"error": "Failed to add good"}), 500
    except Exception as e:
        return jsonify({"error": f"Invalid request: {e}"}), 400


@app.route('/api/goods/deduct/<int:good_id>', methods=['PUT'])
def api_deduct_good(good_id):
    """
    API Endpoint to deduct a quantity from a good's stock count.

    Method:
        PUT

    URL:
        /api/goods/deduct/<good_id>

    URL Parameters:
        good_id (int): The unique ID of the good.

    Request Body:
        JSON object containing:
            - 'quantity' (int): The quantity to deduct. Must be a positive integer.

    Success Responses:
        Code: 200
            - Stock deducted successfully.
        Code: 400
            - Missing 'quantity' field.
            - Invalid 'quantity' value.
            - Insufficient stock to deduct.
        Code: 404
            - Good not found.

    Error Response:
        Code: 500
            - Server error during deduction.

    Example:
        PUT /api/goods/deduct/1
        {
            "quantity": 5
        }
    """
    try:
        data = request.get_json()
        if 'quantity' not in data:
            return jsonify({"error": "Missing field: quantity"}), 400
        quantity = data['quantity']
        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({"error": "Invalid quantity"}), 400

        result = deduct_good(good_id, quantity)
        if result["status"] == "Stock deducted successfully.":
            return jsonify(result), 200
        elif result["status"] == "Insufficient stock to deduct.":
            return jsonify(result), 400
        elif result["status"] == "Good not found.":
            return jsonify(result), 404
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"error": f"Invalid request: {e}"}), 400


@app.route('/api/goods/update/<int:good_id>', methods=['PUT'])
def api_update_good(good_id):
    """
    API Endpoint to update details of an existing good.

    Method:
        PUT

    URL:
        /api/goods/update/<good_id>

    URL Parameters:
        good_id (int): The unique ID of the good to update.

    Request Body:
        JSON object containing fields to update. Valid fields include:
            - 'name' (str, optional)
            - 'category' (str, optional): Must be one of ['food', 'clothes', 'accessories', 'electronics'] if provided.
            - 'price' (float, optional): Must be non-negative if provided.
            - 'description' (str, optional)
            - 'stock_count' (int, optional): Must be non-negative if provided.

    Success Response:
        Code: 200
        Content: Updated good dictionary in JSON format.

    Error Responses:
        Code: 400
            - No fields to update.
            - Invalid category, stock_count, or price.
            - Invalid request format.
        Code: 404
            - Good not found or failed to update.

    Example:
        PUT /api/goods/update/1
        {
            "price": 899.99,
            "stock_count": 45
        }
    """
    try:
        updated_fields = request.get_json()
        if not updated_fields:
            return jsonify({"error": "No fields to update"}), 400

        # Validate category if it's being updated
        if 'category' in updated_fields and updated_fields['category'] not in ['food', 'clothes', 'accessories', 'electronics']:
            return jsonify({"error": "Invalid category"}), 400

        # Validate stock_count if it's being updated
        if 'stock_count' in updated_fields:
            if not isinstance(updated_fields['stock_count'], int) or updated_fields['stock_count'] < 0:
                return jsonify({"error": "Invalid stock_count"}), 400

        # Validate price if it's being updated
        if 'price' in updated_fields:
            if not isinstance(updated_fields['price'], (int, float)) or updated_fields['price'] < 0:
                return jsonify({"error": "Invalid price"}), 400

        updated_good = update_good(good_id, updated_fields)
        if updated_good:
            return jsonify(updated_good), 200
        else:
            return jsonify({"error": "Good not found or failed to update"}), 404
    except Exception as e:
        return jsonify({"error": f"Invalid request: {e}"}), 400


if __name__ == "__main__":
    create_db_table()
    app.run(debug=True, port=5001)
