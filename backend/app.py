"""Flask application factory."""
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import logging

from backend.config import get_config
from backend.api.routes import api_bp
from backend.api.auth_routes import auth_bp
from backend.database.db_utils import init_database


def create_app(db_path: Path = None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Override DB path if provided (for testing)
    if db_path:
        app.config['DB_PATH'] = db_path

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ALLOWED_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 600
        }
    })

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register error handlers
    register_error_handlers(app)

    # Initialize database
    init_database(app.config['DB_PATH'])

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy'})

    return app


def register_error_handlers(app):
    """Register error handlers for consistent JSON error responses."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({
            'error': 'Bad request',
            'status': 400,
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({
            'error': 'Resource not found',
            'status': 404
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed."""
        return jsonify({
            'error': 'Method not allowed',
            'status': 405
        }), 405

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Payload Too Large."""
        max_size_mb = app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024)
        return jsonify({
            'error': f'File too large. Maximum size is {max_size_mb:.0f}MB',
            'status': 413
        }), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        # Log the full error for debugging
        app.logger.error(f'Internal server error: {error}', exc_info=True)

        # Return generic error to client (don't leak details)
        return jsonify({
            'error': 'Internal server error',
            'status': 500
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle any unhandled exceptions."""
        # Log the exception
        app.logger.error(f'Unhandled exception: {error}', exc_info=True)

        # Return 500 error
        return jsonify({
            'error': 'Internal server error',
            'status': 500
        }), 500


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
