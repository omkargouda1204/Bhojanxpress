"""
Enhanced Notification System for BhojanXpress
Handles creating, sending, and managing notifications for users, agents, and admins
"""

from app import db
from app.models import Notification, User
from datetime import datetime
from flask import current_app
import logging

class NotificationService:
    """Service class to handle all notification operations"""
    
    @staticmethod
    def create_notification(user_id, title, content, notification_type, reference_id=None, image_url=None):
        """
        Create a new notification for a user
        
        Args:
            user_id: ID of the user to receive notification
            title: Notification title
            content: Notification content/message
            notification_type: Type of notification (order_update, review_reply, etc.)
            reference_id: Optional reference to related entity (order_id, review_id, etc.)
            image_url: Optional image URL for visual notifications
            
        Returns:
            Notification object if successful, None if failed
        """
        try:
            # Validate user exists
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f"User {user_id} not found when creating notification")
                return None
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                title=title,
                content=content,
                notification_type=notification_type,
                reference_id=reference_id,
                image_url=image_url,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            current_app.logger.info(f"Notification created for user {user_id}: {title}")
            return notification
            
        except Exception as e:
            current_app.logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def create_order_notification(user_id, order_id, status, title=None, content=None):
        """Create order-related notification"""
        if not title:
            title = f"Order #{order_id} Update"
        
        if not content:
            status_messages = {
                'confirmed': f"Your order #{order_id} has been confirmed and is being prepared.",
                'preparing': f"Your order #{order_id} is being prepared by the restaurant.",
                'ready': f"Your order #{order_id} is ready for pickup/delivery.",
                'out_for_delivery': f"Your order #{order_id} is out for delivery.",
                'delivered': f"Your order #{order_id} has been delivered successfully.",
                'cancelled': f"Your order #{order_id} has been cancelled."
            }
            content = status_messages.get(status, f"Your order #{order_id} status has been updated to {status}.")
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type='order_update',
            reference_id=order_id
        )
    
    @staticmethod
    def create_review_reply_notification(user_id, review_id, admin_name="Admin"):
        """Create notification when admin replies to review"""
        title = "Admin replied to your review"
        content = f"{admin_name} has replied to your review. Check out their response!"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type='review_reply',
            reference_id=review_id
        )
    
    @staticmethod
    def create_delivery_assignment_notification(agent_id, order_id):
        """Create notification for delivery agent assignment"""
        title = f"New Delivery Assignment - Order #{order_id}"
        content = f"You have been assigned to deliver order #{order_id}. Please check the details and prepare for pickup."
        
        return NotificationService.create_notification(
            user_id=agent_id,
            title=title,
            content=content,
            notification_type='order_assignment',
            reference_id=order_id
        )
    
    @staticmethod
    def create_payment_notification(user_id, order_id, amount, status):
        """Create payment-related notification"""
        title = f"Payment {status.title()} - Order #{order_id}"
        
        if status == 'successful':
            content = f"Payment of ₹{amount} for order #{order_id} was successful."
        elif status == 'failed':
            content = f"Payment of ₹{amount} for order #{order_id} failed. Please try again."
        elif status == 'refunded':
            content = f"Refund of ₹{amount} for order #{order_id} has been processed."
        else:
            content = f"Payment status for order #{order_id} has been updated."
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type='payment',
            reference_id=order_id
        )
    
    @staticmethod
    def create_admin_message_notification(user_id, title, content, image_url=None):
        """Create admin message notification"""
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type='admin_message',
            image_url=image_url
        )
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a notification as read"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error marking notification as read: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        try:
            notifications = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).all()
            
            for notification in notifications:
                notification.is_read = True
            
            db.session.commit()
            return len(notifications)
            
        except Exception as e:
            current_app.logger.error(f"Error marking all notifications as read: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete a notification"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                db.session.delete(notification)
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error deleting notification: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_notifications(user_id, filter_type='all', page=1, per_page=20):
        """Get paginated notifications for a user"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if filter_type == 'unread':
                query = query.filter_by(is_read=False)
            elif filter_type == 'read':
                query = query.filter_by(is_read=True)
            
            query = query.order_by(Notification.created_at.desc())
            
            notifications = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return notifications
            
        except Exception as e:
            current_app.logger.error(f"Error getting user notifications: {str(e)}")
            return None
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            current_app.logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """Clean up notifications older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_notifications = Notification.query.filter(
                Notification.created_at < cutoff_date,
                Notification.is_read == True
            ).all()
            
            count = len(old_notifications)
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            
            current_app.logger.info(f"Cleaned up {count} old notifications")
            return count
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up notifications: {str(e)}")
            db.session.rollback()
            return 0


class NotificationTriggers:
    """Class to handle automatic notification triggers"""
    
    @staticmethod
    def on_order_status_change(order):
        """Trigger notification when order status changes"""
        if order.user_id:
            NotificationService.create_order_notification(
                user_id=order.user_id,
                order_id=order.id,
                status=order.status
            )
        
        # Notify delivery agent if assigned
        if order.delivery_agent_id and order.status == 'ready':
            NotificationService.create_notification(
                user_id=order.delivery_agent_id,
                title=f"Order #{order.id} Ready for Pickup",
                content=f"Order #{order.id} is ready for pickup from the restaurant.",
                notification_type='order_update',
                reference_id=order.id
            )
    
    @staticmethod
    def on_delivery_assignment(order):
        """Trigger notification when delivery agent is assigned"""
        if order.delivery_agent_id:
            NotificationService.create_delivery_assignment_notification(
                agent_id=order.delivery_agent_id,
                order_id=order.id
            )
    
    @staticmethod
    def on_review_reply(review, admin_user):
        """Trigger notification when admin replies to review"""
        if review.user_id:
            NotificationService.create_review_reply_notification(
                user_id=review.user_id,
                review_id=review.id,
                admin_name=admin_user.username
            )
    
    @staticmethod
    def on_payment_update(order, payment_status):
        """Trigger notification when payment status updates"""
        if order.user_id and order.total_amount:
            NotificationService.create_payment_notification(
                user_id=order.user_id,
                order_id=order.id,
                amount=order.total_amount,
                status=payment_status
            )