#!/usr/bin/python
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

def connect_to_db():
    conn = sqlite3.connect('sales_database.db')
    return conn

def create_db_table():
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
    except:
        print("Sales table creation failed - Maybe table already exists")
    finally:
        conn.close()

def display_available_goods():
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
    except:
        goods = []
    finally:
        conn.close()
    return goods

def get_good_details(good_name):
    good = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM goods WHERE name = ?", (good_name,))
        row = cur.fetchone()
        if row:
            good = dict(row)
    except:
        good = {}
    finally:
        conn.close()
    return good

def make_sale(customer_username, good_name):
    sale_result = {}
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Check if the customer has enough money in the wallet
        cur.execute("SELECT wallet_balance FROM customers WHERE username = ?", (customer_username,))
        wallet_balance = cur.fetchone()["wallet_balance"]
        cur.execute("SELECT price_per_item, count_in_stock FROM goods WHERE name = ?", (good_name,))
        result = cur.fetchone()

        if result and wallet_balance >= result["price_per_item"] and result["count_in_stock"] > 0:
            # Deduct money from the customer's wallet
            cur.execute("UPDATE customers SET wallet_balance = wallet_balance - ? WHERE username = ?", (result["price_per_item"], customer_username))
            # Decrease the count of the purchased good from the database
            cur.execute("UPDATE goods SET count_in_stock = count_in_stock - 1 WHERE name = ?", (good_name,))
            # Record the sale in the sales table
            cur.execute("INSERT INTO sales (customer_username, good_name, sale_date, sale_amount) VALUES (?, ?, datetime('now'), ?)",
                        (customer_username, good_name, result["price_per_item"]))
            conn.commit()
            sale_result["status"] = "Sale successful"
        else:
            sale_result["status"] = "Insufficient funds or item not available for sale"
    except:
        conn.rollback()
        sale_result["status"] = "Sale failed"
    finally:
        conn.close()
    return sale_result

def get_customer_sales(customer_username):
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
    except:
        sales = []
    finally:
        conn.close()
    return sales




app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})



@app.route('/api/display_goods', methods=['GET'])
def api_display_goods():
    return jsonify(display_available_goods())

@app.route('/api/goods_details/<good_name>', methods=['GET'])
def api_get_good_details(good_name):
    return jsonify(get_good_details(good_name))

@app.route('/api/make_sale', methods=['POST'])
def api_make_sale():
    sale_data = request.get_json()
    return jsonify(make_sale(sale_data['customer_username'], sale_data['good_name']))

@app.route('/api/customer_sales/<customer_username>', methods=['GET'])
def api_get_customer_sales(customer_username):
    return jsonify(get_customer_sales(customer_username))

if __name__ == "__main__":
    app.run(debug=True, port=5002)
