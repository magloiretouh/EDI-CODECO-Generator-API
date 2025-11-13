"""
Flask Application Factory and Configuration.
Creates and configures the Flask app with all blueprints and error handlers.
"""

from flask import Flask, jsonify
from flasgger import Swagger
import logging
from config import config
from api.routes import codeco_bp

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_obj=None):
    """
    Flask application factory.

    Creates and configures a Flask application instance with all necessary
    blueprints, error handlers, and middleware.

    Args:
        config_obj: Optional configuration object. Uses config from config.py if not provided.

    Returns:
        Flask: Configured Flask application instance.
    """

    app = Flask(__name__)

    # Load configuration
    if config_obj is None:
        config_obj = config

    app.config['JSON_SORT_KEYS'] = False

    # Register blueprints
    app.register_blueprint(codeco_bp)

    # Configure Swagger/OpenAPI documentation
    try:
        swagger = Swagger(app)
    except Exception as e:
        logger.warning(f"Could not initialize Swagger: {str(e)}")

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint returning API information."""
        return jsonify({
            "name": "EDI CODECO Generator API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/api/docs"
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "status": "error",
            "message": "Endpoint not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "status": "error",
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

    logger.info("Flask application created and configured")
    return app


# Create app instance for direct execution
app = create_app()

if __name__ == '__main__':
    logger.info(f"Starting EDI CODECO Generator API (debug={config.DEBUG})")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )
