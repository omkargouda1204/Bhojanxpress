from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import pymysql
import os
import glob

# Use PyMySQL as MySQL driver
pymysql.install_as_MySQLdb()

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

def create_app():
    app = Flask(__name__, instance_relative_config=False)  # Disable instance folder to prevent SQLite

    # Load configuration from Config class
    from config_new import Config as AppConfig
    app.config.from_object(AppConfig)

    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:system@localhost/bhojanxpress'
        print("WARNING: SQLite detected in configuration. Forcing MySQL instead.")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Import models to ensure they are registered with SQLAlchemy
    from app import models

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.utils.template_filters import template_filters

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(template_filters)

    return app
