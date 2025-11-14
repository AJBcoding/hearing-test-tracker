"""Flask application factory."""
from flask import Flask
from flask_cors import CORS


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)

    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
