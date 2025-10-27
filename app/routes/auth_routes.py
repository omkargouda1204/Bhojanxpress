from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm, DeliveryBoyRegistrationForm
from app.utils.helpers import validate_phone_number, flash_errors
from app.utils.email_utils import send_verification_otp, send_password_reset_otp, is_email_domain_valid, generate_otp, send_email
from app.utils.notification_utils import create_login_notification
from app.utils.otp_service import OTPService, OTPManager

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
        login_id = form.username.data.strip()
        password = form.password.data.strip()
        remember = bool(request.form.get('remember'))
        
        if not login_id or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html', form=form)
        
        # Debug login attempts
        current_app.logger.info(f"🔐 Login attempt with username/email: {login_id}")
        print(f"🔐 Login attempt with username/email: {login_id}")
        
        # Try to find user by email or username
        user = None
        if '@' in login_id:
            # Looks like email
            user = User.query.filter_by(email=login_id.lower()).first()
            current_app.logger.info(f"Trying email login: {'Found user' if user else 'No user found'}")
            print(f"Trying email login: {'Found user ID=' + str(user.id) if user else 'No user found'}")
        else:
            # Looks like username
            user = User.query.filter_by(username=login_id).first()
            current_app.logger.info(f"Trying username login: {'Found user' if user else 'No user found'}")
            print(f"Trying username login: {'Found user ID=' + str(user.id) if user else 'No user found'}")
        
        if user:
            current_app.logger.info(f"User found: ID={user.id}, Username={user.username}, Email={user.email}")
            print(f"User found: ID={user.id}, Username={user.username}, Email={user.email}, Admin: {user.is_admin}, Delivery: {user.is_delivery_boy}")
            print(f"Password hash: {user.password_hash[:50]}...")

            current_app.logger.info(f"Checking password...")
            print(f"Checking password...")
            password_valid = user.check_password(password)
            current_app.logger.info(f"Password check result: {password_valid}")
            print(f"Password check result: {password_valid}")
            
            if password_valid:
                login_user(user, remember=remember)
                current_app.logger.info(f"✅ Password correct for {user.username}. Login successful.")
                print(f"✅ Password correct for {user.username}. Login successful.")
                
                # Create login notification
                try:
                    create_login_notification(user, request)
                except Exception as e:
                    print(f"Error creating login notification: {str(e)}")
                
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
                current_app.logger.error(f"❌ Password incorrect for {user.username}")
                print(f"❌ Password incorrect for {user.username}")
                flash('Invalid password. Please try again.', 'error')
        else:
            current_app.logger.error(f"❌ No user found with username/email: {login_id}")
            print(f"❌ No user found with username/email: {login_id}")
            flash('User not found. Please check your username/email and try again.', 'error')

    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    # Select template: prefer 3D variant when requested and available
    use_3d = request.args.get('3d', 'true').lower() == 'true'
    template = 'register.html'
    if use_3d:
        try:
            available = current_app.jinja_env.list_templates()
            if 'register.html' in available:
                template = 'register.html'
        except Exception:
            template = 'register.html'
    
    form = RegistrationForm()
    
    # Log form submission and validation
    if request.method == 'POST':
        current_app.logger.info("Registration form submitted")
        print("Registration form submitted")
        current_app.logger.info(f"Form data: username={form.username.data}, email={form.email.data}")
        print(f"Form data: username={form.username.data}, email={form.email.data}")
        
        if not form.validate_on_submit():
            current_app.logger.error(f"Form validation failed: {form.errors}")
            print(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
                    print(f"Validation error - {field}: {error}")
    
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash('⚠️ Username already exists. Please choose a different username.', 'error')
            else:
                flash('⚠️ Email already registered. Please use a different email address or try logging in.', 'error')
            return render_template(template, form=form)

        # Store registration data in session temporarily
        session['pending_registration'] = {
            'username': form.username.data,
            'email': form.email.data,
            'phone': form.phone.data,
            'address': form.address.data,
            'password': form.password.data,  # In production, hash this
            'user_type': form.user_type.data if hasattr(form, 'user_type') else 'customer',
            'role': form.role.data if hasattr(form, 'role') else 'customer'
        }
        
        # Generate and send OTP
        otp = OTPService.generate_otp()
        email_sent = OTPService.send_email_otp(form.email.data, otp, 'registration')
        
        if email_sent:
            # Store OTP in session
            OTPManager.store_otp_in_session(session, form.email.data, otp, 'registration')
            flash('📧 Registration details saved! Please check your email for the 6-digit verification code to complete your registration.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('❌ Failed to send verification email. Please check your email address or try again later.', 'error')
            # Log the error for debugging
            current_app.logger.error(f'Failed to send verification email to {form.email.data}')
            return render_template(template, form=form)

    return render_template(template, form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Handle OTP verification for registration"""
    if 'pending_registration' not in session:
        flash('No pending registration found. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    form = OTPVerificationForm()
    
    if form.validate_on_submit():
        # Get OTP from form - handle both single field and individual digit fields
        if hasattr(form, 'otp') and form.otp.data:
            entered_otp = form.otp.data.strip()
        elif hasattr(form, 'digit1'):
            entered_otp = ''.join([
                form.digit1.data, form.digit2.data, form.digit3.data,
                form.digit4.data, form.digit5.data, form.digit6.data
            ])
        else:
            # Fallback - try to get from request
            entered_otp = request.form.get('otp', '').strip()
        
        current_app.logger.info(f"OTP verification attempt for registration: {entered_otp}")
        
        # Verify OTP
        pending_data = session['pending_registration']
        current_app.logger.info(f"Pending registration data for: {pending_data['email']}")
        
        if OTPManager.verify_otp_from_session(session, pending_data['email'], entered_otp, 'registration'):
            # Create user account
            try:
                current_app.logger.info(f"Creating user account for: {pending_data['username']}")
                
                # Check if username or email already exists
                existing_user = User.query.filter(
                    (User.username == pending_data['username']) |
                    (User.email == pending_data['email'])
                ).first()
                
                if existing_user:
                    if existing_user.username == pending_data['username']:
                        flash('❌ Username already exists. Please go back and choose a different username.', 'error')
                        current_app.logger.error(f"Username already exists: {pending_data['username']}")
                    else:
                        flash('❌ Email already registered. Please go back and use a different email.', 'error')
                        current_app.logger.error(f"Email already exists: {pending_data['email']}")
                    
                    # Clear session and redirect back to registration
                    session.pop('pending_registration', None)
                    OTPManager.clear_otp_from_session(session, 'registration')
                    return redirect(url_for('auth.register'))
                
                user = User(
                    username=pending_data['username'],
                    email=pending_data['email'],
                    phone=pending_data['phone'],
                    address=pending_data['address']
                )
                user.set_password(pending_data['password'])
                
                current_app.logger.info(f"User object created, setting user type...")
                
                # Set user type
                if pending_data.get('role') == 'delivery_boy' or pending_data.get('user_type') == 'delivery_boy':
                    user.is_delivery_boy = True
                
                current_app.logger.info(f"Adding user to database session...")
                db.session.add(user)
                
                current_app.logger.info(f"Committing user to database...")
                db.session.commit()
                
                current_app.logger.info(f"User committed successfully! User ID: {user.id}")
                
                # VERIFICATION: Query the user to confirm it's in the database
                verification_query = User.query.filter_by(email=user.email).first()
                if verification_query:
                    current_app.logger.info(f"✅ VERIFIED: User {user.username} found in database with ID: {verification_query.id}")
                else:
                    current_app.logger.error(f"❌ VERIFICATION FAILED: User {user.username} NOT found in database after commit!")
                
                # Clear session data
                session.pop('pending_registration', None)
                OTPManager.clear_otp_from_session(session, 'registration')
                
                flash('🎉 Registration successful! Your account has been created. You can now login with your credentials.', 'success')
                
                # Log successful registration
                current_app.logger.info(f'New user registered successfully: {user.username} ({user.email})')
                
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error creating user account: {str(e)}')
                current_app.logger.error(f'Exception type: {type(e).__name__}')
                import traceback
                current_app.logger.error(f'Traceback: {traceback.format_exc()}')
                flash('❌ Error creating account. Please try again or contact support if the issue persists.', 'error')
                return render_template('components/verify_otp.html', form=form, email=pending_data['email'])
        else:
            current_app.logger.error(f"OTP verification failed for {pending_data['email']}")
            flash('❌ Invalid or expired OTP. Please check your email and try again, or request a new code.', 'error')
    
    return render_template('components/verify_otp.html', form=form, email=session['pending_registration']['email'])


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for verification"""
    if 'pending_registration' not in session:
        flash('No pending registration found. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    pending_data = session['pending_registration']
    email = pending_data['email']
    
    # Generate new OTP
    otp = OTPService.generate_otp()
    email_sent = OTPService.send_email_otp(email, otp, 'registration')
    
    if email_sent:
        # Update OTP in session
        OTPManager.store_otp_in_session(session, email, otp, 'registration')
        flash('📧 New verification code sent! Please check your email.', 'success')
        return redirect(url_for('auth.verify_otp'))
    else:
        flash('❌ Failed to send OTP. Please try again.', 'error')
        return redirect(url_for('auth.verify_otp'))



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
    
    # Log form submission and validation
    if request.method == 'POST':
        current_app.logger.info("Reset password form submitted")
        print("Reset password form submitted")
        current_app.logger.info(f"Form data: OTP={request.form.get('otp')}, has_password={bool(request.form.get('password'))}")
        print(f"Form data: OTP={request.form.get('otp')}, has_password={bool(request.form.get('password'))}")
        
        if not form.validate_on_submit():
            current_app.logger.error(f"Form validation failed: {form.errors}")
            print(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
    
    if form.validate_on_submit():
        # Debug information
        current_app.logger.info(f"Form submitted with OTP: {form.otp.data}")
        print(f"Form submitted with OTP: {form.otp.data}")

        # Check both database and session for OTP
        session_otp_data = session.get('password_reset_otp', {})
        session_otp = session_otp_data.get('otp')

        # Try to get OTP from user object or session
        try:
            user_otp = user.password_reset_otp
            otp_expiry = user.password_reset_otp_expiry
            using_session = False
            current_app.logger.info(f"Using database OTP: {user_otp}, Expiry: {otp_expiry}")
            print(f"Using database OTP: {user_otp}, Expiry: {otp_expiry}")
        except (AttributeError, Exception) as e:
            # Fallback to session-based OTP
            current_app.logger.info(f"Database OTP not available ({str(e)}), using session OTP: {session_otp}")
            print(f"Database OTP not available ({str(e)}), using session OTP: {session_otp}")
            user_otp = session_otp
            otp_expiry = datetime.fromtimestamp(session_otp_data.get('expiry', 0)) if session_otp_data.get('expiry') else None
            using_session = True

        # Debug information
        current_app.logger.info(f"User OTP (from {'session' if using_session else 'database'}): {user_otp}")
        current_app.logger.info(f"Form OTP: {form.otp.data}")
        current_app.logger.info(f"OTP expiry: {otp_expiry}, Current time: {datetime.utcnow()}")
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
                current_app.logger.info(f"OTP verified successfully, resetting password for user: {user.email}")
                print(f"OTP verified successfully, resetting password for user: {user.email}")
                
                user.set_password(form.password.data)
                current_app.logger.info(f"Password hash generated for user: {user.email}")
                print(f"Password hash generated for user: {user.email}")

                # Clear OTP data
                if not using_session:
                    try:
                        user.password_reset_otp = None
                        user.password_reset_otp_expiry = None
                        current_app.logger.info("Cleared OTP from database")
                    except AttributeError:
                        pass
                else:
                    session.pop('password_reset_otp', None)
                    current_app.logger.info("Cleared OTP from session")

                current_app.logger.info("Committing password change to database...")
                print("Committing password change to database...")
                
                try:
                    db.session.commit()
                    current_app.logger.info(f"✅ Password reset committed successfully for user: {user.email}")
                    print(f"✅ Password reset committed successfully for user: {user.email}")
                    
                    # VERIFICATION: Query the user to confirm password was updated
                    verification_query = User.query.get(user.id)
                    if verification_query and verification_query.check_password(form.password.data):
                        current_app.logger.info(f"✅ VERIFIED: Password updated successfully in database!")
                        print(f"✅ VERIFIED: Password updated successfully in database!")
                    else:
                        current_app.logger.error(f"❌ VERIFICATION FAILED: Password NOT updated in database!")
                        print(f"❌ VERIFICATION FAILED: Password NOT updated in database!")
                        
                except Exception as commit_error:
                    current_app.logger.error(f"❌ Error committing password reset: {commit_error}")
                    print(f"❌ Error committing password reset: {commit_error}")
                    db.session.rollback()
                    flash('❌ Error updating password. Please try again.', 'error')
                    return render_template('components/reset_password.html', form=form, email=user.email)

                # Clear session
                session.pop('user_id_for_password_reset', None)

                flash('✅ Your password has been reset successfully! You can now log in with your new password.', 'success')
                return redirect(url_for('auth.login'))
            else:
                current_app.logger.error(f"OTP expired for user: {user.email}")
                flash('⏰ OTP has expired. Please request a new one.', 'error')
                return redirect(url_for('auth.forgot_password'))
        else:
            if not user_otp:
                current_app.logger.error("No OTP found in database or session")
                print("No OTP found in database or session")
                flash('❌ No OTP found. Please request a password reset again.', 'error')
                return redirect(url_for('auth.forgot_password'))
            elif not form_otp:
                current_app.logger.error("No OTP provided in form")
                print("No OTP provided in form")
                flash('❌ Please enter the OTP.', 'error')
            else:
                current_app.logger.error(f"OTP mismatch: '{user_otp}' != '{form_otp}'")
                print(f"OTP mismatch: '{user_otp}' != '{form_otp}'")
                flash('❌ Invalid OTP. Please check your email and try again.', 'error')

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
