import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the create_app factory function
from app import create_app, db

# Create Flask application with MySQL config only
flask_app = create_app()

# This is needed for "flask run" command to work
app = flask_app

# Import models after app creation to avoid circular imports
# Only import from models.py, not models directory
import app.models

@flask_app.shell_context_processor
def make_shell_context():
    # Import models inside function to avoid circular imports
    from app.models import User, FoodItem, Order, OrderItem, CartItem
    return {
        'db': db,
        'User': User,
        'FoodItem': FoodItem,
        'Order': Order,
        'OrderItem': OrderItem,
        'CartItem': CartItem
    }

@flask_app.cli.command()
def create_admin():
    """Create admin user."""
    # Import models inside function to avoid circular imports
    from app.models import User
    
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@bhojanxpress.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Check if admin already exists
    admin = User.query.filter_by(username=admin_username).first()
    if admin:
        print(f'Admin user {admin_username} already exists.')
        return
    
    # Create admin user
    admin = User(
        username=admin_username,
        email=admin_email,
        is_admin=True
    )
    admin.set_password(admin_password)
    
    try:
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {admin_username} created successfully.')
    except Exception as e:
        db.session.rollback()
        print(f'Error creating admin user: {str(e)}')

@flask_app.cli.command()
def init_db():
    """Initialize database with sample data."""
    # Import models inside function to avoid circular imports
    from app.models import FoodItem
    
    try:
        # Create tables
        db.create_all()
        
        # Check if food items already exist
        if FoodItem.query.first():
            print('Database already has data.')
            return
        
        # Sample food items
        sample_foods = [
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with fresh mozzarella, tomatoes, and basil',
                'price': 299.99,
                'category': 'main_course',
                'preparation_time': 20
            },
            {
                'name': 'Chicken Biryani',
                'description': 'Aromatic basmati rice with tender chicken and spices',
                'price': 249.99,
                'category': 'main_course',
                'preparation_time': 30
            },
            {
                'name': 'Veg Spring Rolls',
                'description': 'Crispy rolls filled with fresh vegetables',
                'price': 129.99,
                'category': 'appetizer',
                'preparation_time': 15
            },
            {
                'name': 'Chocolate Brownie',
                'description': 'Rich and fudgy chocolate brownie with vanilla ice cream',
                'price': 89.99,
                'category': 'dessert',
                'preparation_time': 10
            },
            {
                'name': 'Fresh Lime Soda',
                'description': 'Refreshing lime soda with mint',
                'price': 49.99,
                'category': 'beverage',
                'preparation_time': 5
            },
            {
                'name': 'Samosa',
                'description': 'Crispy pastry filled with spiced potatoes',
                'price': 39.99,
                'category': 'snacks',
                'preparation_time': 10
            }
        ]
        
        for food_data in sample_foods:
            food_item = FoodItem(**food_data)
            db.session.add(food_item)
        
        db.session.commit()
        print('Database initialized with sample data.')
        
    except Exception as e:
        db.session.rollback()
        print(f'Error initializing database: {str(e)}')

if __name__ == '__main__':
    with flask_app.app_context():
        # Ensure we're using environment DATABASE_URL
        if 'sqlite' in flask_app.config['SQLALCHEMY_DATABASE_URI']:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                flask_app.config['SQLALCHEMY_DATABASE_URI'] = db_url
            
        # Print the database type being used (without credentials)
        db_type = flask_app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]
        print(f"Using database type: {db_type}")
        
        try:
            # Create tables in MySQL database
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error: {str(e)}")
            print("\n\n===== MYSQL CONNECTION ERROR =====")
            print("The application could not connect to MySQL. Please ensure:")
            print("1. MySQL server is running on localhost")
            print("2. A database named 'bhojanxpress' exists")
            print("3. User 'root' has permission to access this database")
            print("4. The password is correct in config_new.py")
            print("5. No SQLite database is being used")
            print("\nTo setup MySQL properly:")
            print("1. Install MySQL if not already installed")
            print("2. Log in to MySQL and create the database:")
            print("   CREATE DATABASE bhojanxpress;")
            print("3. Update the config_new.py with your actual credentials")
            print("   Current URI: " + flask_app.config['SQLALCHEMY_DATABASE_URI'])
            print("==================================\n\n")
            import sys
            sys.exit(1)
    
    # Run the application with debug mode
    flask_app.run(debug=True)
