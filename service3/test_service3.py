import pytest
import os
import sqlite3
from service3 import app, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_sales_database.db'

    def connect_to_db_override():
        conn = sqlite3.connect(app.config['DATABASE'])
        return conn

    import service3
    service3.connect_to_db = connect_to_db_override

    # Create necessary tables for testing
    create_tables_for_test()

    with app.test_client() as client:
        yield client

    os.remove(app.config['DATABASE'])

def create_tables_for_test():
    conn = sqlite3.connect('test_sales_database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            username TEXT PRIMARY KEY,
            wallet_balance REAL DEFAULT 0
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS goods (
            name TEXT PRIMARY KEY,
            price_per_item REAL NOT NULL,
            count_in_stock INTEGER NOT NULL
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_username TEXT NOT NULL,
            good_name TEXT NOT NULL,
            sale_date TEXT NOT NULL,
            sale_amount REAL NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

def test_make_sale(client):
    # Set up customer and good
    conn = sqlite3.connect('test_sales_database.db')
    conn.execute("INSERT INTO customers (username, wallet_balance) VALUES ('testuser', 1000.0)")
    conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES ('TestProduct', 100.0, 5)")
    conn.commit()
    conn.close()

    sale_data = {
        'customer_username': 'testuser',
        'good_name': 'TestProduct'
    }
    response = client.post('/api/make_sale', json=sale_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Sale successful'

def test_display_available_goods(client):
    # Add goods to display
    conn = sqlite3.connect('test_sales_database.db')
    conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES ('AvailableProduct', 50.0, 10)")
    conn.commit()
    conn.close()

    response = client.get('/api/display_goods')
    assert response.status_code == 200
    data = response.get_json()
    assert any(good['name'] == 'AvailableProduct' for good in data)

def test_get_good_details(client):
    # Add a good to retrieve details
    conn = sqlite3.connect('test_sales_database.db')
    conn.execute("INSERT INTO goods (name, price_per_item, count_in_stock) VALUES ('DetailProduct', 75.0, 3)")
    conn.commit()
    conn.close()

    response = client.get('/api/goods_details/DetailProduct')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'DetailProduct'

def test_get_customer_sales(client):
    # Add a sale record
    conn = sqlite3.connect('test_sales_database.db')
    conn.execute("INSERT INTO sales (customer_username, good_name, sale_date, sale_amount) VALUES ('testuser', 'TestProduct', '2021-01-01', 100.0)")
    conn.commit()
    conn.close()

    response = client.get('/api/customer_sales/testuser')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]['customer_username'] == 'testuser'
