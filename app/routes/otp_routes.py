from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import re

from app import db
from app.models import User
from app.utils.gmail_otp import generate_otp, send_gmail_otp, is_otp_expired

otp_bp = Blueprint('otp', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Check password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

@otp_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration with OTP verification"""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not email or not username or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/register.html')
        
        is_strong, message = is_strong_password(password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login or use forgot password.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'error')
            return render_template('auth/register.html')
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        
        # Store user data in session temporarily
        session['registration_data'] = {
            'email': email,
            'username': username,
            'password': password,
            'phone': phone,
            'otp': otp,
            'otp_expiry': otp_expiry.isoformat()
        }
        
        # Send OTP email
        subject = "Verify your BhojanXpress account - OTP"
        if send_gmail_otp(email, subject, otp, "verification"):
            flash(f'Verification OTP has been sent to {email}. Please check your email.', 'success')
            return redirect(url_for('otp.verify_otp'))
        else:
            flash('Failed to send verification email. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@otp_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for registration"""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    registration_data = session.get('registration_data')
    if not registration_data:
        flash('No registration in progress. Please register first.', 'error')
        return redirect(url_for('otp.register'))
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        
        if not entered_otp:
            flash('Please enter the OTP', 'error')
            return render_template('auth/verify_otp.html', email=registration_data['email'])
        
        # Check OTP expiry
        otp_expiry = datetime.fromisoformat(registration_data['otp_expiry'])
        if datetime.utcnow() > otp_expiry:
            flash('OTP has expired. Please register again.', 'error')
            session.pop('registration_data', None)
            return redirect(url_for('otp.register'))
        
        # Verify OTP
        if entered_otp == registration_data['otp']:
            # Create user account
            try:
                user = User(
                    email=registration_data['email'],
                    username=registration_data['username'],
                    phone=registration_data.get('phone'),
                    is_verified=True
                )
                user.set_password(registration_data['password'])
                
                db.session.add(user)
                db.session.commit()
                
                # Clear registration data
                session.pop('registration_data', None)
                
                # Login user
                login_user(user)
                
                flash('Account created successfully! Welcome to BhojanXpress!', 'success')
                return redirect(url_for('user.home'))
                
            except Exception as e:
                db.session.rollback()
                flash('Registration failed. Please try again.', 'error')
                return render_template('auth/verify_otp.html', email=registration_data['email'])
        else:
            flash('Invalid OTP. Please try again.', 'error')
            return render_template('auth/verify_otp.html', email=registration_data['email'])
    
    return render_template('auth/verify_otp.html', email=registration_data['email'])

@otp_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    """Resend OTP for registration"""
    registration_data = session.get('registration_data')
    if not registration_data:
        return jsonify({'success': False, 'message': 'No registration in progress'})
    
    # Generate new OTP
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    
    # Update session data
    registration_data['otp'] = otp
    registration_data['otp_expiry'] = otp_expiry.isoformat()
    session['registration_data'] = registration_data
    
    # Send new OTP
    subject = "Verify your BhojanXpress account - New OTP"
    if send_gmail_otp(registration_data['email'], subject, otp, "verification"):
        return jsonify({'success': True, 'message': 'New OTP sent successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send OTP'})

@otp_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password with OTP"""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html')
        
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/forgot_password.html')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with this email address', 'error')
            return render_template('auth/forgot_password.html')
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        
        # Store OTP in user record
        try:
            user.password_reset_otp = otp
            user.password_reset_otp_expiry = otp_expiry
            db.session.commit()
            
            # Send OTP email
            subject = "Reset your BhojanXpress password - OTP"
            if send_gmail_otp(email, subject, otp, "reset"):
                flash(f'Password reset OTP has been sent to {email}. Please check your email.', 'success')
                return redirect(url_for('otp.reset_password', email=email))
            else:
                flash('Failed to send password reset email. Please try again.', 'error')
                return render_template('auth/forgot_password.html')
                
        except Exception as e:
            db.session.rollback()
            flash('Failed to process request. Please try again.', 'error')
            return render_template('auth/forgot_password.html')
    
    return render_template('auth/forgot_password.html')

@otp_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with OTP verification"""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    email = request.args.get('email')
    if not email:
        flash('Invalid reset link', 'error')
        return redirect(url_for('otp.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset link', 'error')
        return redirect(url_for('otp.forgot_password'))
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not entered_otp or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', email=email)
        
        is_strong, message = is_strong_password(new_password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/reset_password.html', email=email)
        
        # Check OTP
        if not user.password_reset_otp or not user.password_reset_otp_expiry:
            flash('No password reset request found. Please try again.', 'error')
            return redirect(url_for('otp.forgot_password'))
        
        if datetime.utcnow() > user.password_reset_otp_expiry:
            flash('OTP has expired. Please request a new password reset.', 'error')
            return redirect(url_for('otp.forgot_password'))
        
        if entered_otp != user.password_reset_otp:
            flash('Invalid OTP. Please try again.', 'error')
            return render_template('auth/reset_password.html', email=email)
        
        # Reset password
        try:
            user.set_password(new_password)
            user.password_reset_otp = None
            user.password_reset_otp_expiry = None
            db.session.commit()
            
            flash('Password has been reset successfully! You can now login with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to reset password. Please try again.', 'error')
            return render_template('auth/reset_password.html', email=email)
    
    return render_template('auth/reset_password.html', email=email)

@otp_bp.route('/resend_reset_otp', methods=['POST'])
def resend_reset_otp():
    """Resend OTP for password reset"""
    email = request.json.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Generate new OTP
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    
    try:
        user.password_reset_otp = otp
        user.password_reset_otp_expiry = otp_expiry
        db.session.commit()
        
        # Send new OTP
        subject = "Reset your BhojanXpress password - New OTP"
        if send_gmail_otp(email, subject, otp, "reset"):
            return jsonify({'success': True, 'message': 'New OTP sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to generate OTP'})