from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField, BooleanField, HiddenField, SubmitField
from wtforms.fields import MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
import re

def gmail_email_validator(form, field):
    """Custom validator to ensure email is from Gmail"""
    if not field.data.lower().endswith('@gmail.com'):
        raise ValidationError('Email must be a valid Gmail address (@gmail.com)')

def strong_password_validator(form, field):
    """Custom validator for strong password"""
    password = field.data
    
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character')

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    user_type = SelectField('Login As', choices=[
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('delivery_boy', 'Delivery Boy')
    ], default='customer')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email(), gmail_email_validator])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8), strong_password_validator])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=15)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    role = SelectField('Account Type', choices=[
        ('customer', 'Customer'),
        ('delivery_boy', 'Delivery Boy')
    ], default='customer')
    submit = SubmitField('Create Account')
    user_type = SelectField('Register As', choices=[
        ('customer', 'Customer'),
        ('delivery_boy', 'Delivery Boy')
    ], default='customer')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=50)])

class NutritionalInfoForm(FlaskForm):
    calories_per_serving = FloatField('Calories per Serving', validators=[Optional(), NumberRange(min=0.0)])
    protein_g = FloatField('Protein (g)', validators=[Optional(), NumberRange(min=0.0)])
    carbohydrates_g = FloatField('Carbohydrates (g)', validators=[Optional(), NumberRange(min=0.0)])
    fat_g = FloatField('Fat (g)', validators=[Optional(), NumberRange(min=0.0)])
    fiber_g = FloatField('Fiber (g)', validators=[Optional(), NumberRange(min=0.0)])
    sugar_g = FloatField('Sugar (g)', validators=[Optional(), NumberRange(min=0.0)])
    sodium_mg = FloatField('Sodium (mg)', validators=[Optional(), NumberRange(min=0.0)])
    cholesterol_mg = FloatField('Cholesterol (mg)', validators=[Optional(), NumberRange(min=0.0)])
    serving_size = StringField('Serving Size', validators=[Optional(), Length(max=50)])
    allergens = TextAreaField('Allergens (comma-separated)', validators=[Optional(), Length(max=500)])
    ingredients = TextAreaField('Ingredients', validators=[Optional(), Length(max=1000)])

class FoodItemForm(FlaskForm):
    name = StringField('Food Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', validators=[DataRequired()])
    image = FileField('Food Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only (JPG, JPEG, PNG)')
    ])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=255)])
    is_available = BooleanField('Available')
    preparation_time = IntegerField('Preparation Time (minutes)', 
                                   validators=[Optional(), NumberRange(min=1, max=120)])

    # Nutritional Information Fields
    add_nutrition = BooleanField('Add Nutritional Information')
    calories_per_serving = FloatField('Calories per Serving', validators=[Optional(), NumberRange(min=0.0)])
    protein_g = FloatField('Protein (g)', validators=[Optional(), NumberRange(min=0.0)])
    carbohydrates_g = FloatField('Carbohydrates (g)', validators=[Optional(), NumberRange(min=0.0)])
    fat_g = FloatField('Fat (g)', validators=[Optional(), NumberRange(min=0.0)])
    fiber_g = FloatField('Fiber (g)', validators=[Optional(), NumberRange(min=0.0)])
    sugar_g = FloatField('Sugar (g)', validators=[Optional(), NumberRange(min=0.0)])
    sodium_mg = FloatField('Sodium (mg)', validators=[Optional(), NumberRange(min=0.0)])
    cholesterol_mg = FloatField('Cholesterol (mg)', validators=[Optional(), NumberRange(min=0.0)])
    serving_size = StringField('Serving Size', validators=[Optional(), Length(max=50)])
    allergens = TextAreaField('Allergens (comma-separated)', validators=[Optional(), Length(max=500)])
    ingredients = TextAreaField('Ingredients', validators=[Optional(), Length(max=1000)])

class OrderForm(FlaskForm):
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=500)])

class CartForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, max=10)])
    food_item_id = HiddenField('Food Item ID', validators=[DataRequired()])

class OrderStatusForm(FlaskForm):
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    delivery_boy_id = SelectField('Assign Delivery Boy', validators=[Optional()])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Category', 
                          choices=[('all', 'All Categories'),
                                 ('appetizer', 'Appetizer'), 
                                 ('main_course', 'Main Course'),
                                 ('dessert', 'Dessert'),
                                 ('beverage', 'Beverage'),
                                 ('snacks', 'Snacks')],
                          default='all')
    price_min = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    price_max = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])

class DeliveryBoyRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('bike', 'Motorcycle'),
        ('bicycle', 'Bicycle'),
        ('car', 'Car'),
        ('scooter', 'Scooter')
    ], validators=[DataRequired()])
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=20)])

class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=15)])
    subject_type = SelectField('Subject', choices=[
        ('order', 'Order Related'),
        ('delivery', 'Delivery Issue'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])

class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])

class OTPVerificationForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])


class ReviewForm(FlaskForm):
    rating = SelectField('Rating', 
                        choices=[(5, '5 - Excellent'), 
                                (4, '4 - Very Good'), 
                                (3, '3 - Good'), 
                                (2, '2 - Fair'), 
                                (1, '1 - Poor')], 
                        coerce=int, 
                        validators=[DataRequired()])
    comment = TextAreaField('Write your review', 
                           validators=[Optional(), Length(max=1000)],
                           render_kw={"placeholder": "Share your experience with this dish..."})
    images = MultipleFileField('Upload Photos', 
                              validators=[Optional(), 
                                        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 
                                                  'Images only (JPG, JPEG, PNG, WEBP)')],
                              render_kw={"multiple": True, "accept": ".jpg,.jpeg,.png,.webp"})
    food_item_id = HiddenField('Food Item ID', validators=[DataRequired()])


class EditReviewForm(FlaskForm):
    rating = SelectField('Rating', 
                        choices=[(5, '5 - Excellent'), 
                                (4, '4 - Very Good'), 
                                (3, '3 - Good'), 
                                (2, '2 - Fair'), 
                                (1, '1 - Poor')], 
                        coerce=int, 
                        validators=[DataRequired()])
    comment = TextAreaField('Edit your review', 
                           validators=[Optional(), Length(max=1000)],
                           render_kw={"placeholder": "Update your experience with this dish..."})
    new_images = MultipleFileField('Add New Photos', 
                                  validators=[Optional(), 
                                            FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 
                                                      'Images only (JPG, JPEG, PNG, WEBP)')],
                                  render_kw={"multiple": True, "accept": ".jpg,.jpeg,.png,.webp"})
    remove_images = StringField('Remove Images', 
                               render_kw={"type": "hidden"})  # JSON string of image IDs to remove


class AdminReplyForm(FlaskForm):
    admin_reply = TextAreaField('Admin Reply', 
                               validators=[DataRequired(), Length(max=500)],
                               render_kw={"placeholder": "Write your response to this review...", 
                                        "rows": 4})
    review_id = HiddenField('Review ID', validators=[DataRequired()])


class ReviewModerationForm(FlaskForm):
    is_approved = BooleanField('Approve Review')
    admin_reply = TextAreaField('Admin Reply', 
                               validators=[Optional(), Length(max=500)],
                               render_kw={"placeholder": "Optional response to the customer...", 
                                        "rows": 3})
    action = SelectField('Action', 
                        choices=[('approve', 'Approve'), 
                                ('reject', 'Reject'), 
                                ('reply', 'Reply Only')], 
                        validators=[DataRequired()])


class ReviewFilterForm(FlaskForm):
    rating = SelectField('Filter by Rating', 
                        choices=[('', 'All Ratings'),
                                ('5', '5 Stars'),
                                ('4', '4 Stars'), 
                                ('3', '3 Stars'),
                                ('2', '2 Stars'),
                                ('1', '1 Star')], 
                        default='')
    sort_by = SelectField('Sort By', 
                         choices=[('newest', 'Newest First'),
                                 ('oldest', 'Oldest First'),
                                 ('highest_rating', 'Highest Rating'),
                                 ('lowest_rating', 'Lowest Rating'),
                                 ('most_helpful', 'Most Helpful')], 
                         default='newest')
    verified_only = BooleanField('Verified Purchases Only')
    with_images = BooleanField('Reviews with Images Only')

class OTPVerificationForm(FlaskForm):
    otp = StringField('Verification Code', 
                     validators=[DataRequired(), Length(min=6, max=6, message="OTP must be 6 digits")],
                     render_kw={"placeholder": "Enter 6-digit code", "maxlength": "6", "pattern": "[0-9]{6}"})
    submit = SubmitField('Verify Code')
    resend = SubmitField('Resend Code')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Code')

