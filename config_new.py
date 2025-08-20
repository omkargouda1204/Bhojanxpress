import os

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration - MySQL ONLY
    # Using root/system credentials for MySQL connection
    # Format: mysql://username:password@host/dbname
    # Force MySQL connection regardless of environment variable
    db_uri = os.environ.get('DATABASE_URL') or 'mysql://root:system@localhost/bhojanxpress'
    # Ensure we're using MySQL and not SQLite
    if 'sqlite' in db_uri.lower():
        db_uri = 'mysql://root:system@localhost/bhojanxpress'
    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = os.environ.get('SESSION_LIFETIME') or 7200  # 2 hours in seconds
    
    # Mail configuration (for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # Security
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/bhojanxpress_test'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
