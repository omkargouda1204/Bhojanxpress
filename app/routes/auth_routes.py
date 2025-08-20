from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app.utils.helpers import validate_phone_number, flash_errors

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # If already logged in, redirect accordingly
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Debug login attempts
        print(f"Login attempt with username/email: {form.username.data}")
        
        # Try username login first
        user = User.query.filter_by(username=form.username.data).first()
        
        # If not found by username, try email
        if not user and '@' in form.username.data:
            user = User.query.filter_by(email=form.username.data).first()
            print(f"Trying email login: {'Found user' if user else 'No user found'}")
        
        if user:
            print(f"User found: {user.username}, {user.email}, Admin: {user.is_admin}")
            if user.check_password(form.password.data):
                login_user(user, remember=True)
                print(f"Password correct for {user.username}. Login successful.")
                next_page = request.args.get('next')
                
                if user.is_admin:
                    flash(f'Welcome back, Admin {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
                else:
                    flash(f'Welcome back, {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('user.home'))
            else:
                print(f"Password incorrect for {user.username}")
                flash('Invalid password. Please try again.', 'error')
        else:
            print(f"No user found with username/email: {form.username.data}")
            flash('User not found. Please check your username or email.', 'error')
    
    flash_errors(form)
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html', form=form)
        
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)
        
        try:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {e}")

    flash_errors(form)
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('user.home'))
