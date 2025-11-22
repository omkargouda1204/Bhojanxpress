from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
import os
import glob

# Using PostgreSQL with psycopg2 driver (no special setup needed)

# Ensure no SQLite related modules are loaded
os.environ['SQLALCHEMY_WARN_20'] = '1'

# Remove any SQLite databases to prevent accidental use
def remove_sqlite_databases():
    sqlite_files = glob.glob('*.db') + glob.glob('instance/*.db') + glob.glob('*.sqlite') + glob.glob('*.sqlite3')
    for file in sqlite_files:
        try:
            os.remove(file)
            print(f"Removed SQLite file: {file}")
        except:
            pass

# Call the function to remove SQLite databases
remove_sqlite_databases()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

def create_app():
    flask_app = Flask(__name__, instance_relative_config=False)  # Disable instance folder to prevent SQLite

    # Load configuration from Config class
    from config_new import Config as AppConfig
    flask_app.config.from_object(AppConfig)

    if 'sqlite' in flask_app.config['SQLALCHEMY_DATABASE_URI'].lower():
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:system@localhost/bhojanxpress'
        print("WARNING: SQLite detected in configuration. Forcing MySQL instead.")
    
    # Initialize extensions with flask_app
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)
    mail.init_app(flask_app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register error handlers
    @flask_app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404
        
    @flask_app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Import models outside app context to avoid circular imports
    # Only import from models.py, not models directory
    import app.models
    
    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api_routes import api_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.routes.delivery_routes import delivery_bp
    from app.routes.review_routes import review_bp
    from app.routes.otp_routes import otp_bp

    # Register blueprints
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(user_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(api_bp)
    flask_app.register_blueprint(chatbot_bp)
    flask_app.register_blueprint(delivery_bp, url_prefix='/delivery')
    flask_app.register_blueprint(review_bp, url_prefix='/reviews')
    flask_app.register_blueprint(otp_bp, url_prefix='/otp')
    
    # Register template filters
    from app.utils.template_filters import format_currency, format_datetime, time_ago, nl2br
    flask_app.jinja_env.filters['format_currency'] = format_currency
    flask_app.jinja_env.filters['format_datetime'] = format_datetime
    flask_app.jinja_env.filters['time_ago'] = time_ago
    flask_app.jinja_env.filters['nl2br'] = nl2br
    
    # Error handlers
    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Return the flask_app
    return flask_app
