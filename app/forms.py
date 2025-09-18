from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField, BooleanField, HiddenField
from wtforms.fields import MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('Login As', choices=[
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('delivery_boy', 'Delivery Boy')
    ], default='customer')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('Register As', choices=[
        ('customer', 'Customer'),
        ('delivery_boy', 'Delivery Boy')
    ], default='customer')
    phone = StringField('Phone Number', validators=[Optional(), Length(max=15)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=50)])

class NutritionalInfoForm(FlaskForm):
    calories_per_serving = FloatField('Calories per Serving', validators=[Optional(), NumberRange(min=0)])
    protein_g = FloatField('Protein (g)', validators=[Optional(), NumberRange(min=0)])
    carbohydrates_g = FloatField('Carbohydrates (g)', validators=[Optional(), NumberRange(min=0)])
    fat_g = FloatField('Fat (g)', validators=[Optional(), NumberRange(min=0)])
    fiber_g = FloatField('Fiber (g)', validators=[Optional(), NumberRange(min=0)])
    sugar_g = FloatField('Sugar (g)', validators=[Optional(), NumberRange(min=0)])
    sodium_mg = FloatField('Sodium (mg)', validators=[Optional(), NumberRange(min=0)])
    cholesterol_mg = FloatField('Cholesterol (mg)', validators=[Optional(), NumberRange(min=0)])
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
    calories_per_serving = FloatField('Calories per Serving', validators=[Optional(), NumberRange(min=0)])
    protein_g = FloatField('Protein (g)', validators=[Optional(), NumberRange(min=0)])
    carbohydrates_g = FloatField('Carbohydrates (g)', validators=[Optional(), NumberRange(min=0)])
    fat_g = FloatField('Fat (g)', validators=[Optional(), NumberRange(min=0)])
    fiber_g = FloatField('Fiber (g)', validators=[Optional(), NumberRange(min=0)])
    sugar_g = FloatField('Sugar (g)', validators=[Optional(), NumberRange(min=0)])
    sodium_mg = FloatField('Sodium (mg)', validators=[Optional(), NumberRange(min=0)])
    cholesterol_mg = FloatField('Cholesterol (mg)', validators=[Optional(), NumberRange(min=0)])
    serving_size = StringField('Serving Size', validators=[Optional(), Length(max=50)])
    allergens = TextAreaField('Allergens (comma-separated)', validators=[Optional(), Length(max=500)])
    ingredients = TextAreaField('Ingredients', validators=[Optional(), Length(max=1000)])

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[
        ('5', '5 Stars - Excellent'),
        ('4', '4 Stars - Very Good'),
        ('3', '3 Stars - Good'),
        ('2', '2 Stars - Fair'),
        ('1', '1 Star - Poor')
    ], validators=[DataRequired()])
    title = StringField('Review Title', validators=[Optional(), Length(max=200)])
    comment = TextAreaField('Your Review', validators=[Optional(), Length(max=1000)])
    images = MultipleFileField('Photos (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only (JPG, JPEG, PNG)')
    ])
    food_item_id = HiddenField('Food Item ID', validators=[DataRequired()])
    order_id = HiddenField('Order ID', validators=[Optional()])

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
