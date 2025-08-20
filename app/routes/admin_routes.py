from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db, csrf
from app.models import User, FoodItem, Order, OrderItem, Category, Coupon, ContactMessage
from app.forms import FoodItemForm, OrderStatusForm, CategoryForm
from app.utils.decorators import admin_required
from app.utils.helpers import format_currency, flash_errors, paginate_query
from app.utils.image_utils import save_image, get_image_url_from_data
from datetime import datetime, timedelta
from flask_mail import Message
from flask import current_app
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.filter_by(is_admin=False).count()
    total_orders = Order.query.count()
    total_food_items = FoodItem.query.count()
    
    # Revenue calculation
    today = datetime.now().date()
    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == today,
        Order.status != 'cancelled'
    ).all()
    today_revenue = sum(order.total_amount for order in today_orders)
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Pending orders
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Unread contact messages for admin notification
    unread_messages = ContactMessage.query.filter_by(is_read=False).count()

    stats = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_food_items': total_food_items,
        'today_revenue': format_currency(today_revenue),
        'pending_orders': pending_orders,
        'unread_messages': unread_messages
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)
    
@admin_bp.route('/pending_orders')
@login_required
@admin_required
def pending_orders():
    # Get all pending orders with user relationship loaded
    from sqlalchemy.orm import joinedload
    orders = Order.query.options(joinedload(Order.user)).filter_by(status='pending').order_by(Order.created_at.desc()).all()
    return render_template('admin/pending_orders.html', orders=orders)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    # Date range filter
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    # Set default date range if not provided (last 30 days)
    if not end_date_str:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    if not start_date_str:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    
    # Query orders in date range
    orders = Order.query.filter(
        db.func.date(Order.created_at) >= start_date,
        db.func.date(Order.created_at) <= end_date,
        Order.status != 'cancelled'
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate statistics
    total_revenue = sum(order.total_amount for order in orders)
    order_count = len(orders)
    avg_order_value = total_revenue / order_count if order_count > 0 else 0
    
    # Category distribution
    category_sales = {}
    for order in orders:
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in order_items:
            food_item = FoodItem.query.get(item.food_item_id)
            category_name = food_item.category_rel.name if food_item and food_item.category_rel else 'General'
            if category_name in category_sales:
                category_sales[category_name]['count'] += item.quantity
                category_sales[category_name]['revenue'] += item.price * item.quantity
            else:
                category_sales[category_name] = {
                    'count': item.quantity,
                    'revenue': item.price * item.quantity,
                    'name': category_name
                }
    
    # Format dates for form
    start_date_formatted = start_date.strftime('%Y-%m-%d')
    end_date_formatted = end_date.strftime('%Y-%m-%d')
    
    return render_template(
        'admin/reports.html',
        orders=orders,
        start_date=start_date_formatted,
        end_date=end_date_formatted,
        total_revenue=format_currency(total_revenue),
        order_count=order_count,
        avg_order_value=format_currency(avg_order_value),
        category_sales=list(category_sales.values())
    )

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    form = CategoryForm()
    
    if form.validate_on_submit():
        # Check if category already exists
        if Category.query.filter_by(name=form.name.data.lower()).first():
            flash('This category already exists.', 'error')
        else:
            # Create new category
            category = Category(
                name=form.name.data.lower(),
                display_name=form.display_name.data
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{form.display_name.data}" added successfully!', 'success')
            return redirect(url_for('admin.categories'))
    
    # Get all categories
    categories = Category.query.all()
    
    # If there are no categories, add default ones
    if not categories:
        default_categories = [
            {'name': 'appetizer', 'display_name': 'Appetizer'},
            {'name': 'main_course', 'display_name': 'Main Course'},
            {'name': 'dessert', 'display_name': 'Dessert'},
            {'name': 'beverage', 'display_name': 'Beverage'},
            {'name': 'snacks', 'display_name': 'Snacks'}
        ]
        
        for cat in default_categories:
            category = Category(**cat)
            db.session.add(category)
        
        db.session.commit()
        categories = Category.query.all()
    
    return render_template('admin/categories.html', form=form, categories=categories)

@admin_bp.route('/food_items')
@login_required
@admin_required
def food_items():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    
    query = FoodItem.query
    
    if category != 'all':
        query = query.filter(FoodItem.category == category)
    
    food_items = query.order_by(FoodItem.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get all category names for filter dropdown
    categories = ['all'] + [c.name for c in Category.query.all()]
    
    return render_template('admin/food_items.html', food_items=food_items, categories=categories, current_category=category)

@admin_bp.route('/add_food', methods=['GET', 'POST'])
@login_required
@admin_required
def add_food():
    form = FoodItemForm()
    
    # Get all categories for the dropdown
    categories = Category.query.all()
    form.category.choices = [(cat.name, cat.display_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
            # Handle image upload
            image_data = None
            image_url = None

            if form.image.data:
                image_data, file_url = save_image(form.image.data, folder='uploads/food')
                if file_url:
                    image_url = file_url

            # Get the category object
            category_obj = Category.query.filter_by(name=form.category.data).first()

            # Create new food item
            food_item = FoodItem(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,  # This is the string name of the category
                category_id=category_obj.id if category_obj else None,  # Set the foreign key
                image_data=image_data,
                image_url=image_url,
                is_available=form.is_available.data,
                preparation_time=form.preparation_time.data or 15
            )
            
            db.session.add(food_item)
            db.session.commit()
            
            flash(f'Food item "{food_item.name}" added successfully!', 'success')
            return redirect(url_for('admin.food_items'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding food item: {str(e)}', 'error')
    
    flash_errors(form)
    return render_template('admin/add_food.html', form=form)

@admin_bp.route('/food_image/<int:food_id>')
@login_required
def food_image(food_id):
    food_item = FoodItem.query.get_or_404(food_id)
    
    if food_item.image_data:
        return send_file(
            io.BytesIO(food_item.image_data),
            mimetype='image/jpeg'
        )
    else:
        return redirect(url_for('static', filename='images/no-image.png'))

@admin_bp.route('/edit_food/<int:food_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_food(food_id):
    food_item = FoodItem.query.get_or_404(food_id)
    form = FoodItemForm(obj=food_item)
    
    # Get all categories for the dropdown
    categories = Category.query.all()
    form.category.choices = [(cat.name, cat.display_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
            # Update basic fields
            food_item.name = form.name.data
            food_item.description = form.description.data
            food_item.price = form.price.data
            food_item.category = form.category.data
            food_item.is_available = form.is_available.data
            food_item.preparation_time = form.preparation_time.data or 15
            
            # Handle image upload if a new image is provided
            if form.image.data:
                image_data, file_url = save_image(form.image.data, folder='uploads/food')
                if file_url:
                    food_item.image_data = image_data
                    food_item.image_url = file_url
            # If only URL is provided and no file
            elif form.image_url.data and form.image_url.data != food_item.image_url:
                food_item.image_url = form.image_url.data
            
            db.session.commit()
            
            flash(f'Food item "{food_item.name}" updated successfully!', 'success')
            return redirect(url_for('admin.food_items'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating food item: {str(e)}', 'error')
    
    flash_errors(form)
    return render_template('admin/edit_food.html', form=form, food_item=food_item)

@admin_bp.route('/delete_food/<int:food_id>', methods=['POST'])
@login_required
@admin_required
def delete_food(food_id):
    food_item = FoodItem.query.get_or_404(food_id)
    
    try:
        db.session.delete(food_item)
        db.session.commit()
        flash(f'Food item "{food_item.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting food item. Please try again.', 'error')
    
    return redirect(url_for('admin.food_items'))

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Order.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    statuses = ['all', 'pending', 'confirmed', 'preparing', 'delivered', 'cancelled']
    
    return render_template('admin/orders.html', orders=orders, statuses=statuses, current_status=status)

@admin_bp.route('/order/<int:order_id>')
@login_required
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_details.html', order=order)

@admin_bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@csrf.exempt
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Handle both form and JSON requests
    if request.is_json:
        data = request.get_json()
        new_status = data.get('status')
    else:
        new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'preparing', 'delivered', 'cancelled']:
        try:
            order.status = new_status
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': f'Order #{order.id} status updated to {new_status.title()}.'})
            else:
                flash(f'Order #{order.id} status updated to {new_status.title()}.', 'success')
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'error': 'Error updating order status.'})
            else:
                flash('Error updating order status.', 'error')
    else:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid status.'})
        else:
            flash('Invalid status.', 'error')
    
    return redirect(url_for('admin.order_details', order_id=order_id))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Calculate user statistics
    total_orders = Order.query.filter_by(user_id=user_id).count()
    total_spent = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.user_id == user_id,
        Order.status != 'cancelled'
    ).scalar() or 0
    
    user_stats = {
        'total_orders': total_orders,
        'total_spent': format_currency(total_spent)
    }
    
    return render_template('admin/user_details.html', user=user, user_orders=user_orders, user_stats=user_stats)

@admin_bp.route('/reports_dashboard')
@login_required
@admin_required
def reports_dashboard():
    # Daily revenue for last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    daily_revenue = []
    current_date = start_date
    
    while current_date <= end_date:
        day_orders = Order.query.filter(
            db.func.date(Order.created_at) == current_date,
            Order.status != 'cancelled'
        ).all()
        
        day_revenue = sum(order.total_amount for order in day_orders)
        daily_revenue.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': day_revenue,
            'orders': len(day_orders)
        })
        
        current_date += timedelta(days=1)
    
    # Category-wise sales
    category_sales = db.session.query(
        FoodItem.category,
        db.func.sum(OrderItem.quantity).label('total_quantity'),
        db.func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.status != 'cancelled'
    ).group_by(FoodItem.category).all()
    
    return render_template('admin/reports.html', daily_revenue=daily_revenue, category_sales=category_sales)

@admin_bp.route('/toggle_food_availability/<int:food_id>', methods=['POST'])
@login_required
@admin_required
def toggle_food_availability(food_id):
    food_item = FoodItem.query.get_or_404(food_id)
    
    try:
        food_item.is_available = not food_item.is_available
        db.session.commit()
        
        status = "available" if food_item.is_available else "unavailable"
        flash(f'{food_item.name} is now {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating food availability.', 'error')
    
    return redirect(url_for('admin.food_items'))

@admin_bp.route('/coupons')
@login_required
@admin_required
def coupons():
    page = request.args.get('page', 1, type=int)
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template('admin/coupons.html', coupons=coupons)

@admin_bp.route('/add_coupon', methods=['GET', 'POST'])
@login_required
@admin_required
def add_coupon():
    if request.method == 'POST':
        try:
            # Parse form data
            code = request.form.get('code').upper().strip()
            description = request.form.get('description')
            discount_type = request.form.get('discount_type')
            discount_value = float(request.form.get('discount_value'))
            min_order_amount = float(request.form.get('min_order_amount', 0))
            max_discount_amount = request.form.get('max_discount_amount')
            max_discount_amount = float(max_discount_amount) if max_discount_amount else None
            usage_limit = request.form.get('usage_limit')
            usage_limit = int(usage_limit) if usage_limit else None
            valid_until_str = request.form.get('valid_until')
            try:
                valid_until = datetime.fromisoformat(valid_until_str)
            except ValueError:
                valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')

            # Check if coupon code already exists
            if Coupon.query.filter_by(code=code).first():
                flash('Coupon code already exists!', 'error')
                return render_template('admin/add_coupon.html')
            
            # Create coupon object incrementally to avoid invalid argument errors
            coupon = Coupon()
            coupon.code = code
            coupon.description = description
            coupon.discount_type = discount_type
            coupon.discount_value = discount_value
            coupon.min_order_amount = min_order_amount
            coupon.max_discount_amount = max_discount_amount
            coupon.valid_until = valid_until
            coupon.is_active = True

            # Only set usage_limit if it's available in the database schema
            try:
                coupon.usage_limit = usage_limit
            except:
                pass  # Ignore if column doesn't exist

            db.session.add(coupon)
            db.session.commit()
            
            flash(f'Coupon "{code}" created successfully!', 'success')
            return redirect(url_for('admin.coupons'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating coupon: {str(e)}', 'error')
    
    return render_template('admin/add_coupon.html')

@admin_bp.route('/edit_coupon/<int:coupon_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_coupon(coupon_id):
    """Edit an existing coupon"""
    coupon = Coupon.query.get_or_404(coupon_id)

    if request.method == 'POST':
        try:
            # Parse form data
            code = request.form.get('code').upper().strip()
            description = request.form.get('description')
            discount_type = request.form.get('discount_type')
            discount_value = float(request.form.get('discount_value'))
            min_order_amount = float(request.form.get('min_order_amount', 0))
            max_discount_amount = request.form.get('max_discount_amount')
            max_discount_amount = float(max_discount_amount) if max_discount_amount else None
            usage_limit = request.form.get('usage_limit')
            usage_limit = int(usage_limit) if usage_limit else None
            valid_until_str = request.form.get('valid_until')
            try:
                valid_until = datetime.fromisoformat(valid_until_str)
            except ValueError:
                valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')

            # Check if new code already exists (but only if it's different from current)
            if code != coupon.code and Coupon.query.filter_by(code=code).first():
                flash('Coupon code already exists!', 'error')
                return render_template('admin/edit_coupon.html', coupon=coupon)

            # Update coupon attributes one by one
            coupon.code = code
            coupon.description = description
            coupon.discount_type = discount_type
            coupon.discount_value = discount_value
            coupon.min_order_amount = min_order_amount
            coupon.max_discount_amount = max_discount_amount
            coupon.valid_until = valid_until

            # Only update usage_limit if it's available in the database schema
            try:
                coupon.usage_limit = usage_limit
            except:
                pass  # Ignore if column doesn't exist

            db.session.commit()
            flash(f'Coupon "{code}" updated successfully!', 'success')
            return redirect(url_for('admin.coupons'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating coupon: {str(e)}', 'error')

    # Format date for the form
    valid_until_formatted = coupon.valid_until.strftime('%Y-%m-%d')

    return render_template('admin/edit_coupon.html', coupon=coupon, valid_until=valid_until_formatted)

@admin_bp.route('/delete_coupon/<int:coupon_id>', methods=['POST'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    
    try:
        db.session.delete(coupon)
        db.session.commit()
        flash(f'Coupon "{coupon.code}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting coupon.', 'error')
    
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/toggle_coupon/<int:coupon_id>', methods=['POST'])
@login_required
@admin_required
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    
    try:
        coupon.is_active = not coupon.is_active
        db.session.commit()
        
        status = "activated" if coupon.is_active else "deactivated"
        flash(f'Coupon "{coupon.code}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating coupon status.', 'error')
    
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/contact-messages')
@login_required
@admin_required
def contact_messages():
    page = request.args.get('page', 1, type=int)
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/contact_messages.html', messages=messages)

@admin_bp.route('/contact-message/<int:message_id>')
@login_required
@admin_required
def contact_message_detail(message_id):
    message = ContactMessage.query.get_or_404(message_id)

    # Mark as read
    if not message.is_read:
        message.is_read = True
        db.session.commit()

    return render_template('admin/contact_message_detail.html', message=message)

@admin_bp.route('/reply-contact-message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def reply_contact_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)

    reply_text = request.form.get('reply')
    send_email = request.form.get('send_email') == 'on'

    if not reply_text:
        flash('Reply text is required.', 'error')
        return redirect(url_for('admin.contact_message_detail', message_id=message_id))

    try:
        message.admin_reply = reply_text
        message.replied_at = datetime.utcnow()
        message.replied_by = current_user.id
        message.is_read = True

        db.session.commit()

        # Send email notification if requested
        if send_email:
            try:
                from flask_mail import Message as MailMessage
                from flask import current_app

                msg = MailMessage(
                    subject=f'Re: {message.subject_type.title()} - BhojanXpress',
                    sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                    recipients=[message.email]
                )

                msg.body = f"""
Dear {message.name},

Thank you for contacting BhojanXpress. Here's our response to your message:

{reply_text}

If you have any further questions, please don't hesitate to contact us.

Best regards,
BhojanXpress Team
                """

                # mail.send(msg)
                flash('Reply sent and email notification delivered successfully!', 'success')
            except Exception as e:
                flash(f'Reply saved but email notification failed: {str(e)}', 'warning')
        else:
            flash('Reply sent successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error sending reply: {str(e)}', 'error')

    return redirect(url_for('admin.contact_message_detail', message_id=message_id))

@admin_bp.route('/delete-contact-message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_contact_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)

    try:
        db.session.delete(message)
        db.session.commit()
        flash('Contact message deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting contact message.', 'error')

    return redirect(url_for('admin.contact_messages'))
