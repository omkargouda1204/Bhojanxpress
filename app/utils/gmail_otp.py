import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging
import os
import re

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_gmail_otp(to_email, subject, otp, otp_type="verification"):
    """Send OTP via Gmail SMTP"""
    try:
        # Gmail credentials
        sender_email = "bhojanaxpress@gmail.com"
        sender_password = "akcx hvme pfqp axqq"
        sender_name = "BhojanXpress"

        # Create email template
        if otp_type == "verification":
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f9f9f9;
                        padding: 30px;
                        border: 1px solid #ddd;
                    }}
                    .otp-box {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-size: 32px;
                        font-weight: bold;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px;
                        margin: 20px 0;
                        letter-spacing: 5px;
                    }}
                    .footer {{
                        background: #333;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 0 0 10px 10px;
                        font-size: 12px;
                    }}
                    .warning {{
                        color: #e74c3c;
                        font-weight: bold;
                        margin: 15px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🍽️ BhojanXpress</h1>
                    <p>Email Verification Required</p>
                </div>
                <div class="content">
                    <h2>Welcome to BhojanXpress!</h2>
                    <p>Thank you for registering with BhojanXpress. To complete your registration, please verify your email address using the OTP below:</p>
                    
                    <div class="otp-box">
                        {otp}
                    </div>
                    
                    <p><strong>This OTP is valid for 5 minutes only.</strong></p>
                    
                    <div class="warning">
                        ⚠️ If you didn't create an account with BhojanXpress, please ignore this email.
                    </div>
                    
                    <p>For support, contact us at:</p>
                    <ul>
                        <li>📧 Email: bhojanaxpress@gmail.com</li>
                        <li>📞 Phone: +91 84317 29319</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2025 BhojanXpress. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """
        else:  # password reset
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f9f9f9;
                        padding: 30px;
                        border: 1px solid #ddd;
                    }}
                    .otp-box {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-size: 32px;
                        font-weight: bold;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px;
                        margin: 20px 0;
                        letter-spacing: 5px;
                    }}
                    .footer {{
                        background: #333;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 0 0 10px 10px;
                        font-size: 12px;
                    }}
                    .warning {{
                        color: #e74c3c;
                        font-weight: bold;
                        margin: 15px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🍽️ BhojanXpress</h1>
                    <p>Password Reset Request</p>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset your password for your BhojanXpress account. Use the OTP below to reset your password:</p>
                    
                    <div class="otp-box">
                        {otp}
                    </div>
                    
                    <p><strong>This OTP is valid for 5 minutes only.</strong></p>
                    
                    <div class="warning">
                        ⚠️ If you didn't request a password reset, please ignore this email and ensure your account is secure.
                    </div>
                    
                    <p>For support, contact us at:</p>
                    <ul>
                        <li>📧 Email: bhojanaxpress@gmail.com</li>
                        <li>📞 Phone: +91 84317 29319</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2025 BhojanXpress. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """

        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = to_email

        # Add HTML content
        html_part = MIMEText(html_template, "html")
        message.attach(html_part)

        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Enable TLS encryption
        server.login(sender_email, sender_password)
        
        # Send email
        server.sendmail(sender_email, to_email, message.as_string())
        server.quit()
        
        # Log success
        print(f"\n🎉 OTP Email sent successfully to {to_email}")
        print(f"📧 OTP: {otp}")
        print(f"⏰ Valid for 5 minutes\n")
        
        if current_app:
            current_app.logger.info(f"OTP email sent successfully to {to_email}")
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        error_msg = "Gmail authentication failed. Please check email credentials."
        print(f"❌ {error_msg}")
        if current_app:
            current_app.logger.error(error_msg)
        return False
        
    except smtplib.SMTPRecipientsRefused:
        error_msg = f"Recipient {to_email} was refused by the server."
        print(f"❌ {error_msg}")
        if current_app:
            current_app.logger.error(error_msg)
        return False
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"❌ {error_msg}")
        if current_app:
            current_app.logger.error(error_msg)
        return False

def is_otp_expired(otp_time):
    """Check if OTP is expired (5 minutes validity)"""
    if not otp_time:
        return True
    return datetime.utcnow() > otp_time + timedelta(minutes=5)