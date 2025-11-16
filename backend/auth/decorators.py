"""Authentication decorators."""
from functools import wraps
from flask import request, jsonify, g

from backend.auth.utils import decode_token


def require_auth(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return jsonify({'error': 'Invalid authorization header format'}), 401

        token = parts[1]

        # Decode and verify token
        try:
            payload = decode_token(token)
            g.user_id = payload['user_id']
        except ValueError as e:
            return jsonify({'error': str(e)}), 401

        return f(*args, **kwargs)

    return decorated_function
