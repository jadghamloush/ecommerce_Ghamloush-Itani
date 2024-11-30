from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

def connect_to_db():
    conn = sqlite3.connect('reviews_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_db_table():
    try:
        conn = connect_to_db()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                customer_username TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                moderated BOOLEAN DEFAULT 0
            );
        ''')
        conn.commit()
        print("Reviews table created successfully")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

# Helper functions
def insert_review(review):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO reviews (product_name, customer_username, rating, comment) VALUES (?, ?, ?, ?)",
                    (review['product_name'], review['customer_username'], review['rating'], review['comment']))
        conn.commit()
        return {"status": "Review added successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def update_review(review_id, updated_review):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("UPDATE reviews SET rating = ?, comment = ? WHERE review_id = ?",
                    (updated_review['rating'], updated_review['comment'], review_id))
        conn.commit()
        return {"status": "Review updated successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def delete_review(review_id):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
        conn.commit()
        return {"status": "Review deleted successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def get_product_reviews(product_name):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE product_name = ?", (product_name,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def get_customer_reviews(customer_username):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE customer_username = ?", (customer_username,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def moderate_review(review_id, action):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("UPDATE reviews SET moderated = ? WHERE review_id = ?", (1 if action == "approve" else 0, review_id))
        conn.commit()
        return {"status": "Review moderated successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

def get_review_details(review_id):
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE review_id = ?", (review_id,))
        row = cur.fetchone()
        return dict(row) if row else {"status": "Review not found"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/reviews', methods=['POST'])
def api_add_review():
    review = request.get_json()
    return jsonify(insert_review(review))

@app.route('/api/reviews/<int:review_id>', methods=['PUT'])
def api_update_review(review_id):
    updated_review = request.get_json()
    return jsonify(update_review(review_id, updated_review))

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def api_delete_review(review_id):
    return jsonify(delete_review(review_id))

@app.route('/api/reviews/product/<product_name>', methods=['GET'])
def api_get_product_reviews(product_name):
    return jsonify(get_product_reviews(product_name))

@app.route('/api/reviews/customer/<customer_username>', methods=['GET'])
def api_get_customer_reviews(customer_username):
    return jsonify(get_customer_reviews(customer_username))

@app.route('/api/reviews/moderate/<int:review_id>', methods=['POST'])
def api_moderate_review(review_id):
    action = request.json.get('action')
    return jsonify(moderate_review(review_id, action))

@app.route('/api/reviews/details/<int:review_id>', methods=['GET'])
def api_get_review_details(review_id):
    return jsonify(get_review_details(review_id))

if __name__ == "__main__":
    create_db_table()
    app.run(debug=True, port=5004)
