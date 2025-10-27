"""
OTP (One-Time Password) Service for BhojanXpress
Handles OTP generation, sending, and verification for enhanced security
"""

import random
import string
from datetime import datetime, timedelta
from flask import current_app, render_template
from flask_mail import Message
from app import db, mail
import logging
logging.basicConfig(level=logging.INFO)

class OTPService:
    """Service class to handle OTP operations"""
    
    @staticmethod
    def generate_otp(length=6):
        """
        Generate a random OTP
        
        Args:
            length: Length of OTP (default 6)
            
        Returns:
            String: Generated OTP
        """
        digits = string.digits
        return ''.join(random.choice(digits) for _ in range(length))
    
    @staticmethod
    def send_email_otp(email, otp, purpose="registration"):
        """
        Send OTP via email
        
        Args:
            email: Recipient email address
            otp: OTP to send
            purpose: Purpose of OTP (registration, password_reset, etc.)
            
        Returns:
            Boolean: True if sent successfully, False otherwise
        """
        try:
            logging.info(f'Attempting to send {purpose} OTP to {email}')
            
            # Render email template
            try:
                html = render_template('emails/otp_email.html',
                                     otp=otp,
                                     purpose=purpose,
                                     expiry_minutes=10)
            except Exception as template_error:
                logging.error(f'Template rendering error: {str(template_error)}')
                return False
                
            # Create message
            # Create message
            msg = Message(
                subject=f'BhojanXpress - {purpose.title()} Verification Code',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email],
                html=html
            )
            
            # Attempt to send email
            try:
                mail.send(msg)
                logging.info(f'Successfully sent {purpose} OTP to {email}')
                return True
            except Exception as smtp_error:
                logging.error(f'SMTP Error sending to {email}: {str(smtp_error)}')
                return False
                
        except Exception as e:
            logging.error(f'Unexpected error sending OTP: {str(e)}')
            return False
            
            # Create email content
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        overflow: hidden;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                        font-weight: bold;
                    }}
                    .content {{
                        padding: 40px;
                        text-align: center;
                    }}
                    .otp-box {{
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        font-size: 32px;
                        font-weight: bold;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                        letter-spacing: 5px;
                        display: inline-block;
                        min-width: 200px;
                    }}
                    .instructions {{
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                        border-left: 4px solid #667eea;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 14px;
                    }}
                    .warning {{
                        color: #dc3545;
                        font-weight: bold;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🍽️ BhojanXpress</h1>
                        <p>Your Food Delivery Partner</p>
                    </div>
                    
                    <div class="content">
                        <h2>Email Verification Required</h2>
                        <p>Welcome to BhojanXpress! To complete your registration, please use the verification code below:</p>
                        
                        <div class="otp-box">
                            {otp}
                        </div>
                        
                        <div class="instructions">
                            <h4>📝 Instructions:</h4>
                            <ul style="text-align: left; display: inline-block;">
                                <li>Enter this code on the verification page</li>
                                <li>This code is valid for 10 minutes only</li>
                                <li>Do not share this code with anyone</li>
                                <li>If you didn't request this, please ignore this email</li>
                            </ul>
                        </div>
                        
                        <p class="warning">
                            ⚠️ This code will expire in 10 minutes for security reasons.
                        </p>
                        
                        <p>Thank you for choosing BhojanXpress!</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from BhojanXpress.</p>
                        <p>If you have any questions, please contact our support team.</p>
                        <p>© 2025 BhojanXpress. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            BhojanXpress - Email Verification
            
            Welcome to BhojanXpress!
            
            Your verification code is: {otp}
            
            Please enter this code on the verification page to complete your registration.
            
            This code is valid for 10 minutes only.
            
            If you didn't request this verification, please ignore this email.
            
            Thank you for choosing BhojanXpress!
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            current_app.logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def verify_otp(stored_otp, entered_otp, created_at, expiry_minutes=10):
        """
        Verify OTP
        
        Args:
            stored_otp: OTP stored in database/session
            entered_otp: OTP entered by user
            created_at: When OTP was created
            expiry_minutes: OTP expiry time in minutes
            
        Returns:
            dict: {'valid': Boolean, 'message': String}
        """
        try:
            # Check if OTP matches
            if str(stored_otp).strip() != str(entered_otp).strip():
                return {'valid': False, 'message': 'Invalid OTP. Please check and try again.'}
            
            # Check if OTP has expired
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            expiry_time = created_at + timedelta(minutes=expiry_minutes)
            current_time = datetime.utcnow()
            
            if current_time > expiry_time:
                return {'valid': False, 'message': 'OTP has expired. Please request a new one.'}
            
            return {'valid': True, 'message': 'OTP verified successfully.'}
            
        except Exception as e:
            current_app.logger.error(f"Error verifying OTP: {str(e)}")
            return {'valid': False, 'message': 'Error verifying OTP. Please try again.'}
    
    @staticmethod
    def cleanup_expired_otps():
        """
        Clean up expired OTP records (if storing in database)
        This method can be extended to clean database records
        """
        try:
            # This would be implemented if OTPs are stored in database
            # For now, we're using session storage
            current_app.logger.info("OTP cleanup completed")
            return True
        except Exception as e:
            current_app.logger.error(f"Error cleaning up OTPs: {str(e)}")
            return False


class OTPManager:
    """Manager class for handling OTP session operations"""
    
    @staticmethod
    def store_otp_in_session(session, email, otp, purpose="registration"):
        """Store OTP in session"""
        session[f'otp_{purpose}'] = {
            'email': email,
            'otp': otp,
            'created_at': datetime.utcnow().isoformat(),
            'attempts': 0
        }
    
    @staticmethod
    def get_otp_from_session(session, purpose="registration"):
        """Get OTP from session"""
        return session.get(f'otp_{purpose}')
    
    @staticmethod
    def clear_otp_from_session(session, purpose="registration"):
        """Clear OTP from session"""
        session.pop(f'otp_{purpose}', None)
    
    @staticmethod
    def increment_attempts(session, purpose="registration"):
        """Increment OTP verification attempts"""
        otp_data = session.get(f'otp_{purpose}')
        if otp_data:
            otp_data['attempts'] = otp_data.get('attempts', 0) + 1
            session[f'otp_{purpose}'] = otp_data
            return otp_data['attempts']
        return 0
    
    @staticmethod
    def is_max_attempts_reached(session, purpose="registration", max_attempts=3):
        """Check if maximum attempts reached"""
        otp_data = session.get(f'otp_{purpose}')
        if otp_data:
            return otp_data.get('attempts', 0) >= max_attempts
        return False
    
    @staticmethod
    def verify_otp_from_session(session, email, entered_otp, purpose="registration"):
        """Verify OTP from session"""
        from flask import current_app
        
        current_app.logger.info(f"Verifying OTP for {email}, purpose: {purpose}")
        
        otp_data = OTPManager.get_otp_from_session(session, purpose)
        
        if not otp_data:
            current_app.logger.error(f"No OTP data found in session for purpose: {purpose}")
            return False
        
        current_app.logger.info(f"OTP data found: {otp_data}")
        
        # Check if email matches
        stored_email = otp_data.get('email')
        if stored_email != email:
            current_app.logger.error(f"Email mismatch: stored={stored_email}, provided={email}")
            return False
        
        # Check if OTP matches
        stored_otp = str(otp_data.get('otp', '')).strip()
        entered_otp = str(entered_otp).strip()
        
        current_app.logger.info(f"Comparing OTPs: stored={stored_otp}, entered={entered_otp}")
        
        if stored_otp != entered_otp:
            # Increment failed attempts
            OTPManager.increment_attempts(session, purpose)
            current_app.logger.error(f"OTP mismatch: stored={stored_otp}, entered={entered_otp}")
            return False
        
        # Check if OTP has expired (10 minutes)
        created_at_str = otp_data.get('created_at')
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                expiry_time = created_at + timedelta(minutes=10)
                current_time = datetime.utcnow()
                
                current_app.logger.info(f"OTP expiry check: created={created_at}, expiry={expiry_time}, current={current_time}")
                
                if current_time > expiry_time:
                    current_app.logger.error(f"OTP expired: created at {created_at}, expired at {expiry_time}")
                    return False
            except Exception as e:
                current_app.logger.error(f"Error parsing OTP creation time: {e}")
                return False
        
        current_app.logger.info(f"OTP verification successful for {email}")
        return True