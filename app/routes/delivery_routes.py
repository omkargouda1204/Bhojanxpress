from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import User, Order, OrderItem, FoodItem
from app.forms import OrderStatusForm
from functools import wraps

delivery_bp = Blueprint('delivery', __name__)

def delivery_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_delivery_boy:
            flash('Access denied. Delivery boys only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@delivery_bp.route('/dashboard')
@login_required
@delivery_required
def dashboard():
    """Delivery boy dashboard showing assigned orders and statistics"""
    # Get assigned orders
    assigned_orders = Order.query.filter_by(
        delivery_boy_id=current_user.id
    ).order_by(Order.created_at.desc()).all()

    # Get pending assignments (orders ready for delivery)
    pending_orders = Order.query.filter(
        Order.status == 'preparing',
        Order.delivery_boy_id.is_(None)
    ).order_by(Order.created_at.asc()).limit(10).all()

    # Statistics for today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    stats = {
        'total_assigned': len(assigned_orders),
        'today_deliveries': Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.delivered_at >= today_start,
            Order.delivered_at <= today_end,
            Order.status == 'delivered'
        ).count(),
        'pending_deliveries': Order.query.filter(
            Order.delivery_boy_id == current_user.id,
            Order.status.in_(['out_for_delivery', 'confirmed', 'preparing'])
        ).count(),
        'total_earnings': db.session.query(db.func.sum(Order.delivery_charge)).filter(
            Order.delivery_boy_id == current_user.id,
            Order.status == 'delivered'
        ).scalar() or 0
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

    return render_template('delivery/orders.html', orders=orders, status_filter=status_filter)

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

    return render_template('delivery/order_details.html', order=order)

# Auto-assignment removed - Admin now manually assigns orders

@delivery_bp.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
@delivery_required
def update_order_status(order_id):
    """Update the status of an assigned order"""
    order = Order.query.get_or_404(order_id)

    # Check if this order is assigned to the current delivery boy
    if order.delivery_boy_id != current_user.id:
        flash('You can only update orders assigned to you.', 'error')
        return redirect(url_for('delivery.dashboard'))

    new_status = request.form.get('status')

    if new_status == 'delivered':
        order.status = 'delivered'
        order.delivered_at = datetime.utcnow()
        flash(f'Order #{order.id} has been marked as delivered.', 'success')
    elif new_status == 'out_for_delivery':
        order.status = 'out_for_delivery'
        if not order.delivery_started_at:
            order.delivery_started_at = datetime.utcnow()
        flash(f'Order #{order.id} is now out for delivery.', 'success')
    else:
        flash('Invalid status update.', 'error')
        return redirect(url_for('delivery.order_details', order_id=order.id))

    db.session.commit()
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
        base_commission = 100  # ₹100 per order
        if order.status == 'delivered':
            percentage_commission = order.total_amount * 0.12  # 12% for delivered
        elif order.status in ['returned', 'cancelled']:
            percentage_commission = order.total_amount * 0.06  # 6% for returned/cancelled
        else:
            percentage_commission = 0
        return base_commission + percentage_commission

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
                         end_date=end_date)

@delivery_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@delivery_required
def profile():
    """Delivery boy profile page with editable functionality"""
    if request.method == 'POST':
        try:
            # Update profile information
            current_user.username = request.form.get('name', current_user.username)
            current_user.phone = request.form.get('phone', current_user.phone)

            # Update password if provided
            new_password = request.form.get('new_password')
            if new_password and new_password.strip():
                from werkzeug.security import generate_password_hash
                current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('delivery.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')

    # Get delivered orders for commission calculation
    delivered_orders = Order.query.filter(
        Order.delivery_boy_id == current_user.id,
        Order.status == 'delivered'
    ).all()

    def calculate_order_commission_profile(order):
        """Calculate commission for a single order - same logic as earnings page"""
        base_commission = 100  # ₹100 per order
        if order.status == 'delivered':
            percentage_commission = order.total_amount * 0.12  # 12% for delivered
        elif order.status in ['returned', 'cancelled']:
            percentage_commission = order.total_amount * 0.06  # 6% for returned/cancelled
        else:
            percentage_commission = 0
        return base_commission + percentage_commission

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

    return render_template('delivery/profile.html', stats=stats, recent_orders=recent_orders)

@delivery_bp.route('/toggle_status', methods=['POST'])
@login_required
@delivery_required
def toggle_status():
    """Toggle delivery agent active/inactive status"""
    try:
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
        # Update account details
        current_user.bank_name = request.form.get('bank_name', '').strip()
        current_user.account_number = request.form.get('account_number', '').strip()
        current_user.ifsc_code = request.form.get('ifsc_code', '').strip()
        current_user.account_holder_name = request.form.get('account_holder_name', '').strip()
        current_user.upi_id = request.form.get('upi_id', '').strip()

        db.session.commit()
        flash('Account details updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Account update error: {str(e)}")
        flash('Error updating account details. Please try again.', 'error')

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
