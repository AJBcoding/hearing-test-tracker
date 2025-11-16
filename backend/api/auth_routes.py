"""Authentication routes."""
from flask import Blueprint, request, jsonify, current_app
from backend.database.db_utils import get_connection
from backend.auth.utils import hash_password, verify_password, generate_token

auth_bp = Blueprint('auth', __name__)


def _get_db_connection():
    """Get database connection using app config."""
    db_path = current_app.config.get('DB_PATH')
    return get_connection(db_path)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Check if user already exists
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM user WHERE email = ?', (email,))
    if cursor.fetchone():
        return jsonify({'error': 'Email already exists'}), 409

    # Hash password and create user
    password_hash = hash_password(password)

    cursor.execute(
        'INSERT INTO user (email, password_hash) VALUES (?, ?)',
        (email, password_hash)
    )
    conn.commit()

    user_id = cursor.lastrowid

    # Generate token
    token = generate_token(user_id)

    return jsonify({
        'user_id': user_id,
        'email': email,
        'token': token
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login existing user."""
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Get user from database
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id, password_hash FROM user WHERE email = ?',
        (email,)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    user_id, password_hash = user

    # Verify password
    if not verify_password(password, password_hash):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Generate token
    token = generate_token(user_id)

    return jsonify({
        'user_id': user_id,
        'email': email,
        'token': token
    })
