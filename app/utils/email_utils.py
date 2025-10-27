import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dns.resolver
from flask import current_app, render_template_string, session
import os
import logging
import requests
import re
import traceback

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def is_email_domain_valid(email):
    """Check if the email domain exists"""
    try:
        domain = email.split('@')[1]
        # For development/testing, consider all domains valid
        if current_app.config.get('TESTING') or current_app.config.get('DEBUG'):
            return True

        dns.resolver.resolve(domain, 'MX')
        return True
    except (IndexError, dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return False

def send_email(to_email, subject, html_content):
    """Send email using Mailtrap SMTP for development"""
    try:
        sender_email = current_app.config.get('MAIL_USERNAME', 'bhojanaxpress@gmail.com')
        sender_name = "BhojanXpress"

        current_app.logger.info(f"Attempting to send email to {to_email} from {sender_email}")

        # Create email content
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = to_email

        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Save email to file for backup/debugging
        email_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'dev_emails')
        os.makedirs(email_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{to_email.replace('@', '_at_')}.html"
        filepath = os.path.join(email_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        current_app.logger.info(f"Email saved to file: {filepath}")

        # Extract OTP for console display
        otp_match = re.search(r'<div[^>]*>(\d{6})</div>', html_content)
        if otp_match:
            otp = otp_match.group(1)
            print(f"\n====================")
            print(f"OTP for {to_email}: {otp}")
            print(f"====================\n")

        # Try to send the email through SMTP
        try:
            # Use Gmail SMTP configuration from config
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            smtp_username = current_app.config.get('MAIL_USERNAME', 'bhojanaxpress@gmail.com')
            smtp_password = current_app.config.get('MAIL_PASSWORD', 'wojerowhpteimebv')

            current_app.logger.info(f"SMTP Connection: Server={smtp_server}, Port={smtp_port}, TLS=True, SSL=False")

            # Create SMTP connection with timeout
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            # server.set_debuglevel(1)  # Disable debug output for cleaner logs

            # Try establishing TLS connection
            server.ehlo()
            server.starttls()
            server.ehlo()  # Re-identify ourselves over TLS connection

            # Login and send
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, to_email, message.as_string())
            server.quit()

            current_app.logger.info(f"Email sent successfully to {to_email} via Gmail")
            print(f"Email successfully sent to {to_email} via Gmail")
        except smtplib.SMTPException as smtp_e:
            current_app.logger.error(f"SMTP Error: {str(smtp_e)}")
            print(f"SMTP Error: {str(smtp_e)}")
            # Continue execution - we've already saved the email to file

        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return False

def send_verification_otp(user):
    """Send verification OTP email"""
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes

    # Update user with OTP
    try:
        user.verification_otp = otp
        user.otp_expiry = expiry
    except Exception as e:
        current_app.logger.error(f"Error setting OTP attributes: {e}")
        # Fallback to session storage
        session['registration_otp'] = {
            'otp': otp,
            'expiry': expiry.timestamp()
        }

    # Create email content
    subject = "BhojanXpress - Verify Your Email"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9;">
            <h2 style="color: #FF5722; text-align: center;">Welcome to BhojanXpress!</h2>
            <p>Thank you for registering with BhojanXpress. Please verify your email by entering the OTP below:</p>
            <div style="text-align: center; margin: 25px 0;">
                <div style="font-size: 24px; font-weight: bold; letter-spacing: 5px; padding: 10px; background: #FF8C00; color: white; border-radius: 5px; display: inline-block;">{otp}</div>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't request this verification, please ignore this email.</p>
            <p style="text-align: center; margin-top: 30px; font-size: 14px; color: #777;">
                &copy; {datetime.utcnow().year} BhojanXpress. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    # Send email
    return send_email(user.email, subject, html_content)

def send_password_reset_otp(user):
    """Send password reset OTP email"""
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes

    try:
        # Update user with password reset OTP
        user.password_reset_otp = otp
        user.password_reset_otp_expiry = expiry
        current_app.logger.info(f"Set password reset OTP in database for {user.email}: {otp}")
    except Exception as e:
        current_app.logger.error(f"Error setting password reset OTP attributes: {e}")
        # Fallback to session storage
        from flask import session
        session['password_reset_otp'] = {
            'otp': otp,
            'expiry': expiry.timestamp(),
            'email': user.email
        }
        current_app.logger.info(f"Stored password reset OTP in session for {user.email}: {otp}")

    # Create email content
    subject = "BhojanXpress - Password Reset Request"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9;">
            <h2 style="color: #FF5722; text-align: center;">Password Reset</h2>
            <p>We received a request to reset your password for your BhojanXpress account. Please use the OTP below to complete the password reset:</p>
            <div style="text-align: center; margin: 25px 0;">
                <div style="font-size: 24px; font-weight: bold; letter-spacing: 5px; padding: 10px; background: #FF8C00; color: white; border-radius: 5px; display: inline-block;">{otp}</div>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't request a password reset, please ignore this email or contact our support team.</p>
            <p style="text-align: center; margin-top: 30px; font-size: 14px; color: #777;">
                &copy; {datetime.utcnow().year} BhojanXpress. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    # Print OTP to console for debugging
    print(f"\n====================")
    print(f"PASSWORD RESET OTP for {user.email}: {otp}")
    print(f"====================\n")

    # Send email
    return send_email(user.email, subject, html_content)

def send_refund_notification(user, order):
    """Send refund notification email for cancelled orders with online payments"""

    # Create email content
    subject = f"BhojanXpress - Refund Initiated for Order #{order.id}"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9;">
            <h2 style="color: #FF5722; text-align: center;">Refund Initiated</h2>
            <p>Dear {user.username},</p>
            <p>We're sorry to inform you that your order #{order.id} has been cancelled. A refund has been initiated for your payment.</p>
            
            <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #333;">Refund Details</h3>
                <p><strong>Order ID:</strong> #{order.id}</p>
                <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                <p><strong>Refund Amount:</strong> ₹{order.total_amount:.2f}</p>
                <p><strong>Payment Method:</strong> {order.payment_method.replace('_', ' ').title()}</p>
                <p><strong>Refund Status:</strong> Initiated</p>
                <p><strong>Expected Refund Time:</strong> 5-7 business days</p>
            </div>
            
            <p>The refund amount will be credited back to your original payment method. Please note that it may take 5-7 business days for the refund to reflect in your account, depending on your bank's processing time.</p>
            <p>If you have any questions about your refund, please contact our customer support team.</p>
            <p>Thank you for your understanding.</p>
            
            <p style="text-align: center; margin-top: 30px; font-size: 14px; color: #777;">
                &copy; {datetime.utcnow().year} BhojanXpress. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    # Send email
    return send_email(user.email, subject, html_content)
