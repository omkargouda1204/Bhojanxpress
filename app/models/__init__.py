from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from datetime import datetime

# Simple re-export of models to avoid circular imports
# All actual model definitions are in the main models.py file

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_delivery_boy = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # String category name
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # Foreign key reference
    image_data = db.Column(db.LargeBinary, nullable=True)  # For storing image data
    image_url = db.Column(db.String(255), nullable=True)  # For external URLs
    image_path = db.Column(db.String(255))  # Keep existing field for compatibility
    is_available = db.Column(db.Boolean, default=True)
    preparation_time = db.Column(db.Integer, default=15)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FoodItem {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    food_item = db.relationship('FoodItem', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delivery_boy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20), nullable=False)
    payment_received = db.Column(db.Boolean, default=False)  # COD payment tracking
    subtotal = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0)
    coupon_discount = db.Column(db.Float, default=0)
    delivery_charge = db.Column(db.Float, default=0)
    gst_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)  # Added this field
    estimated_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Commission fields
    commission_amount = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=12.0)  # 12% commission
    commission_paid = db.Column(db.Boolean, default=False)
    commission_paid_at = db.Column(db.DateTime, nullable=True)
    
    # COD and Status tracking fields
    cod_received = db.Column(db.Boolean, default=False)
    cod_amount = db.Column(db.Float, default=0.0)
    cod_collected = db.Column(db.Boolean, default=False)
    cod_collection_time = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.Text, nullable=True)
    return_reason = db.Column(db.Text, nullable=True)

    # Relationships
    customer = db.relationship('User', foreign_keys=[user_id], backref='orders')
    delivery_boy = db.relationship('User', foreign_keys=[delivery_boy_id], backref='assigned_orders')
    
    def calculate_commission(self):
        """Calculate commission based on order total and commission rate"""
        if self.total_amount and self.commission_rate:
            # Commission is calculated per 100 rupees
            commission_base = self.total_amount / 100
            return round(commission_base * self.commission_rate, 2)
        return 0.0
    
    def update_commission(self):
        """Update commission amount based on current total and rate"""
        self.commission_amount = self.calculate_commission()
        
    @property
    def order_items(self):
        """Provides compatibility with old code expecting order_items"""
        return self.items.all()

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    order = db.relationship('Order', backref=db.backref('items', lazy='dynamic'))
    food_item = db.relationship('FoodItem')

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(200))
    discount_type = db.Column(db.String(20), nullable=False)  # percentage or fixed
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    display_on_home = db.Column(db.Boolean, default=False)  # Admin permission to display on home page
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Add this missing field

    def is_valid(self):
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with food items
    food_items = db.relationship('FoodItem', backref='category_rel', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    alternate_phone = db.Column(db.String(20))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='profile')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='ratings')

    def __repr__(self):
        return f'<Rating {self.id}: {self.rating}/5>'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    subject_type = db.Column(db.String(50), nullable=False)  # order, delivery, feedback, other
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    admin_reply = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)
    replied_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    admin_user = db.relationship('User', backref='contact_replies')

    def __repr__(self):
        return f'<ContactMessage {self.id}: {self.subject_type}>'

class ReviewImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey('rating.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # URL for uploaded images
    image_filename = db.Column(db.String(255), nullable=True)  # Original filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    rating = db.relationship('Rating', backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ReviewImage {self.id} for Rating {self.rating_id}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='reviews')
    food_item = db.relationship('FoodItem', backref='reviews')

    def __repr__(self):
        return f'<Review {self.id}: {self.rating}/5>'

class NutritionalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    serving_size = db.Column(db.String(50))
    calories = db.Column(db.Float)
    fat = db.Column(db.Float)
    carbohydrates = db.Column(db.Float)
    protein = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    food_item = db.relationship('FoodItem', backref='nutritional_info', uselist=False)

    def __repr__(self):
        return f'<NutritionalInfo for FoodItem {self.food_item_id}>'
