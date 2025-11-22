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
    is_active = db.Column(db.Boolean, default=True)
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
    orders = db.relationship('Order', foreign_keys='Order.user_id', backref='customer', lazy=True)
    cart_items = db.relationship('CartItem', foreign_keys='CartItem.user_id', backref='user', lazy=True)
    delivery_assignments = db.relationship('Order', foreign_keys='Order.delivery_boy_id', backref='delivery_boy', lazy=True)
    
    def __init__(self, **kwargs):
        # Handle all standard fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def active(self):
        """Property for backward compatibility"""
        return self.is_active
        
    @active.setter
    def active(self, value):
        """Setter for backward compatibility"""
        self.is_active = value
        
    # Additional explicit property for is_active to ensure it works
    # This helps fix the error: property 'is_active' of 'User' object has no setter
    @property
    def is_active_prop(self):
        """Explicit property for is_active"""
        return self.is_active
        
    @is_active_prop.setter
    def is_active_prop(self, value):
        """Explicit setter for is_active"""
        self.is_active = value

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
    calories = db.Column(db.Float, nullable=True)  # Match existing DB column
    protein = db.Column(db.Float, nullable=True)   # Match existing DB column
    carbohydrates = db.Column(db.Float, nullable=True)  # Match existing DB column
    fat = db.Column(db.Float, nullable=True)       # Match existing DB column
    fiber_g = db.Column(db.Float, nullable=True)
    sugar_g = db.Column(db.Float, nullable=True)
    sodium_mg = db.Column(db.Float, nullable=True)
    cholesterol_mg = db.Column(db.Float, nullable=True)
    serving_size = db.Column(db.String(50), nullable=True)
    allergens = db.Column(db.Text, nullable=True)  # Comma-separated list
    ingredients = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Properties for backward compatibility with form field names
    @property
    def calories_per_serving(self):
        return self.calories
    
    @calories_per_serving.setter
    def calories_per_serving(self, value):
        self.calories = value
        
    @property
    def protein_g(self):
        return self.protein
    
    @protein_g.setter
    def protein_g(self, value):
        self.protein = value
        
    @property
    def carbohydrates_g(self):
        return self.carbohydrates
    
    @carbohydrates_g.setter
    def carbohydrates_g(self, value):
        self.carbohydrates = value
        
    @property
    def fat_g(self):
        return self.fat
    
    @fat_g.setter
    def fat_g(self, value):
        self.fat = value

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
    commission_payment_method = db.Column(db.String(20), nullable=True)  # cash, online
    commission_reference_id = db.Column(db.String(100), nullable=True)  # for online payments
    is_viewed_by_admin = db.Column(db.Boolean, default=False)  # Flag to track if admin has viewed this order
    
    # COD tracking fields
    payment_received = db.Column(db.Boolean, default=False)  # Whether cash payment was received
    cod_received = db.Column(db.Boolean, default=False)  # COD amount collected flag
    cod_collected = db.Column(db.Boolean, default=False)  # COD collection status
    cod_collection_time = db.Column(db.DateTime, nullable=True)  # When COD was collected

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
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('profile', uselist=False), lazy=True)

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
    user = db.relationship('User', foreign_keys=[user_id], backref='ratings')

    def __repr__(self):
        return f'<Rating {self.id}: {self.rating}/5>'

# This duplicate ReviewImage class was removed and merged with the one above
# Related to Rating model - replaced with RatingImage model

class RatingImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey('rating.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # URL for uploaded images
    image_filename = db.Column(db.String(255), nullable=True)  # Original filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    rating = db.relationship('Rating', backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<RatingImage {self.id} for Rating {self.rating_id}>'

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
    admin_user = db.relationship('User', foreign_keys=[replied_by], backref='contact_replies')

    def __repr__(self):
        return f'<ContactMessage {self.id}: {self.subject_type}>'
        
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # review_reply, order_update, admin_message, etc.
    reference_id = db.Column(db.Integer, nullable=True)  # ID of referenced item (review_id, order_id, etc.)
    image_url = db.Column(db.String(255), nullable=True)  # For notifications with images
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.id}: {self.notification_type} for User {self.user_id}>'

# Special offers model - moved from models/special_offers.py
class SpecialOffer(db.Model):
    __tablename__ = 'special_offers'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed, or coupon
    discount_value = db.Column(db.Float, nullable=False)
    min_order_value = db.Column(db.Float, default=0)
    max_discount_value = db.Column(db.Float)
    coupon_code = db.Column(db.String(20))
    image_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    applies_to_category = db.Column(db.String(50))  # specific category or None for all
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)

    def __repr__(self):
        return f'<SpecialOffer {self.id}: {self.title}>'

# Banner model - moved from models/banner.py
class Banner(db.Model):
    __tablename__ = 'banners'
    
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100))
    subtitle = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Banner {self.id}: {self.title}>'

class SiteImage(db.Model):
    __tablename__ = 'site_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True)  # logo, favicon, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteImage {self.id}: {self.category or "Uncategorized"}>'


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=True)  # Admin can moderate reviews
    admin_reply = db.Column(db.Text, nullable=True)  # Admin response to review
    admin_reply_at = db.Column(db.DateTime, nullable=True)
    helpful_count = db.Column(db.Integer, default=0)  # Number of helpful votes
    is_verified_purchase = db.Column(db.Boolean, default=False)  # User bought this item
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    food_item = db.relationship('FoodItem', backref=db.backref('reviews', lazy=True))
    images = db.relationship('ReviewImage', backref='review', lazy=True, cascade='all, delete-orphan')
    helpful_votes = db.relationship('ReviewHelpful', backref='review', lazy=True, cascade='all, delete-orphan')
    
    @property
    def average_rating(self):
        """Calculate average rating for this review's food item"""
        reviews = Review.query.filter_by(food_item_id=self.food_item_id, is_approved=True).all()
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)
    
    @property
    def total_reviews_count(self):
        """Get total number of approved reviews for this food item"""
        return Review.query.filter_by(food_item_id=self.food_item_id, is_approved=True).count()
    
    def is_helpful_by_user(self, user_id):
        """Check if current user marked this review as helpful"""
        return ReviewHelpful.query.filter_by(review_id=self.id, user_id=user_id).first() is not None
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating} stars by User {self.user_id}>'


class ReviewImage(db.Model):
    __tablename__ = 'review_images'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    # Legacy columns (for backward compatibility)
    image_path = db.Column(db.String(255), nullable=False, default='')
    image_name = db.Column(db.String(255), nullable=True)
    image_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # New columns
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def image_url(self):
        """Generate the URL for the review image"""
        return f"/static/uploads/reviews/{self.filename}"

    def __repr__(self):
        return f'<ReviewImage {self.id} for Review {self.review_id}>'


class ReviewHelpful(db.Model):
    __tablename__ = 'review_helpful'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_helpful = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate helpful votes
    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='unique_review_helpful'),)
    
    user = db.relationship('User', backref=db.backref('helpful_votes', lazy=True))
    
    def __repr__(self):
        return f'<ReviewHelpful: User {self.user_id} found Review {self.review_id} helpful>'

class SliderImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)  # New field for subtitle
    image_filename = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)  # For external URLs if needed
    button_text = db.Column(db.String(50), nullable=True, default='ORDER NOW')  # New field for button text
    button_link = db.Column(db.String(200), nullable=True, default='/menu')  # New field for button link
    button_color = db.Column(db.String(20), nullable=True, default='warning')  # New field for button color
    offer_text = db.Column(db.String(50), nullable=True)  # New field for offer/discount text
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SliderImage {self.id}: {self.title}>'

class CancellationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    order = db.relationship('Order', backref='cancellation_requests', foreign_keys=[order_id])
    user = db.relationship('User', backref='cancellation_requests', foreign_keys=[user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<CancellationRequest Order#{self.order_id} - {self.status}>'
