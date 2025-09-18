from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_delivery_boy = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # Agent status toggle
    is_verified = db.Column(db.Boolean, default=False)
    verification_otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    password_reset_otp = db.Column(db.String(6), nullable=True)
    password_reset_otp_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Account details (for delivery agents)
    bank_name = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(20), nullable=True)
    ifsc_code = db.Column(db.String(15), nullable=True)
    account_holder_name = db.Column(db.String(100), nullable=True)
    upi_id = db.Column(db.String(50), nullable=True)

    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    delivery_assignments = db.relationship('Order', foreign_keys='Order.delivery_boy_id', backref='delivery_boy', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(50), nullable=False)

    # Relationship with food items
    food_items = db.relationship('FoodItem', backref='category_rel', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class NutritionalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False, unique=True)
    calories_per_serving = db.Column(db.Float, nullable=True)
    protein_g = db.Column(db.Float, nullable=True)
    carbohydrates_g = db.Column(db.Float, nullable=True)
    fat_g = db.Column(db.Float, nullable=True)
    fiber_g = db.Column(db.Float, nullable=True)
    sugar_g = db.Column(db.Float, nullable=True)
    sodium_mg = db.Column(db.Float, nullable=True)
    cholesterol_mg = db.Column(db.Float, nullable=True)
    serving_size = db.Column(db.String(50), nullable=True)
    allergens = db.Column(db.Text, nullable=True)  # Comma-separated list
    ingredients = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NutritionalInfo for FoodItem {self.food_item_id}>'

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)  # For storing image data
    image_url = db.Column(db.String(255), nullable=True)  # For external URLs or generated paths
    is_available = db.Column(db.Boolean, default=True)
    preparation_time = db.Column(db.Integer, default=15)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='food_item', lazy=True)
    cart_items = db.relationship('CartItem', backref='food_item', lazy=True)
    nutritional_info = db.relationship('NutritionalInfo', backref='food_item', uselist=False, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='food_item', lazy=True)

    def __repr__(self):
        return f'<FoodItem {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delivery_boy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False, default='Customer')
    delivery_address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='cash')
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    coupon_discount = db.Column(db.Float, default=0.0)
    delivery_charge = db.Column(db.Float, default=0.0)
    gst_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, preparing, out_for_delivery, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    special_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    delivery_started_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    commission_paid = db.Column(db.Boolean, default=False)
    commission_paid_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order

    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Optional link to order
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    review_images = db.relationship('ReviewImage', backref='review', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Review {self.id} - {self.rating} stars>'

class ReviewImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ReviewImage {self.id} for Review {self.review_id}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem {self.id}>'

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float, nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    display_on_home = db.Column(db.Boolean, default=False)  # whether to show coupon on home page
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Coupon {self.code}>'

    def is_valid(self):
        now = datetime.utcnow()
        return (self.is_active and
                self.valid_from <= now <= self.valid_until and
                (self.usage_limit is None or self.used_count < self.usage_limit))

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    alternate_phone = db.Column(db.String(15), nullable=True)
    address_line1 = db.Column(db.String(200), nullable=True)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(50), default='India')

    # Relationship
    user = db.relationship('User', backref=db.backref('profile', uselist=False), lazy=True)

    def __repr__(self):
        return f'<UserProfile {self.user_id}>'

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
