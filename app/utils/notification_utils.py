from datetime import datetime
from app import db
from app.models import Notification
import platform
import socket


def create_login_notification(user, request=None):
    """Create a login notification for the user with device/browser info."""
    try:
        device_info = "Unknown device"
        browser_info = "Unknown browser"
        ip_address = "Unknown IP"
        
        if request:
            # Get user agent info
            user_agent = request.headers.get('User-Agent', '')
            
            # Extract browser info
            if 'Chrome' in user_agent:
                browser_info = "Chrome"
            elif 'Firefox' in user_agent:
                browser_info = "Firefox"
            elif 'Safari' in user_agent and 'Chrome' not in user_agent:
                browser_info = "Safari"
            elif 'Edge' in user_agent:
                browser_info = "Edge"
            elif 'Opera' in user_agent:
                browser_info = "Opera"
            
            # Extract device info
            if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                if 'Android' in user_agent:
                    device_info = "Android device"
                elif 'iPhone' in user_agent or 'iPad' in user_agent:
                    device_info = "iOS device"
                else:
                    device_info = "Mobile device"
            elif 'Windows' in user_agent:
                device_info = "Windows computer"
            elif 'Macintosh' in user_agent or 'Mac OS X' in user_agent:
                device_info = "Mac computer"
            elif 'Linux' in user_agent:
                device_info = "Linux computer"
            
            # Get IP address
            ip_address = request.remote_addr or request.environ.get('REMOTE_ADDR', 'Unknown IP')
            # Handle proxy headers
            if 'X-Forwarded-For' in request.headers:
                ip_address = request.headers['X-Forwarded-For'].split(',')[0].strip()
            elif 'X-Real-IP' in request.headers:
                ip_address = request.headers['X-Real-IP']
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            title=f"🔐 New Login Detected",
            content=f"You logged in from {device_info} using {browser_info} at {datetime.now().strftime('%B %d, %Y at %I:%M %p')}. IP: {ip_address}",
            notification_type="login_alert",
            reference_id=None,
            image_url=None,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating login notification: {str(e)}")
        return None


def create_order_status_notification(user, order, status, message=None):
    """Create a notification when order status changes."""
    try:
        # Status-specific messages and titles
        status_configs = {
            'confirmed': {
                'title': '✅ Order Confirmed',
                'content': f'Your order #{order.id} has been confirmed! We are preparing your delicious meal.',
                'icon': 'fas fa-check-circle'
            },
            'preparing': {
                'title': '👨‍🍳 Order Being Prepared',
                'content': f'Your order #{order.id} is now being prepared by our chef. Estimated time: 20-30 minutes.',
                'icon': 'fas fa-utensils'
            },
            'out_for_delivery': {
                'title': '🚚 Out for Delivery',
                'content': f'Your order #{order.id} is on its way! The delivery agent will reach you soon.',
                'icon': 'fas fa-truck'
            },
            'delivered': {
                'title': '🎉 Order Delivered',
                'content': f'Your order #{order.id} has been delivered successfully! Thank you for choosing BhojanXpress. Enjoy your meal!',
                'icon': 'fas fa-check-double'
            },
            'cancelled': {
                'title': '❌ Order Cancelled',
                'content': f'Your order #{order.id} has been cancelled. If this was unexpected, please contact our support team.',
                'icon': 'fas fa-times-circle'
            }
        }
        
        config = status_configs.get(status, {
            'title': 'Order Update',
            'content': f'Your order #{order.id} status has been updated.',
            'icon': 'fas fa-info-circle'
        })
        
        # Use custom message if provided
        if message:
            config['content'] = message
        
        notification = Notification(
            user_id=user.id,
            title=config['title'],
            content=config['content'],
            notification_type="order_update",
            reference_id=order.id,
            image_url=None,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating order status notification: {str(e)}")
        return None


def create_admin_message_notification(user, title, message, admin_user=None):
    """Create a notification for admin messages to users."""
    try:
        admin_name = "Admin"
        if admin_user:
            admin_name = admin_user.username or "Admin"
        
        notification = Notification(
            user_id=user.id,
            title=f"📢 Message from {admin_name}: {title}",
            content=message,
            notification_type="admin_message",
            reference_id=admin_user.id if admin_user else None,
            image_url=None,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating admin message notification: {str(e)}")
        return None


def create_delivery_assignment_notification(delivery_user, order):
    """Create a notification when an order is assigned to a delivery agent."""
    try:
        notification = Notification(
            user_id=delivery_user.id,
            title=f"📦 New Delivery Assignment",
            content=f"You have been assigned order #{order.id} for delivery to {order.delivery_address[:50]}{'...' if len(order.delivery_address) > 50 else ''}. Total amount: ₹{order.total_amount:.2f}",
            notification_type="delivery_assignment",
            reference_id=order.id,
            image_url=None,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating delivery assignment notification: {str(e)}")
        return None


def create_review_reply_notification(user, review, reply_content, admin_user=None):
    """Create a notification when admin replies to a review."""
    try:
        admin_name = "Admin"
        if admin_user:
            admin_name = admin_user.username or "Admin"
        
        notification = Notification(
            user_id=user.id,
            title=f"💬 Reply to Your Review",
            content=f"{admin_name} replied to your review: \"{reply_content[:100]}{'...' if len(reply_content) > 100 else ''}\"",
            notification_type="review_reply",
            reference_id=review.id,
            image_url=None,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating review reply notification: {str(e)}")
        return None


def create_promotion_notification(user, title, message, image_url=None):
    """Create a notification for promotions and special offers."""
    try:
        notification = Notification(
            user_id=user.id,
            title=f"🎯 {title}",
            content=message,
            notification_type="promotion",
            reference_id=None,
            image_url=image_url,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    except Exception as e:
        print(f"Error creating promotion notification: {str(e)}")
        return None


def create_bulk_notifications(user_ids, title, message, notification_type="admin_message", admin_user=None):
    """Create notifications for multiple users at once."""
    try:
        notifications = []
        admin_name = "Admin"
        if admin_user:
            admin_name = admin_user.username or "Admin"
        
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=f"📢 {title}" if notification_type == "admin_message" else title,
                content=message,
                notification_type=notification_type,
                reference_id=admin_user.id if admin_user else None,
                image_url=None,
                is_read=False
            )
            notifications.append(notification)
        
        db.session.add_all(notifications)
        db.session.commit()
        
        return notifications
    except Exception as e:
        print(f"Error creating bulk notifications: {str(e)}")
        return []


def get_unread_notification_count(user):
    """Get the count of unread notifications for a user."""
    try:
        return Notification.query.filter_by(user_id=user.id, is_read=False).count()
    except Exception as e:
        print(f"Error getting unread notification count: {str(e)}")
        return 0


def mark_notifications_read(user, notification_ids=None):
    """Mark notifications as read for a user."""
    try:
        query = Notification.query.filter_by(user_id=user.id, is_read=False)
        
        if notification_ids:
            query = query.filter(Notification.id.in_(notification_ids))
        
        count = query.update({'is_read': True})
        db.session.commit()
        
        return count
    except Exception as e:
        print(f"Error marking notifications as read: {str(e)}")
        return 0