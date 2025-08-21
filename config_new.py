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
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587  # Changed to TLS port
    MAIL_USE_TLS = True  # Using TLS instead of SSL
    MAIL_USE_SSL = False  # Disabling SSL since we're using TLS
    MAIL_USERNAME = 'bhojanaxpress@gmail.com'
    # Use app password for Gmail - replace this with your actual Gmail app password
    MAIL_PASSWORD = 'btxbezayvyijxpcl'
    EMAIL_PASSWORD = 'btxbezayvyijxpcl'  # Same app password

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
