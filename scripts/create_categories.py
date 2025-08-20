from app import create_app, db
from app.models import Category
from config import Config

app = create_app(Config)

def create_categories():
    categories = [
        {
            'name': 'appetizer',
            'display_name': 'Appetizers',
            'description': 'Start your meal with our delicious appetizers',
            'order': 1
        },
        {
            'name': 'main_course',
            'display_name': 'Main Course',
            'description': 'Satisfying main dishes for every palate',
            'order': 2
        },
        {
            'name': 'dessert',
            'display_name': 'Desserts',
            'description': 'Sweet treats to end your meal',
            'order': 3
        },
        {
            'name': 'beverage',
            'display_name': 'Beverages',
            'description': 'Refreshing drinks and beverages',
            'order': 4
        },
        {
            'name': 'snacks',
            'display_name': 'Snacks',
            'description': 'Quick bites and snacks',
            'order': 5
        }
    ]
    
    with app.app_context():
        for cat_data in categories:
            category = Category.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = Category(**cat_data)
                db.session.add(category)
        
        db.session.commit()
        print("Categories created successfully!")

if __name__ == '__main__':
    create_categories()
