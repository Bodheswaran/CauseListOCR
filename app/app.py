"""
Flask application factory and configuration
"""

import logging
from flask import Flask
from flask_cors import CORS

from app.models.database import init_db
from app.api.routes import api_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """Application factory.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.update(config)
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Initialize database
    db_url = app.config.get('DATABASE_URL', 'sqlite:///causelist_ocr.db')
    init_db(db_url)
    logger.info("Database initialized")
    
    # Enable CORS
    CORS(app)
    logger.info("CORS enabled")
    
    # Register blueprints
    app.register_blueprint(api_bp)
    logger.info("API routes registered")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return {"error": "Internal server error"}, 500
    
    logger.info("Flask application created")
    return app
