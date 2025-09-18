from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm, DeliveryBoyRegistrationForm
from app.utils.helpers import validate_phone_number, flash_errors
from app.utils.email_utils import send_verification_otp, send_password_reset_otp, is_email_domain_valid, generate_otp, send_email

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on user type
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_delivery_boy:
            return redirect(url_for('delivery.dashboard'))
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
            print(f"User found: {user.username}, {user.email}, Admin: {user.is_admin}, Delivery: {user.is_delivery_boy}")

            if user.check_password(form.password.data):
                login_user(user, remember=True)
                print(f"Password correct for {user.username}. Login successful.")
                next_page = request.args.get('next')
                
                if user.is_admin:
                    flash(f'Welcome back, Admin {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
                elif user.is_delivery_boy:
                    flash(f'Welcome back, {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('delivery.dashboard'))
                else:
                    flash(f'Welcome back, {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('user.home'))
            else:
                print(f"Password incorrect for {user.username}")
                flash('Invalid password. Please try again.', 'error')
        else:
            print(f"No user found with username/email: {form.username.data}")
            flash('User not found. Please check your username/email and try again.', 'error')

    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)

        # Set user type
        if form.user_type.data == 'delivery_boy':
            user.is_delivery_boy = True

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth_bp.route('/register_delivery_boy', methods=['GET', 'POST'])
def register_delivery_boy():
    """Separate registration form for delivery boys with additional fields"""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    form = DeliveryBoyRegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register_delivery_boy.html', form=form)

        # Create new delivery boy user
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            is_delivery_boy=True
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Delivery boy registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_delivery_boy.html', form=form)

@auth_bp.route('/verify-registration', methods=['GET', 'POST'])
def verify_registration():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    # Check if registration data exists in session
    registration_data = session.get('registration_data')
    registration_otp = session.get('registration_otp')

    if not registration_data or not registration_otp:
        flash('Registration session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))

    # Check if OTP has expired
    otp_expiry = datetime.fromtimestamp(registration_otp['expiry'])
    if otp_expiry < datetime.utcnow():
        flash('OTP has expired. Please register again.', 'error')
        # Clear expired data
        session.pop('registration_data', None)
        session.pop('registration_otp', None)
        return redirect(url_for('auth.register'))

    form = OTPVerificationForm()
    if form.validate_on_submit():
        if form.otp.data == registration_otp['otp']:
            try:
                # Create the user now that OTP is verified - without using is_verified parameter
                user = User(
                    username=registration_data['username'],
                    email=registration_data['email']
                )
                user.set_password(registration_data['password'])

                # Add user to database first
                db.session.add(user)
                db.session.commit()

                # Now try to set is_verified if the attribute exists
                try:
                    user.is_verified = True
                    db.session.commit()
                except Exception as e:
                    current_app.logger.warning(f"Could not set is_verified: {e}")
                    # Continue anyway as this is not critical

                # Clear session data
                session.pop('registration_data', None)
                session.pop('registration_otp', None)

                flash('Email verified and account created successfully! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while creating your account. Please try again.', 'error')
                print(f"User creation error after verification: {e}")
                return redirect(url_for('auth.register'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('verify_registration.html', form=form, email=registration_data['email'])

@auth_bp.route('/resend-registration-otp', methods=['GET'])
def resend_registration_otp():
    # Check if registration data exists in session
    registration_data = session.get('registration_data')

    if not registration_data:
        flash('Registration session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))

    # Generate new OTP
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)

    # Update OTP in session
    session['registration_otp'] = {
        'otp': otp,
        'expiry': expiry.timestamp()
    }

    # Send verification email
    subject = "BhojanXpress - New Verification OTP"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9;">
            <h2 style="color: #FF5722; text-align: center;">New Verification OTP</h2>
            <p>Here is your new verification OTP for BhojanXpress registration:</p>
            <div style="text-align: center; margin: 25px 0;">
                <div style="font-size: 24px; font-weight: bold; letter-spacing: 5px; padding: 10px; background: #FF8C00; color: white; border-radius: 5px; display: inline-block;">{otp}</div>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p style="text-align: center; margin-top: 30px; font-size: 14px; color: #777;">
                &copy; {datetime.utcnow().year} BhojanXpress. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    if send_email(registration_data['email'], subject, html_content):
        flash('A new OTP has been sent to your email.', 'success')
    else:
        flash('Failed to send new OTP. Please try again later.', 'error')

    return redirect(url_for('auth.verify_registration'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Send password reset OTP
            if send_password_reset_otp(user):
                db.session.commit()
                session['user_id_for_password_reset'] = user.id
                flash('Password reset OTP has been sent to your email.', 'success')
                return redirect(url_for('auth.reset_password'))
            else:
                flash('Failed to send password reset email. Please try again later.', 'error')
        else:
            # Don't reveal that the user doesn't exist for security
            flash('If your email is registered, you will receive a password reset OTP.', 'info')
            # Wait a bit to prevent timing attacks
            # In a real application, this should be implemented more securely

    return render_template('components/forgot_password.html', form=form)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    # Check if we have a user_id in session
    user_id = session.get('user_id_for_password_reset')
    if not user_id:
        flash('Password reset session expired. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Debug information
        print(f"Form submitted with OTP: {form.otp.data}")

        # Check both database and session for OTP
        session_otp_data = session.get('password_reset_otp', {})
        session_otp = session_otp_data.get('otp')

        # Try to get OTP from user object or session
        try:
            user_otp = user.password_reset_otp
            otp_expiry = user.password_reset_otp_expiry
            using_session = False
            print(f"Using database OTP: {user_otp}, Expiry: {otp_expiry}")
        except (AttributeError, Exception) as e:
            # Fallback to session-based OTP
            print(f"Database OTP not available ({str(e)}), using session OTP: {session_otp}")
            user_otp = session_otp
            otp_expiry = datetime.fromtimestamp(session_otp_data.get('expiry', 0)) if session_otp_data.get('expiry') else None
            using_session = True

        # Debug information
        print(f"User OTP (from {'session' if using_session else 'database'}): {user_otp}")
        print(f"Form OTP: {form.otp.data}")
        print(f"OTP expiry: {otp_expiry}, Current time: {datetime.utcnow()}")

        # Make sure we're comparing strings
        form_otp = str(form.otp.data).strip()
        if user_otp:
            user_otp = str(user_otp).strip()

        # Check if OTP is valid and not expired
        if user_otp and form_otp and user_otp == form_otp:
            if otp_expiry and otp_expiry > datetime.utcnow():
                # Reset password
                user.set_password(form.password.data)
                print(f"Password reset successful for user: {user.email}")

                # Clear OTP data
                if not using_session:
                    try:
                        user.password_reset_otp = None
                        user.password_reset_otp_expiry = None
                    except AttributeError:
                        pass
                else:
                    session.pop('password_reset_otp', None)

                db.session.commit()

                # Clear session
                session.pop('user_id_for_password_reset', None)

                flash('Your password has been reset successfully! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('OTP has expired. Please request a new one.', 'error')
                return redirect(url_for('auth.resend_reset_otp'))
        else:
            if not user_otp:
                print("No OTP found in database or session")
            elif not form_otp:
                print("No OTP provided in form")
            else:
                print(f"OTP mismatch: '{user_otp}' != '{form_otp}'")
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('components/reset_password.html', form=form, email=user.email)

@auth_bp.route('/resend-reset-otp', methods=['GET'])
def resend_reset_otp():
    user_id = session.get('user_id_for_password_reset')
    if not user_id:
        flash('Password reset session expired. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    # Send new OTP
    if send_password_reset_otp(user):
        db.session.commit()
        flash('A new password reset OTP has been sent to your email.', 'success')
    else:
        flash('Failed to send new OTP. Please try again later.', 'error')

    return redirect(url_for('auth.reset_password'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('user.home'))
