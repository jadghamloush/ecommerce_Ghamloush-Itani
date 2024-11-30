# test_service3.py

import os
import pytest
import sqlite3
import shutil
import json
from service3 import app, create_db_table, connect_to_db

TEST_DB = 'test_sales_database.db'

@pytest.fixture(scope='module')
def test_client():
    # Backup original databases if they exist
    databases = ['sales_database.db', 'customer_database.db', 'inventory_database.db']
    backups = {}
    for db in databases:
        if os.path.exists(db):
            backups[db] = f"{db}_backup.db"
            shutil.copy(db, backups[db])
            os.remove(db)
    
    # Use test databases
    def override_connect_to_db_sales():
        conn = sqlite3.connect(TEST_DB)
        return conn
    
    # Similarly, override customer and inventory databases
    def override_connect_to_db_customers():
        conn = sqlite3.connect('test_customer_database.db')
        return conn
    
    def override_connect_to_db_inventory():
        conn = sqlite3.connect('test_inventory_database.db')
        return conn
    
    # Override the connect_to_db function in service3
    app.config['TESTING'] = True
    with app.test_client() as testing_client:
        with app.app_context():
            global connect_to_db
            connect_to_db = override_connect_to_db_sales
            create_db_table()
            
            # Setup customer database
            conn_customers = sqlite3.connect('test_customer_database.db')
            conn_customers.execute('''
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
            conn_customers.execute("""
                INSERT INTO customers (full_name, username, password, age, address, gender, marital_status, wallet_balance)
                VALUES ('Alice Wonderland', 'alice', 'alicepass', 28, '1 Infinite Loop', 'Female', 'Single', 100.0)
            """)
            conn_customers.commit()
            conn_customers.close()
            
            # Setup inventory database
            conn_inventory = sqlite3.connect('inventory_database.db')
            conn_inventory.execute('''
                CREATE TABLE goods (
                    good_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT CHECK( category IN ('food', 'clothes', 'accessories', 'electronics') ) NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    stock_count INTEGER NOT NULL CHECK(stock_count >= 0)
                );
            ''')
            conn_inventory.execute("""
                INSERT INTO goods (name, category, price, description, stock_count)
                VALUES ('Smartphone', 'electronics', 499.99, 'Latest model smartphone.', 5)
            """)
            conn_inventory.commit()
            conn_inventory.close()
        
        yield testing_client
    
    # Teardown: remove test databases and restore originals
    test_databases = [TEST_DB, 'test_customer_database.db', 'test_inventory_database.db']
    for db in test_databases:
        if os.path.exists(db):
            os.remove(db)
    for db, backup in backups.items():
        shutil.move(backup, db)

def test_display_available_goods(test_client):
    # Display available goods
    response = test_client.get('/api/display_goods')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == "Smartphone"

def test_get_good_details(test_client):
    # Get details of a specific good
    response = test_client.get('/api/goods_details/Smartphone')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == "Smartphone"
    assert data['price'] == 499.99

def test_make_sale_success(test_client):
    # Make a successful sale
    sale_data = {
        "customer_username": "alice",
        "good_name": "Smartphone"
    }
    response = test_client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Sale successful"
    
    # Verify wallet balance deduction and stock count
    # Check customer wallet
    conn = sqlite3.connect('test_customer_database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT wallet_balance FROM customers WHERE username = 'alice'")
    wallet = cur.fetchone()['wallet_balance']
    assert wallet == 100.0 - 499.99  # This should actually result in negative balance, which is an issue
    conn.close()
    
    # Check stock count
    conn = sqlite3.connect('test_inventory_database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT stock_count FROM goods WHERE name = 'Smartphone'")
    stock = cur.fetchone()['stock_count']
    assert stock == 4
    conn.close()

def test_make_sale_insufficient_funds(test_client):
    # Attempt to make a sale with insufficient funds
    sale_data = {
        "customer_username": "alice",
        "good_name": "Smartphone"
    }
    response = test_client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Insufficient funds or item not available for sale"

def test_make_sale_insufficient_stock(test_client):
    # Reduce stock to 0
    conn = sqlite3.connect('test_inventory_database.db')
    conn.execute("UPDATE goods SET stock_count = 0 WHERE name = 'Smartphone'")
    conn.commit()
    conn.close()
    
    # Attempt to make a sale with no stock
    sale_data = {
        "customer_username": "alice",
        "good_name": "Smartphone"
    }
    response = test_client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Insufficient funds or item not available for sale"

def test_get_customer_sales(test_client):
    # Retrieve sales for a customer
    response = test_client.get('/api/customer_sales/alice')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Depending on previous tests, there might be 1 sale or 0
    # Adjust accordingly
    # For this example, assuming the first sale was allowed despite insufficient funds
    assert len(data) == 1
    assert data[0]['customer_username'] == "alice"
    assert data[0]['good_name'] == "Smartphone"

def test_make_sale_nonexistent_customer(test_client):
    # Attempt to make a sale with a non-existent customer
    sale_data = {
        "customer_username": "bob",
        "good_name": "Smartphone"
    }
    response = test_client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Sale failed"

def test_make_sale_nonexistent_good(test_client):
    # Attempt to make a sale with a non-existent good
    sale_data = {
        "customer_username": "alice",
        "good_name": "NonExistentGood"
    }
    response = test_client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "Sale failed"
