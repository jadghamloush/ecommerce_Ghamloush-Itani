from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this to a strong secret in production
jwt = JWTManager(app)

DATABASE = 'reviews_database.db'

def connect_to_db():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the 'reviews_database.db'.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_db_table():
    """
    Creates the necessary tables in the database if they do not already exist.
    Tables:
        - users: Stores user credentials and roles.
        - reviews: Stores product reviews with moderation status.
    """
    try:
        conn = connect_to_db()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'admin'))
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                customer_username TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                moderated BOOLEAN DEFAULT 0,
                flagged BOOLEAN DEFAULT 0,
                FOREIGN KEY (customer_username) REFERENCES users(username)
            );
        ''')
        conn.commit()
        print("Tables created successfully or already exist.")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    """
    API endpoint to register a new user.

    Request Body:
        JSON object containing:
            - username (str): The desired username.
            - password (str): The desired password.
            - role (str): The role of the user ('user' or 'admin').

    Returns:
        Response: JSON response with a status message.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'

    if not username or not password:
        return jsonify({"status": "Error: Username and password are required."}), 400

    if role not in ['user', 'admin']:
        return jsonify({"status": "Error: Invalid role specified."}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed_password, role))
        conn.commit()
        return jsonify({"status": "User registered successfully."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "Error: Username already exists."}), 409
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    """
    API endpoint to authenticate a user and provide a JWT.

    Request Body:
        JSON object containing:
            - username (str): The user's username.
            - password (str): The user's password.

    Returns:
        Response: JSON response with the access token or an error message.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "Error: Username and password are required."}), 400

    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT password, role FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity={'username': username, 'role': user['role']})
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"status": "Error: Invalid username or password."}), 401
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

# Decorator for Admin-Only Routes
def admin_required(fn):
    """
    Custom decorator to ensure that the user has admin privileges.

    Args:
        fn (function): The route function to decorate.

    Returns:
        function: The decorated function.
    """
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'admin':
            return jsonify({"status": "Error: Admin privileges required."}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# Insert Review (Authenticated Users)
@app.route('/api/reviews', methods=['POST'])
@jwt_required()
def api_add_review():
    """
    API endpoint to add a new review. Only authenticated users can add reviews.

    Request Body:
        JSON object containing:
            - product_name (str): The name of the product being reviewed.
            - rating (int): The rating of the product (1-5).
            - comment (str): The review comment.

    Returns:
        Response: JSON response with a status message.
    """
    data = request.get_json()
    product_name = data.get('product_name')
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not product_name or not rating:
        return jsonify({"status": "Error: Missing required fields."}), 400

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"status": "Error: Rating must be an integer between 1 and 5."}), 400

    identity = get_jwt_identity()
    customer_username = identity['username']

    review = {
        'product_name': product_name,
        'customer_username': customer_username,
        'rating': rating,
        'comment': comment
    }

    return jsonify(insert_review(review)), 200

def insert_review(review):
    """
    Inserts a new review into the 'reviews' table.

    Args:
        review (dict): A dictionary containing review details:
            - product_name (str): The name of the product being reviewed.
            - customer_username (str): The username of the customer submitting the review.
            - rating (int): The rating of the product (1-5).
            - comment (str): The review comment.

    Returns:
        dict: A status message indicating success or failure.
    """
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

# Update Review (Authenticated Users)
@app.route('/api/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
def api_update_review(review_id):
    """
    API endpoint to update an existing review. Only the author or an admin can update a review.

    Args:
        review_id (int): The ID of the review to update.

    Request Body:
        JSON object containing:
            - rating (int): The updated rating of the product (1-5).
            - comment (str): The updated review comment.

    Returns:
        Response: JSON response with a status message.
    """
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')

    if rating is not None:
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return jsonify({"status": "Error: Rating must be an integer between 1 and 5."}), 400

    identity = get_jwt_identity()
    customer_username = identity['username']
    user_role = identity['role']

    # Fetch the review to verify ownership
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT customer_username FROM reviews WHERE review_id = ?", (review_id,))
        review = cur.fetchone()
        if not review:
            return jsonify({"status": "Error: Review not found."}), 404
        if review['customer_username'] != customer_username and user_role != 'admin':
            return jsonify({"status": "Error: Unauthorized to update this review."}), 403
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

    updated_review = {}
    if rating is not None:
        updated_review['rating'] = rating
    if comment:
        updated_review['comment'] = comment

    if not updated_review:
        return jsonify({"status": "Error: No fields to update."}), 400

    return jsonify(update_review(review_id, updated_review)), 200

def update_review(review_id, updated_review):
    """
    Updates an existing review in the 'reviews' table.

    Args:
        review_id (int): The ID of the review to update.
        updated_review (dict): A dictionary containing the updated review details:
            - rating (int): The updated rating of the product (1-5).
            - comment (str): The updated review comment.

    Returns:
        dict: A status message indicating success or failure.
    """
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("UPDATE reviews SET rating = ?, comment = ? WHERE review_id = ?",
                    (updated_review.get('rating'), updated_review.get('comment'), review_id))
        conn.commit()
        return {"status": "Review updated successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

# Delete Review (Authenticated Users)
@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def api_delete_review(review_id):
    """
    API endpoint to delete a review. Only the author or an admin can delete a review.

    Args:
        review_id (int): The ID of the review to delete.

    Returns:
        Response: JSON response with a status message.
    """
    identity = get_jwt_identity()
    customer_username = identity['username']
    user_role = identity['role']

    # Fetch the review to verify ownership
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT customer_username FROM reviews WHERE review_id = ?", (review_id,))
        review = cur.fetchone()
        if not review:
            return jsonify({"status": "Error: Review not found."}), 404
        if review['customer_username'] != customer_username and user_role != 'admin':
            return jsonify({"status": "Error: Unauthorized to delete this review."}), 403
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify(delete_review(review_id)), 200

def delete_review(review_id):
    """
    Deletes a review from the 'reviews' table.

    Args:
        review_id (int): The ID of the review to delete.

    Returns:
        dict: A status message indicating success or failure.
    """
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

# Retrieve Product Reviews (Public)
@app.route('/api/reviews/product/<product_name>', methods=['GET'])
def api_get_product_reviews(product_name):
    """
    API endpoint to retrieve all reviews for a specific product.

    Args:
        product_name (str): The name of the product.

    Returns:
        Response: JSON response containing a list of reviews.
    """
    reviews = get_product_reviews(product_name)
    if isinstance(reviews, dict) and 'status' in reviews:
        return jsonify(reviews), 500
    return jsonify(reviews), 200

def get_product_reviews(product_name):
    """
    Retrieves all reviews for a specific product.

    Args:
        product_name (str): The name of the product.

    Returns:
        list[dict]: A list of reviews for the specified product.
    """
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

# Retrieve Customer Reviews (Authenticated Users)
@app.route('/api/reviews/customer/<customer_username>', methods=['GET'])
@jwt_required()
def api_get_customer_reviews(customer_username):
    """
    API endpoint to retrieve all reviews submitted by a specific customer.
    Only the customer themselves or an admin can access this endpoint.

    Args:
        customer_username (str): The username of the customer.

    Returns:
        Response: JSON response containing a list of reviews.
    """
    identity = get_jwt_identity()
    requester_username = identity['username']
    user_role = identity['role']

    if requester_username != customer_username and user_role != 'admin':
        return jsonify({"status": "Error: Unauthorized to view these reviews."}), 403

    reviews = get_customer_reviews(customer_username)
    if isinstance(reviews, dict) and 'status' in reviews:
        return jsonify(reviews), 500
    return jsonify(reviews), 200

def get_customer_reviews(customer_username):
    """
    Retrieves all reviews submitted by a specific customer.

    Args:
        customer_username (str): The username of the customer.

    Returns:
        list[dict]: A list of reviews submitted by the specified customer.
    """
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

# Flag Review (Authenticated Users)
@app.route('/api/reviews/flag/<int:review_id>', methods=['POST'])
@jwt_required()
def api_flag_review(review_id):
    """
    API endpoint to flag a review as inappropriate.

    Args:
        review_id (int): The ID of the review to flag.

    Returns:
        Response: JSON response with a status message.
    """
    identity = get_jwt_identity()
    customer_username = identity['username']

    try:
        conn = connect_to_db()
        cur = conn.cursor()
        # Check if the review exists
        cur.execute("SELECT * FROM reviews WHERE review_id = ?", (review_id,))
        review = cur.fetchone()
        if not review:
            return jsonify({"status": "Error: Review not found."}), 404
        # Update the 'flagged' status
        cur.execute("UPDATE reviews SET flagged = 1 WHERE review_id = ?", (review_id,))
        conn.commit()
        return jsonify({"status": "Review flagged for moderation."}), 200
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

# Moderate Review (Admin Only)
@app.route('/api/reviews/moderate/<int:review_id>', methods=['POST'])
@admin_required
def api_moderate_review(review_id):
    """
    API endpoint to moderate a flagged review. Only administrators can access this endpoint.

    Args:
        review_id (int): The ID of the review to moderate.

    Request Body:
        JSON object containing:
            - action (str): The moderation action ('approve' or 'reject').

    Returns:
        Response: JSON response with a status message.
    """
    data = request.get_json()
    action = data.get('action')

    if action not in ['approve', 'reject']:
        return jsonify({"status": "Error: Invalid action. Use 'approve' or 'reject'."}), 400

    # Fetch the review to verify it's flagged
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT flagged FROM reviews WHERE review_id = ?", (review_id,))
        review = cur.fetchone()
        if not review:
            return jsonify({"status": "Error: Review not found."}), 404
        if not review['flagged']:
            return jsonify({"status": "Error: Review is not flagged for moderation."}), 400
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500
    finally:
        conn.close()

    # Perform moderation
    result = moderate_review(review_id, action)
    return jsonify(result), 200

def moderate_review(review_id, action):
    """
    Moderates a review by approving or rejecting it.

    Args:
        review_id (int): The ID of the review to moderate.
        action (str): The moderation action ('approve' or 'reject').

    Returns:
        dict: A status message indicating success or failure.
    """
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        moderated_value = 1 if action == "approve" else 0
        cur.execute("UPDATE reviews SET moderated = ?, flagged = 0 WHERE review_id = ?",
                    (moderated_value, review_id))
        conn.commit()
        return {"status": "Review moderated successfully"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}
    finally:
        conn.close()

# Retrieve Review Details (Public)
@app.route('/api/reviews/details/<int:review_id>', methods=['GET'])
def api_get_review_details(review_id):
    """
    API endpoint to retrieve the details of a specific review.

    Args:
        review_id (int): The ID of the review.

    Returns:
        Response: JSON response with review details or a status message.
    """
    review = get_review_details(review_id)
    if isinstance(review, dict) and 'status' in review:
        return jsonify(review), 404 if review['status'] == 'Review not found' else 500
    return jsonify(review), 200

def get_review_details(review_id):
    """
    Retrieves the details of a specific review.

    Args:
        review_id (int): The ID of the review.

    Returns:
        dict: The details of the review or a status message if not found.
    """
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

if __name__ == "__main__":
    create_db_table()
    app.run(debug=True, port=5004)
