"""Flask application factory."""
from flask import Flask
from flask_cors import CORS
from pathlib import Path
from backend.config import DB_PATH
from backend.database.db_utils import init_database


def create_app(db_path: Path = None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Initialize database
    if db_path is None:
        db_path = DB_PATH

    init_database(db_path)

    # Store db_path in app config for routes to use
    app.config['DB_PATH'] = db_path

    # Register blueprints
    from backend.api.routes import api_bp
    app.register_blueprint(api_bp)

    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
