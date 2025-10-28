import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import create_app and db
from app import create_app, db

# Ensure DATABASE_URL is used (before creating app)
database_url = os.environ.get('DATABASE_URL')
app_config = {}
if database_url:
    app_config['SQLALCHEMY_DATABASE_URI'] = database_url

# Create Flask app
flask_app = create_app(config_overrides=app_config)

# Gunicorn needs a callable named 'app'
app = flask_app

# Optional: shell context
@flask_app.shell_context_processor
def make_shell_context():
    from app.models import User, FoodItem, Order, OrderItem, CartItem
    return {
        'db': db,
        'User': User,
        'FoodItem': FoodItem,
        'Order': Order,
        'OrderItem': OrderItem,
        'CartItem': CartItem
    }

# CLI commands for DB/admin
@flask_app.cli.command()
def create_admin():
    from app.models import User
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@bhojanxpress.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    admin = User.query.filter_by(username=admin_username).first()
    if admin:
        print(f'Admin user {admin_username} already exists.')
        return
    admin = User(username=admin_username, email=admin_email, is_admin=True)
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    print(f'Admin user {admin_username} created successfully.')

@flask_app.cli.command()
def init_db():
    from app.models import FoodItem
    db.create_all()
    if FoodItem.query.first():
        print('Database already has data.')
        return
    sample_foods = [
        {'name': 'Margherita Pizza', 'description': 'Classic pizza with fresh mozzarella, tomatoes, and basil', 'price': 299.99, 'category': 'main_course', 'preparation_time': 20},
        {'name': 'Chicken Biryani', 'description': 'Aromatic basmati rice with tender chicken and spices', 'price': 249.99, 'category': 'main_course', 'preparation_time': 30},
        {'name': 'Veg Spring Rolls', 'description': 'Crispy rolls filled with fresh vegetables', 'price': 129.99, 'category': 'appetizer', 'preparation_time': 15},
        {'name': 'Chocolate Brownie', 'description': 'Rich and fudgy chocolate brownie with vanilla ice cream', 'price': 89.99, 'category': 'dessert', 'preparation_time': 10},
        {'name': 'Fresh Lime Soda', 'description': 'Refreshing lime soda with mint', 'price': 49.99, 'category': 'beverage', 'preparation_time': 5},
        {'name': 'Samosa', 'description': 'Crispy pastry filled with spiced potatoes', 'price': 39.99, 'category': 'snacks', 'preparation_time': 10}
    ]
    for food in sample_foods:
        db.session.add(FoodItem(**food))
    db.session.commit()
    print('Database initialized with sample data.')

# For local development only
if __name__ == "__main__":
    flask_app.run(debug=True)
