from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=50)])

class FoodItemForm(FlaskForm):
    name = StringField('Food Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', validators=[DataRequired()])
    image = FileField('Food Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only (JPG, JPEG, PNG)')
    ])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=255)])  # Add missing field
    is_available = BooleanField('Available')
    preparation_time = IntegerField('Preparation Time (minutes)', 
                                   validators=[Optional(), NumberRange(min=1, max=120)])

class OrderForm(FlaskForm):
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=500)])

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

class CartForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, max=10)])

class OrderStatusForm(FlaskForm):
    status = SelectField('Status', 
                        choices=[('pending', 'Pending'),
                               ('confirmed', 'Confirmed'),
                               ('preparing', 'Preparing'),
                               ('delivered', 'Delivered'),
                               ('cancelled', 'Cancelled')],
                        validators=[DataRequired()])

class OTPVerificationForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password',
                                   validators=[DataRequired(), EqualTo('password')])
