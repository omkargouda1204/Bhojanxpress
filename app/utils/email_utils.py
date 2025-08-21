import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dns.resolver
from flask import current_app, render_template_string
import os
import logging
import requests

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
        import re
        otp_match = re.search(r'<div[^>]*>(\d{6})</div>', html_content)
        if otp_match:
            otp = otp_match.group(1)
            print(f"\n====================")
            print(f"OTP for {to_email}: {otp}")
            print(f"====================\n")

        # Connect to Mailtrap SMTP server with provided credentials
        smtp_server = "sandbox.smtp.mailtrap.io"
        smtp_port = 587
        smtp_username = "b4fc0351feea70"
        smtp_password = "9de6bb1467b7c3"

        current_app.logger.info(f"Connecting to Mailtrap SMTP: {smtp_server}:{smtp_port}")

        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS

        # Login and send
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, to_email, message.as_string())
        server.quit()

        current_app.logger.info(f"Email sent successfully to {to_email} via Mailtrap")
        print(f"Email successfully sent to {to_email} via Mailtrap")

        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False

def send_verification_otp(user):
    """Send verification OTP email"""
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes

    # Update user with OTP
    user.verification_otp = otp
    user.otp_expiry = expiry

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

    # Update user with password reset OTP
    user.password_reset_otp = otp
    user.password_reset_otp_expiry = expiry

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

    # Send email
    return send_email(user.email, subject, html_content)
