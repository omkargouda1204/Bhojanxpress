from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import User, Order, OrderItem, FoodItem, Notification
from app.forms import OrderStatusForm
from app.utils.notification_utils import create_order_status_notification
from app.utils.notification_service import NotificationService
from functools import wraps
import io

delivery_bp = Blueprint('delivery', __name__)

def delivery_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_delivery_boy:
            flash('Access denied. Delivery boys only.', 'error')
            return redirect(url_for('auth.login'))
        
        # Note: Inactive agents can still login and access dashboard
        # They just won't appear in the order assignment list
        # This allows them to view their profile and existing orders
            
        return f(*args, **kwargs)
    return decorated_function

@delivery_bp.route('/notifications-api')
@login_required
@delivery_required
def get_notifications():
    """API endpoint for delivery agent notifications"""
    # Get unread notifications for the current delivery agent
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        'notifications': [
            {
                'id': n.id,
                'message': n.content,
                'type': n.notification_type,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for n in notifications
        ]
    })

@delivery_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
@delivery_required
def mark_notifications_read():
    """Mark all notifications as read for the current delivery agent"""
    try:
        # Get all unread notifications for the current user
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).all()
        
        # Mark each as read
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notifications marked as read'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@delivery_bp.route('/dashboard')
@login_required
@delivery_required
def dashboard():
    """Delivery boy dashboard showing assigned orders and statistics"""
    
    # Check if agent is inactive and show appropriate message
    if not current_user.is_active:
        flash('Your account is currently inactive. You can view your dashboard but will not receive new order assignments. Please contact the administrator for assistance.', 'warning')
    
    # Get assigned orders
    assigned_orders = Order.query.filter_by(
        delivery_boy_id=current_user.id
    ).order_by(Order.created_at.desc()).all()

    # Get pending assignments (orders ready for delivery but not yet delivered)
    pending_orders = Order.query.filter(
        db.or_(
            # Orders ready for pickup but no delivery agent assigned
            db.and_(
                Order.status == 'preparing',
                Order.delivery_boy_id.is_(None)
            ),
            # Orders assigned to this agent but not yet picked up (status not 'delivering' or 'delivered')
            db.and_(
                Order.delivery_boy_id == current_user.id,
                Order.status.in_(['preparing', 'ready'])
            )
        )
    ).order_by(Order.created_at.asc()).limit(10).all()

    # Statistics for today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_delivered_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.delivered_at >= today_start,
        Order.delivered_at <= today_end,
        Order.status == 'delivered'
    ).all()

    def calculate_order_commission(order):
        """Calculate commission for a single order"""
        if order.status == 'delivered':
            commission = order.total_amount * 0.12  # 12% of order amount
        elif order.status in ['returned', 'cancelled']:
            commission = order.total_amount * 0.06  # 6% of order amount
        else:
            commission = 0
        return commission

    today_commission = sum(calculate_order_commission(order) for order in today_delivered_orders)

    # Get all commission eligible orders for dashboard stats
    all_commission_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled'])
    ).all()

    total_commission_earned = sum(calculate_order_commission(order) for order in all_commission_orders)

    # Calculate pending commission (orders not yet paid)
    pending_commission_orders = [order for order in all_commission_orders if not getattr(order, 'commission_paid', False)]
    pending_commission = sum(calculate_order_commission(order) for order in pending_commission_orders)

    # Calculate paid commission
    paid_commission = total_commission_earned - pending_commission

    # Calculate commission by payment method
    cash_orders = [order for order in all_commission_orders if order.payment_method == 'cash_on_delivery']
    cash_commission = sum(calculate_order_commission(order) for order in cash_orders)

    online_orders = [order for order in all_commission_orders if order.payment_method != 'cash_on_delivery']
    online_commission = sum(calculate_order_commission(order) for order in online_orders)

    stats = {
        'total_assigned': len(assigned_orders),
        'today_deliveries': len(today_delivered_orders),
        'pending_deliveries': Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.status.in_(['out_for_delivery', 'confirmed', 'preparing'])
        ).count(),
        'total_earnings': db.session.query(db.func.sum(Order.delivery_charge)).filter(
            Order.delivery_boy_id == current_user.id,
            Order.status == 'delivered'
        ).scalar() or 0,
        'today_commission': today_commission,
        'total_commission_earned': total_commission_earned,
        'pending_commission': pending_commission,
        'paid_commission': paid_commission,
        'cash_commission': cash_commission,
        'online_commission': online_commission
    }

    return render_template('delivery/dashboard.html',
                         assigned_orders=assigned_orders,
                         pending_orders=pending_orders,
                         stats=stats)

@delivery_bp.route('/my-orders')
@login_required
@delivery_required
def my_orders():
    """Display all orders assigned to the current delivery boy with filtering"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    query = Order.query.filter_by(delivery_boy_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('delivery/orders.html', 
                         orders=orders, 
                         status_filter=status_filter,
                         hide_sidebar=True,
                         back_url=url_for('delivery.dashboard'))

# Add alias route for 'orders' to maintain compatibility
@delivery_bp.route('/orders')
@login_required
@delivery_required
def orders():
    """Alias for my_orders to maintain compatibility"""
    return redirect(url_for('delivery.my_orders', **request.args))

@delivery_bp.route('/order/<int:order_id>')
@login_required
@delivery_required
def order_details(order_id):
    """View detailed information about a specific order"""
    order = Order.query.get_or_404(order_id)

    # Check if this order is assigned to the current delivery boy
    if order.delivery_boy_id != current_user.id:
        flash('You can only view orders assigned to you.', 'error')
        return redirect(url_for('delivery.dashboard'))

    return render_template('delivery/order_details.html', 
                         order=order,
                         hide_sidebar=True,
                         back_url=url_for('delivery.my_orders'))

# Auto-assignment removed - Admin now manually assigns orders

@delivery_bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
@delivery_required
def update_order_status(order_id):
    """Update the status of an assigned order"""
    try:
        order = Order.query.get_or_404(order_id)

        # Check if this order is assigned to the current delivery boy
        if order.delivery_boy_id != current_user.id:
            flash('You can only update orders assigned to you.', 'error')
            return redirect(url_for('delivery.dashboard'))

        new_status = request.form.get('status')
        print(f"Received status update request for order {order_id}: {new_status}")
        
        if not new_status:
            flash('Please select a status to update.', 'error')
            return redirect(url_for('delivery.order_details', order_id=order.id))

        # Additional validation - ensure order can be updated
        if order.status in ['delivered', 'cancelled', 'returned']:
            flash('This order has already been finalized and cannot be updated.', 'error')
            return redirect(url_for('delivery.order_details', order_id=order.id))

        old_status = order.status
        
        if new_status == 'out_for_delivery':
            order.status = 'out_for_delivery'
            flash(f'Order #{order.id} is now out for delivery.', 'success')
        elif new_status == 'delivered':
            order.status = 'delivered'
            order.delivered_at = datetime.utcnow()
            # Mark COD as received if it's a COD order
            if order.payment_method == 'cash_on_delivery':
                order.payment_received = True
                order.cod_received = True
                order.cod_collected = True
                order.cod_collection_time = datetime.utcnow()
            flash(f'Order #{order.id} has been marked as delivered.', 'success')
        elif new_status == 'cancelled':
            order.status = 'cancelled'
            order.cancel_reason = request.form.get('cancel_reason', 'Cancelled by delivery agent')
            order.cancelled_at = datetime.utcnow()
            flash(f'Order #{order.id} has been cancelled.', 'success')
        elif new_status == 'returned':
            order.status = 'returned'
            order.return_reason = request.form.get('return_reason', 'Returned by delivery agent')
            order.returned_at = datetime.utcnow()
            flash(f'Order #{order.id} has been marked as returned.', 'success')
        else:
            flash('Invalid status update. Please select a valid status.', 'error')
            return redirect(url_for('delivery.order_details', order_id=order.id))

        print(f"Updating order {order_id} status from {old_status} to {new_status}")
        db.session.commit()
        print(f"Order status updated successfully in database")
        
        # Create order status notification for customer
        try:
            if order.user:
                create_order_status_notification(order.user, order, new_status)
        except Exception as e:
            print(f"Error creating order status notification: {str(e)}")
        
        flash(f'Order status updated successfully to {new_status.replace("_", " ").title()}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order status: {str(e)}', 'error')
        print(f"Error in update_order_status: {str(e)}")  # Debug print
        
    return redirect(url_for('delivery.order_details', order_id=order.id))

@delivery_bp.route('/update_payment_status/<int:order_id>', methods=['POST'])
@login_required
@delivery_required
def update_payment_status(order_id):
    """Update COD payment status for an order"""
    try:
        order = Order.query.get_or_404(order_id)

        # Check if this order is assigned to the current delivery boy
        if order.delivery_boy_id != current_user.id:
            flash('You can only update orders assigned to you.', 'error')
            return redirect(url_for('delivery.dashboard'))

        # Only allow COD orders
        if order.payment_method != 'cash_on_delivery':
            flash('This order is not a Cash on Delivery order.', 'error')
            return redirect(url_for('delivery.order_details', order_id=order.id))

        payment_received = request.form.get('payment_received') == 'true'
        order.payment_received = payment_received
        
        if payment_received:
            order.cod_received = True
            order.cod_collected = True
            order.cod_collection_time = datetime.utcnow()
            flash(f'Payment received for Order #{order.id}.', 'success')
        else:
            order.cod_received = False
            order.cod_collected = False
            order.cod_collection_time = None
            flash(f'Payment status updated for Order #{order.id}.', 'success')

        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating payment status: {str(e)}', 'error')
        print(f"Error in update_payment_status: {str(e)}")  # Debug print

    return redirect(url_for('delivery.order_details', order_id=order.id))

@delivery_bp.route('/earnings')
@login_required
@delivery_required
def earnings():
    """View earnings and delivery statistics"""
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Default to current month if no dates provided
    if not start_date or not end_date:
        today = datetime.utcnow().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Convert to datetime for database queries
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Get delivered orders in date range
    delivered_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status == 'delivered',
        Order.delivered_at >= start_datetime,
        Order.delivered_at <= end_datetime
    ).all()

    def calculate_order_commission(order):
        """Calculate commission for a single order"""
        # Calculate commission as percentage of order amount
        if order.status == 'delivered':
            commission = order.total_amount * 0.12  # 12% of order amount
        elif order.status in ['returned', 'cancelled']:
            commission = order.total_amount * 0.06  # 6% of order amount
        else:
            commission = 0
        return commission

    # Get all orders assigned to this agent (delivered, returned, cancelled)
    commission_eligible_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled']),
        Order.delivered_at >= start_datetime,
        Order.delivered_at <= end_datetime
    ).all()

    # Calculate earnings
    total_deliveries = len(delivered_orders)
    total_earnings = sum(order.delivery_charge or 0 for order in delivered_orders)

    # Calculate total commission earned
    total_commission_earned = sum(calculate_order_commission(order) for order in commission_eligible_orders)

    # Calculate pending commission (commission not yet paid)
    pending_commission_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled']),
        Order.commission_paid == False
    ).all()

    pending_commission = sum(calculate_order_commission(order) for order in pending_commission_orders)

    # Calculate paid commission (orders where commission is already paid)
    paid_commission_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled']),
        Order.commission_paid == True
    ).all()

    paid_commission = sum(calculate_order_commission(order) for order in paid_commission_orders)

    # Calculate cash commission (commission from cash on delivery orders)
    cash_orders = [order for order in commission_eligible_orders if order.payment_method == 'cash_on_delivery']
    cash_commission = sum(calculate_order_commission(order) for order in cash_orders)

    # Calculate online commission (commission from online payments)
    online_orders = [order for order in commission_eligible_orders if order.payment_method != 'cash_on_delivery']
    online_commission = sum(calculate_order_commission(order) for order in online_orders)

    # Calculate COD received (total amount collected from cash on delivery orders)
    cod_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status == 'delivered',
        Order.payment_method == 'cash_on_delivery',
        Order.delivered_at >= start_datetime,
        Order.delivered_at <= end_datetime
    ).all()
    
    total_cod_amount = sum(order.total_amount for order in cod_orders)
    total_cod_orders = len(cod_orders)

    # Daily breakdown
    daily_stats = {}
    for order in commission_eligible_orders:
        day = order.delivered_at.date() if order.delivered_at else order.created_at.date()
        if day not in daily_stats:
            daily_stats[day] = {'count': 0, 'earnings': 0, 'commission': 0, 'cash': 0, 'online': 0}
        daily_stats[day]['count'] += 1
        daily_stats[day]['earnings'] += order.delivery_charge or 0
        commission_amount = calculate_order_commission(order)
        daily_stats[day]['commission'] += commission_amount
        
        # Separate cash and online commission
        if order.payment_method == 'cash_on_delivery':
            daily_stats[day]['cash'] += commission_amount
        else:
            daily_stats[day]['online'] += commission_amount

    return render_template('delivery/earnings.html',
                         delivered_orders=delivered_orders,
                         total_deliveries=total_deliveries,
                         total_earnings=total_earnings,
                         total_commission_earned=total_commission_earned,
                         pending_commission=pending_commission,
                         paid_commission=paid_commission,
                         cash_commission=cash_commission,
                         online_commission=online_commission,
                         pending_commission_orders=pending_commission_orders,
                         daily_stats=daily_stats,
                         start_date=start_date,
                         end_date=end_date,
                         total_cod_amount=total_cod_amount,
                         total_cod_orders=total_cod_orders,
                         total_orders=total_deliveries,
                         hide_sidebar=True,
                         back_url=url_for('delivery.dashboard'))

@delivery_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@delivery_required
def profile():
    """Delivery boy profile page with editable functionality"""
    if request.method == 'POST':
        try:
            print(f"Updating profile for user {current_user.id} ({current_user.username})")
            print(f"Form data: {request.form}")
            
            # Update profile information
            current_user.username = request.form.get('username', current_user.username)
            current_user.phone = request.form.get('phone', current_user.phone)

            # Update password if provided
            new_password = request.form.get('new_password')
            if new_password and new_password.strip():
                current_user.set_password(new_password)

            print(f"Updated values: username={current_user.username}, phone={current_user.phone}")
            db.session.commit()
            print("Profile update successful")
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('delivery.profile'))
        except Exception as e:
            db.session.rollback()
            print(f"Error updating profile: {str(e)}")
            flash(f'Error updating profile: {str(e)}', 'error')

    # Get delivered orders for commission calculation
    delivered_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status == 'delivered'
    ).all()

    def calculate_order_commission_profile(order):
        """Calculate commission for a single order - same logic as earnings page"""
        base_commission = 100  # ₹100 per order base commission
        
        # Calculate percentage commission based on order status
        if order.status == 'delivered':
            percentage_commission = order.total_amount * 0.12  # 12% for delivered orders
        elif order.status in ['returned', 'cancelled']:
            percentage_commission = order.total_amount * 0.06  # 6% for returned/cancelled orders
        else:
            percentage_commission = 0
            
        total_commission = base_commission + percentage_commission
        return total_commission

    # Get all commission eligible orders
    commission_eligible_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled'])
    ).all()

    # Calculate commission details
    total_commission_earned = sum(calculate_order_commission_profile(order) for order in commission_eligible_orders)

    # Get pending commission (commission eligible orders where commission not paid)
    pending_commission_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['delivered', 'returned', 'cancelled']),
        Order.commission_paid == False
    ).all()
    pending_commission = sum(calculate_order_commission_profile(order) for order in pending_commission_orders)

    # Calculate paid commission (total earned - pending)
    paid_commission = total_commission_earned - pending_commission

    # Get overall statistics
    total_deliveries = len(delivered_orders)
    total_earnings = sum(order.delivery_charge or 0 for order in delivered_orders)

    # Today's statistics
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_deliveries = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status == 'delivered',
        Order.delivered_at >= today_start,
        Order.delivered_at <= today_end
    ).count()

    pending_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status.in_(['confirmed', 'preparing', 'out_for_delivery'])
    ).count()

    # Recent orders
    recent_orders = Order.query.filter_by(
        delivery_boy_id=current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()

    stats = {
        'total_deliveries': total_deliveries,
        'today_deliveries': today_deliveries,
        'pending_orders': pending_orders,
        'total_earnings': total_earnings,
        'total_commission_earned': total_commission_earned,
        'pending_commission': pending_commission,
        'paid_commission': paid_commission,
        'member_since': current_user.created_at
    }

    return render_template('delivery/profile.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         hide_sidebar=True,
                         back_url=url_for('delivery.dashboard'))

@delivery_bp.route('/toggle_status', methods=['POST'])
@login_required
@delivery_required
def toggle_status():
    """Toggle delivery agent active/inactive status"""
    try:
        # If it's an AJAX request with JSON data, get status from request
        if request.headers.get('Content-Type') == 'application/json' and request.json:
            new_status = request.json.get('active', False)
            current_user.is_active = new_status
        else:
            # Otherwise toggle the current status
            current_user.is_active = not current_user.is_active
            
        db.session.commit()

        status = "active" if current_user.is_active else "inactive"
        flash(f'Your status has been updated to {status}.', 'success')

        return jsonify({
            'success': True,
            'is_active': current_user.is_active,
            'status': status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update status'
        }), 500

@delivery_bp.route('/update_account_details', methods=['POST'])
@login_required
@delivery_required
def update_account_details():
    """Update delivery agent's account details"""
    try:
        # Use current_user directly instead of querying again
        print(f"Updating account details for user {current_user.id} ({current_user.username})")
        print(f"Form data: {request.form}")
        
        # Update account details
        current_user.bank_name = request.form.get('bank_name', '').strip()
        current_user.account_number = request.form.get('account_number', '').strip()
        current_user.ifsc_code = request.form.get('ifsc_code', '').strip()
        current_user.account_holder_name = request.form.get('account_holder_name', '').strip()
        current_user.upi_id = request.form.get('upi_id', '').strip()
        
        # Also update basic profile info if provided
        if request.form.get('phone'):
            current_user.phone = request.form.get('phone', '').strip()
        if request.form.get('address'):
            current_user.address = request.form.get('address', '').strip()

        # Print values being set
        print(f"Setting bank_name: {current_user.bank_name}")
        print(f"Setting account_number: {current_user.account_number}")
        print(f"Setting ifsc_code: {current_user.ifsc_code}")
        print(f"Setting account_holder_name: {current_user.account_holder_name}")
        print(f"Setting upi_id: {current_user.upi_id}")
        print(f"Setting phone: {current_user.phone}")
        print(f"Setting address: {current_user.address}")
        
        db.session.commit()
        print("Database commit successful")
        flash('Account details updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Account update error: {str(e)}")
        flash('Error updating account details. Please try again.', 'error')

    return redirect(url_for('delivery.profile'))

@delivery_bp.route('/update_profile', methods=['POST'])
@login_required
@delivery_required
def update_profile():
    """Update delivery agent's profile details"""
    try:
        # Get form data
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        # Update user information
        current_user.phone = phone
        current_user.address = address
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Profile update error: {str(e)}")
        flash(f'Error updating profile: {str(e)}', 'error')

    return redirect(url_for('delivery.profile'))

@delivery_bp.route('/api/available_orders')
@login_required
@delivery_required
def api_available_orders():
    """API endpoint to get available orders for assignment"""
    orders = Order.query.filter(
        Order.status == 'preparing',
        Order.delivery_boy_id.is_(None)
    ).order_by(Order.created_at.asc()).limit(20).all()

    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'customer_name': order.customer_name,
            'delivery_address': order.delivery_address,
            'total_amount': order.total_amount,
            'delivery_charge': order.delivery_charge,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'estimated_delivery': order.estimated_delivery.strftime('%Y-%m-%d %H:%M') if order.estimated_delivery else None
        })

    return jsonify(orders_data)


@delivery_bp.route('/download_invoice/<int:order_id>')
@login_required
@delivery_required
def download_invoice(order_id):
    """Download invoice for delivery agent's assigned order"""
    # Ensure the order is assigned to this delivery agent
    order = Order.query.filter_by(
        id=order_id, 
        delivery_boy_id=current_user.id
    ).first_or_404()
    
    order_items = OrderItem.query.filter_by(order_id=order_id).all()

    # Create invoice HTML content with improved formatting
    invoice_html = render_template('components/invoice_template.html',
                                 order=order,
                                 order_items=order_items,
                                 current_date=datetime.now())

    # Create a properly formatted HTML file
    invoice_io = io.BytesIO()
    # Add proper HTML document structure for better rendering
    formatted_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice #{order.id} - BhojanXpress</title>
    <style>
        @media print {{
            body {{ margin: 0; }}
            .invoice-container {{ box-shadow: none; border: none; }}
        }}
    </style>
</head>
<body>
{invoice_html}
</body>
</html>"""
    
    invoice_io.write(formatted_html.encode('utf-8'))
    invoice_io.seek(0)

    filename = f"BhojanXpress_Invoice_{order.id}_{datetime.now().strftime('%Y%m%d')}.html"

    return send_file(
        invoice_io,
        as_attachment=True,
        download_name=filename,
        mimetype='text/html'
    )
    
@delivery_bp.route('/notifications')
@login_required
@delivery_required
def notifications():
    """View for delivery agent notifications dashboard"""
    page = request.args.get('page', 1, type=int)
    filter_by = request.args.get('filter', 'all')
    per_page = 10
    
    # Get actual notifications from the database
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if filter_by == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_by == 'read':
        query = query.filter_by(is_read=True)
    
    # Get paginated results
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Also get recent orders for context
    recent_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.created_at >= (datetime.utcnow() - timedelta(days=7))
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    # Get notification counts for display
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    total_count = Notification.query.filter_by(user_id=current_user.id).count()
    
    return render_template('delivery/notifications.html', 
                          notifications=notifications,
                          recent_orders=recent_orders,
                          unread_count=unread_count,
                          total_count=total_count,
                          filter_by=filter_by,
                          hide_sidebar=True,
                          back_url=url_for('delivery.dashboard'))

@delivery_bp.route('/notifications/api/get')
@login_required
@delivery_required
def get_delivery_notifications():
    """API endpoint to get delivery agent notifications"""
    try:
        # Get new orders assigned to this delivery agent (created in the last 24 hours)
        new_orders = Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24)),
            Order.is_viewed_by_delivery == False
        ).count()

        # Get recent notifications for display
        notifications = []

        # Add recent orders
        recent_orders = Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24))
        ).order_by(Order.created_at.desc()).limit(3).all()
        
        for order in recent_orders:
            notifications.append({
                'type': 'order',
                'title': f'Order #{order.id}',
                'message': f'Pickup from {order.restaurant_name}',
                'timestamp': order.created_at.isoformat(),
                'link': url_for('delivery.order_details', order_id=order.id)
            })
        
        # Example update notification
        notifications.append({
            'type': 'update',
            'title': 'Earnings Updated',
            'message': 'Your earnings have been updated.',
            'timestamp': datetime.utcnow().isoformat(),
            'link': url_for('delivery.earnings')
        })
        
        total_notifications = new_orders
        
        return jsonify({
            'success': True,
            'total_notifications': total_notifications,
            'notifications': notifications
        })
    except Exception as e:
        current_app.logger.error(f"Error getting delivery notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching notifications'
        })

@delivery_bp.route('/notifications/api/mark-all-read', methods=['POST'])
@login_required
@delivery_required
def mark_all_notifications_read():
    """Mark all delivery agent notifications as read"""
    try:
        # Mark all recent orders as viewed
        recent_orders = Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24)),
            Order.is_viewed_by_delivery == False
        ).all()
        
        for order in recent_orders:
            order.is_viewed_by_delivery = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking notifications as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while marking notifications as read'
        })

@delivery_bp.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
@delivery_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification marked as read'})
        else:
            return jsonify({'success': False, 'error': 'Notification not found'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'})

@delivery_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@delivery_required
def mark_all_notifications_as_read():
    """Mark all notifications as read"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'})

@delivery_bp.route('/notifications/<int:notification_id>/delete', methods=['DELETE'])
@login_required
@delivery_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification deleted'})
        else:
            return jsonify({'success': False, 'error': 'Notification not found'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'})

@delivery_bp.route('/notifications/check-new')
@login_required
@delivery_required
def check_new_notifications():
    """Check for new notifications without full page reload"""
    try:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).count()
        
        # Also check for new orders in the last few minutes
        recent_orders = Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.created_at >= (datetime.utcnow() - timedelta(minutes=5)),
            Order.is_viewed_by_delivery == False
        ).count()
        
        has_new = unread_count > 0 or recent_orders > 0
        
        return jsonify({
            'success': True,
            'has_new': has_new,
            'unread_count': unread_count + recent_orders
        })
    except Exception as e:
        current_app.logger.error(f"Error checking new notifications: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'})
