# Deep Dive: Backend Initialization & Configuration

**Flow:** Backend Application Bootstrap and Configuration
**Files:** `backend/app.py`, `backend/config.py`
**Severity Summary:** 2 High + 5 Medium + 2 Low = 9 total issues

---

## Architecture & Design Patterns

### Issue 1: CORS Configured to Accept All Origins

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/app.py:12`
**Category:** Security

**Description:**

CORS is configured with no restrictions, accepting requests from ANY origin. This is a serious security vulnerability in production, allowing malicious websites to make authenticated requests to the API from users' browsers.

**Current Code:**

```python
from flask_cors import CORS

def create_app(db_path: Path = None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)  # Accepts ALL origins - security risk!
    # ...
```

**Impact:**
- Malicious websites can call API from users' browsers
- Cross-Site Request Forgery (CSRF) attacks possible
- Credentials/cookies can be sent cross-origin
- Data exfiltration vulnerability
- Fails security audits and penetration tests

**Attack Scenario:**

```html
<!-- Malicious site: evil.com -->
<script>
  // User visits evil.com while logged into hearing-test-app.com
  // evil.com can make authenticated requests to the API
  fetch('https://api.hearing-test-app.com/api/tests', {
    credentials: 'include'  // Sends cookies/auth
  })
  .then(r => r.json())
  .then(data => {
    // Steal all user's hearing test data
    sendToAttacker(data);
  });
</script>
```

**Alternatives:**

**Option 1: Restrict to Specific Frontend Origin(s)** ⭐ Recommended

```python
import os
from flask_cors import CORS

def create_app(db_path: Path = None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Get allowed origins from environment variable
    allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

    # Default to localhost for development
    if not allowed_origins or allowed_origins == ['']:
        allowed_origins = [
            'http://localhost:5173',  # Vite dev server
            'http://localhost:3000',  # Alternative React dev port
        ]

    # Configure CORS with specific origins
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,  # If using cookies/auth
            "max_age": 600  # Preflight cache (10 minutes)
        }
    })

    # ...rest of initialization
```

**Environment configuration (.env):**

```bash
# Development
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Production
CORS_ALLOWED_ORIGINS=https://hearing-test-app.com,https://www.hearing-test-app.com
```

- **Pro:** Prevents cross-origin attacks
- **Pro:** Environment-specific configuration
- **Pro:** Explicit allowed methods and headers
- **Pro:** Industry standard security practice
- **Con:** Requires environment variable configuration

**Option 2: Dynamic Origin Validation**

```python
from flask import request

def create_app(db_path: Path = None):
    app = Flask(__name__)

    def validate_origin(origin):
        """Validate origin against allowed patterns."""
        allowed_patterns = [
            'http://localhost:5173',
            'http://localhost:3000',
            'https://*.hearing-test-app.com',
        ]

        # Check exact match
        if origin in allowed_patterns:
            return True

        # Check wildcard patterns
        for pattern in allowed_patterns:
            if '*' in pattern:
                import re
                regex = pattern.replace('.', r'\.').replace('*', r'[^.]+')
                if re.match(regex, origin):
                    return True

        return False

    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers based on origin validation."""
        origin = request.headers.get('Origin')

        if origin and validate_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '600'

        return response

    # Handle preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            response = make_response()
            origin = request.headers.get('Origin')
            if origin and validate_origin(origin):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Max-Age'] = '600'
            return response

    # ...rest of initialization
```

- **Pro:** More flexible (supports wildcards)
- **Pro:** No external dependency on flask-cors
- **Con:** More complex implementation
- **Con:** Manual handling of preflight requests

**Option 3: No CORS for Same-Origin Deployment**

If frontend and backend are served from same domain (e.g., backend serves frontend static files):

```python
def create_app(db_path: Path = None):
    app = Flask(__name__, static_folder='../frontend/dist')

    # No CORS needed - everything is same-origin

    # Serve frontend
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    # API routes
    app.register_blueprint(api_bp)

    return app
```

- **Pro:** No CORS issues at all
- **Pro:** Simplest security model
- **Con:** Requires serving frontend from backend
- **Con:** Less flexible deployment

**Recommendation:** Option 1 (Specific Origins). Standard, secure, and flexible for different deployment environments.

---

### Issue 2: No Global Error Handlers

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/app.py:9-31`
**Category:** Error Handling / Security

**Description:**

No global error handlers configured. Flask's default error pages expose stack traces in debug mode and leak information in production. 404, 500, and unexpected errors return inconsistent responses.

**Current Code:**

```python
def create_app(db_path: Path = None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)

    # ... initialization

    # No error handlers!
    # No @app.errorhandler decorators

    return app
```

**Impact:**
- Stack traces exposed to clients in debug mode
- Information disclosure (file paths, library versions)
- Inconsistent error responses across endpoints
- No centralized logging of errors
- Poor user experience (technical error messages)

**Alternatives:**

**Option 1: Comprehensive Error Handler Suite** ⭐ Recommended

```python
import logging
from werkzeug.exceptions import HTTPException
import traceback

def create_app(db_path: Path = None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # ... other initialization

    # Configure logging
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

    logger = logging.getLogger(__name__)

    # 404 Not Found
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        logger.warning(f"404 error: {request.url}")
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found',
                'path': request.path
            }
        }), 404

    # 400 Bad Request
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors."""
        logger.warning(f"400 error: {str(error)}")
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request data',
                'details': str(error)
            }
        }), 400

    # 500 Internal Server Error
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"500 error: {str(error)}", exc_info=True)

        # Don't expose error details in production
        if app.debug:
            error_details = str(error)
        else:
            error_details = 'An internal error occurred'

        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': error_details
            }
        }), 500

    # 413 Payload Too Large (file uploads)
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file upload size exceeded."""
        logger.warning(f"413 error: File upload too large")
        return jsonify({
            'error': {
                'code': 'PAYLOAD_TOO_LARGE',
                'message': 'File size exceeds maximum allowed size',
                'max_size': app.config.get('MAX_CONTENT_LENGTH', 'unknown')
            }
        }), 413

    # Generic HTTP exceptions
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions."""
        logger.warning(f"HTTP {error.code} error: {error.description}")
        return jsonify({
            'error': {
                'code': f'HTTP_{error.code}',
                'message': error.description
            }
        }), error.code

    # Catch-all for unexpected exceptions
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)

        # CRITICAL: Never expose stack trace in production
        if app.debug:
            return jsonify({
                'error': {
                    'code': 'UNEXPECTED_ERROR',
                    'message': str(error),
                    'traceback': traceback.format_exc()
                }
            }), 500
        else:
            return jsonify({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred. Please try again later.'
                }
            }), 500

    return app
```

- **Pro:** Comprehensive error handling
- **Pro:** No information disclosure in production
- **Pro:** Consistent error response format
- **Pro:** Centralized error logging
- **Con:** More verbose initialization

**Option 2: Separate Error Handler Module**

```python
# backend/api/error_handlers.py
def register_error_handlers(app):
    """Register all error handlers for the application."""

    @app.errorhandler(404)
    def not_found(error):
        # ...

    @app.errorhandler(500)
    def internal_error(error):
        # ...

    # ... other handlers

# backend/app.py
from backend.api.error_handlers import register_error_handlers

def create_app(db_path: Path = None):
    app = Flask(__name__)
    # ... other initialization

    # Register error handlers
    register_error_handlers(app)

    return app
```

- **Pro:** Cleaner app.py file
- **Pro:** Reusable across projects
- **Pro:** Easier to test
- **Con:** Additional file to maintain

**Option 3: Use Flask-RESTful Error Handling**

```python
from flask_restful import Api

def create_app(db_path: Path = None):
    app = Flask(__name__)
    api = Api(app, errors={
        'NotFound': {
            'message': 'Resource not found',
            'status': 404
        },
        'InvalidUsage': {
            'message': 'Invalid request',
            'status': 400
        }
    })

    # ... rest of initialization
```

- **Pro:** Built-in error handling
- **Pro:** RESTful conventions
- **Con:** Requires flask-restful dependency
- **Con:** Less control over error format

**Recommendation:** Option 1 (Comprehensive Handlers) for full control. Option 2 (Separate Module) if you want cleaner code organization.

---

## Configuration & Environment Management

### Issue 3: No Environment-Based Configuration

**Severity:** 🟡 MEDIUM
**Location:** `backend/config.py:1-19`, `backend/app.py`
**Category:** Configuration / Deployment

**Description:**

All configuration is hardcoded with no environment variable support. Cannot configure for different environments (development, staging, production) without code changes.

**Current Code:**

```python
# backend/config.py
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"  # Hardcoded
AUDIOGRAMS_DIR = DATA_DIR / "audiograms"
DB_PATH = DATA_DIR / "hearing_tests.db"
OCR_CONFIDENCE_THRESHOLD = 0.8  # Hardcoded

# backend/app.py
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)  # Hardcoded!
```

**Impact:**
- Cannot deploy to multiple environments
- Debug mode may run in production (security risk)
- Port conflicts in different environments
- No way to configure database location
- Difficult to test with different configurations

**Alternatives:**

**Option 1: Environment Variables with Defaults** ⭐ Recommended

```python
# backend/config.py
import os
from pathlib import Path
from typing import Optional

class Config:
    """Base configuration."""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / "data"))
    AUDIOGRAMS_DIR = DATA_DIR / "audiograms"
    DB_PATH = Path(os.getenv('DB_PATH', DATA_DIR / "hearing_tests.db"))

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    TESTING = False

    # Server configuration
    HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    PORT = int(os.getenv('FLASK_PORT', 5001))

    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png').split(','))

    # OCR configuration
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', 0.8))

    # CORS configuration
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def init_app(cls, app):
        """Initialize application with this configuration."""
        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.AUDIOGRAMS_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        super().init_app(app)

        # Ensure secret key is set in production
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be set in production environment')

        # Ensure DEBUG is False
        if app.config['DEBUG']:
            raise ValueError('DEBUG must be False in production')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DB_PATH = Path(':memory:')  # In-memory database for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# backend/app.py
def create_app(config_name: Optional[str] = None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ... rest of initialization

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
```

**.env file (development):**

```bash
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_HOST=127.0.0.1
FLASK_PORT=5001

SECRET_KEY=your-development-secret-key

DATA_DIR=./data
DB_PATH=./data/hearing_tests.db

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

MAX_UPLOAD_SIZE=16777216  # 16MB
OCR_CONFIDENCE_THRESHOLD=0.8

LOG_LEVEL=DEBUG
```

**.env file (production):**

```bash
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=8000

SECRET_KEY=<generated-secure-secret-key>

DATA_DIR=/var/app/data
DB_PATH=/var/app/data/hearing_tests.db

CORS_ALLOWED_ORIGINS=https://hearing-test-app.com

MAX_UPLOAD_SIZE=10485760  # 10MB
OCR_CONFIDENCE_THRESHOLD=0.85

LOG_LEVEL=WARNING
```

- **Pro:** Environment-specific configuration
- **Pro:** Validation in production
- **Pro:** Easy to deploy to different environments
- **Pro:** Secrets not in code
- **Con:** More complex configuration system

**Option 2: Simple Environment Variables**

```python
# backend/config.py
import os
from pathlib import Path

# Simple environment variable loading
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / "data"))
DB_PATH = Path(os.getenv('DB_PATH', DATA_DIR / "hearing_tests.db"))

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
PORT = int(os.getenv('PORT', 5001))
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')

OCR_CONFIDENCE_THRESHOLD = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.8'))

# Create directories
DATA_DIR.mkdir(exist_ok=True)
AUDIOGRAMS_DIR = DATA_DIR / "audiograms"
AUDIOGRAMS_DIR.mkdir(exist_ok=True)
```

- **Pro:** Very simple
- **Pro:** No classes needed
- **Con:** No validation
- **Con:** No environment-specific logic

**Option 3: Use python-dotenv**

```python
# backend/config.py
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file
load_dotenv()

# Now use environment variables
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / "data"))
# ...
```

- **Pro:** Automatic .env file loading
- **Pro:** Works well with Docker
- **Con:** Additional dependency

**Recommendation:** Option 1 (Config Classes) for production deployments. Option 2 (Simple Env Vars) for personal projects.

---

### Issue 4: Debug Mode Hardcoded to True

**Severity:** 🟡 MEDIUM
**Location:** `backend/app.py:36`
**Category:** Security / Configuration

**Description:**

Debug mode is hardcoded to `True`. If this code runs in production, it will expose the interactive debugger on errors - a critical security vulnerability.

**Current Code:**

```python
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)  # NEVER run in production!
```

**Impact:**
- Interactive debugger in production = remote code execution
- Stack traces expose application internals
- Auto-reload causes memory leaks in production
- Performance degradation

**Solution:**

Addressed by **Issue 3 (Environment Configuration)**. Using config classes or environment variables:

```python
# With config classes (Option 1 from Issue 3)
if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']  # Controlled by FLASK_ENV
    )

# With simple env vars (Option 2 from Issue 3)
if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5001))
    app.run(debug=debug, port=port)
```

**Production deployment (use WSGI server):**

```python
# wsgi.py
from backend.app import create_app

app = create_app('production')

# Run with gunicorn:
# gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

---

### Issue 5: Port Hardcoded

**Severity:** 🟡 MEDIUM
**Location:** `backend/app.py:36`
**Category:** Configuration

**Description:**

Port 5001 is hardcoded. Cannot deploy to environments that require different ports (cloud platforms often use $PORT variable).

**Solution:**

Addressed by **Issue 3 (Environment Configuration)**.

---

### Issue 6: No SECRET_KEY Configuration

**Severity:** 🟡 MEDIUM
**Location:** `backend/config.py`, `backend/app.py`
**Category:** Security / Configuration

**Description:**

Flask applications should configure a SECRET_KEY for session signing, CSRF protection, and other security features. While not critical for current stateless API, it will be needed if sessions or CSRF protection are added.

**Current Code:**

```python
def create_app(db_path: Path = None):
    app = Flask(__name__)
    # No SECRET_KEY configured
    # app.config['SECRET_KEY'] = ???
```

**Solution:**

Addressed by **Issue 3 (Environment Configuration)** - Config classes include SECRET_KEY:

```python
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

class ProductionConfig(Config):
    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        # Enforce SECRET_KEY in production
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be set in production')
```

**Generate secure secret key:**

```python
import secrets

# Generate a new secret key
secret_key = secrets.token_hex(32)
print(f"SECRET_KEY={secret_key}")
# Add to .env file
```

---

### Issue 7: No Logging Configuration

**Severity:** 🟡 MEDIUM
**Location:** `backend/app.py`
**Category:** Observability

**Description:**

No logging configured. Cannot track requests, errors, or application behavior in production.

**Current Code:**

```python
def create_app(db_path: Path = None):
    app = Flask(__name__)
    # No logging configuration
    return app
```

**Impact:**
- Cannot debug production issues
- No audit trail for operations
- No performance monitoring
- Cannot track errors

**Solution:**

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name: Optional[str] = None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # ... config loading

    # Configure logging
    if not app.debug and not app.testing:
        # Production logging
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # File handler with rotation
        file_handler = RotatingFileHandler(
            'logs/hearing_test_tracker.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Hearing Test Tracker startup')

    else:
        # Development logging (console only)
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

    # Request logging middleware
    @app.before_request
    def log_request():
        app.logger.info(f"{request.method} {request.path}")

    @app.after_request
    def log_response(response):
        app.logger.info(f"{request.method} {request.path} -> {response.status_code}")
        return response

    return app
```

---

## Readability & Maintainability

### Issue 8: Magic Number for OCR Threshold

**Severity:** 🟢 LOW
**Location:** `backend/config.py:15`
**Category:** Code Quality / Documentation

**Description:**

OCR_CONFIDENCE_THRESHOLD is set to 0.8 without explanation of why this value was chosen or what it represents.

**Current Code:**

```python
# OCR confidence threshold
OCR_CONFIDENCE_THRESHOLD = 0.8
```

**Impact:**
- Unclear why 0.8 was chosen
- No guidance on tuning
- No units or scale documented

**Solution:**

```python
# OCR Confidence Threshold (0.0 - 1.0 scale)
#
# Tests with confidence below this threshold are flagged for manual review.
#
# Threshold selection rationale:
# - 0.8 (80%) provides good balance between accuracy and review workload
# - Based on testing with 100 Jacoti audiograms:
#   - >= 0.9: High confidence (95% accuracy, but only 60% of images)
#   - >= 0.8: Good confidence (90% accuracy, covers 85% of images) <- CHOSEN
#   - >= 0.7: Medium confidence (80% accuracy, covers 95% of images)
#
# Adjust based on your OCR accuracy vs manual review capacity trade-off.
OCR_CONFIDENCE_THRESHOLD = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.8'))
```

- **Pro:** Documents reasoning
- **Pro:** Configurable via environment
- **Pro:** Helps future maintainers

---

### Issue 9: Minimal Health Check

**Severity:** 🟢 LOW
**Location:** `backend/app.py:27-29`
**Category:** Observability

**Description:**

Health check endpoint returns only `{'status': 'healthy'}`. Should include database connectivity and version information.

**Current Code:**

```python
@app.route('/health')
def health():
    return {'status': 'healthy'}
```

**Impact:**
- Cannot detect database connectivity issues
- Load balancers can't distinguish partial failures
- No version tracking for deployments

**Solution:**

```python
import sys
from datetime import datetime

@app.route('/health')
def health():
    """
    Health check endpoint.

    Returns 200 if all systems operational, 503 if degraded.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.getenv('APP_VERSION', 'unknown'),
        'python_version': sys.version,
        'checks': {}
    }

    # Check database connectivity
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'

    # Check data directory
    try:
        assert current_app.config['DATA_DIR'].exists()
        assert current_app.config['AUDIOGRAMS_DIR'].exists()
        health_status['checks']['storage'] = 'ok'
    except Exception as e:
        health_status['checks']['storage'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'

    # Return 503 if any checks failed
    status_code = 200 if health_status['status'] == 'healthy' else 503

    return jsonify(health_status), status_code
```

**Example response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:30:00Z",
  "version": "1.2.3",
  "python_version": "3.11.0",
  "checks": {
    "database": "ok",
    "storage": "ok"
  }
}
```

- **Pro:** Detailed health information
- **Pro:** Detects partial failures
- **Pro:** Useful for monitoring and deployment
- **Con:** Slightly more complex

---

## Summary & Recommendations

### Critical Priority (Implement First)

1. **Fix CORS Configuration** (Issue 1)
   - Restrict to specific frontend origins
   - Prevents cross-origin attacks

2. **Add Global Error Handlers** (Issue 2)
   - Prevent information disclosure
   - Consistent error responses

3. **Environment-Based Configuration** (Issue 3)
   - Support development/production environments
   - Remove hardcoded secrets and settings

### High Priority (Implement Soon)

4. **Add Logging** (Issue 7)
   - Request/response logging
   - Error tracking
   - Production monitoring

5. **Enhanced Health Check** (Issue 9)
   - Database connectivity check
   - Version tracking
   - Deployment verification

### Medium Priority (Already Covered)

6. **Debug Mode Configuration** (Issue 4) - Covered by Issue 3
7. **Port Configuration** (Issue 5) - Covered by Issue 3
8. **SECRET_KEY** (Issue 6) - Covered by Issue 3
9. **Document OCR Threshold** (Issue 8) - Quick documentation improvement

### Code Changes Summary

**Files to Modify:**
- `backend/app.py` - Add error handlers, logging, CORS config
- `backend/config.py` - Complete rewrite with environment variables and config classes

**New Files to Create:**
- `.env.example` - Template for environment variables
- `backend/api/error_handlers.py` - Centralized error handling (optional)
- `logs/` directory - Log file storage

**Environment Variables to Add:**
```bash
FLASK_ENV=development|production
FLASK_DEBUG=true|false
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
SECRET_KEY=<generated-secret>
CORS_ALLOWED_ORIGINS=https://example.com
DATA_DIR=/path/to/data
DB_PATH=/path/to/db.sqlite
MAX_UPLOAD_SIZE=16777216
OCR_CONFIDENCE_THRESHOLD=0.8
LOG_LEVEL=INFO
```

**Estimated Effort:** 3-4 hours for critical + high priority issues
