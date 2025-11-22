from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db, csrf
from app.models import User, FoodItem, Order, OrderItem, Category, Coupon, ContactMessage, NutritionalInfo, Notification, CancellationRequest
from app.forms import FoodItemForm, OrderStatusForm, CategoryForm
from app.utils.decorators import admin_required
from app.utils.helpers import format_currency, flash_errors, paginate_query
from app.utils.image_utils import save_image, get_image_url_from_data
from app.utils.notification_utils import create_order_status_notification, create_admin_message_notification, create_delivery_assignment_notification
from datetime import datetime, timedelta
from flask_mail import Message
from flask import current_app
import io
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.filter_by(is_admin=False).count()
    total_orders = Order.query.count()
    total_food_items = FoodItem.query.count()
    total_delivery_agents = User.query.filter_by(is_delivery_boy=True).count()

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
        'total_delivery_agents': total_delivery_agents,
        'today_revenue': format_currency(today_revenue),
        'pending_orders': pending_orders,
        'unread_messages': unread_messages
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

@admin_bp.route('/manage_reviews')
@login_required
@admin_required
def manage_reviews():
    """Redirect to review management"""
    return redirect(url_for('reviews.admin_reviews'))
    
@admin_bp.route('/pending_orders')
@login_required
@admin_required
def pending_orders():
    # Get all pending orders with user information
    try:
        from sqlalchemy.orm import joinedload
        orders = Order.query.options(joinedload(Order.user)).filter_by(status='pending').order_by(Order.created_at.desc()).all()
    except AttributeError:
        # Fallback if relationship doesn't work - get orders and users separately
        orders = Order.query.filter_by(status='pending').order_by(Order.created_at.desc()).all()
        # Manually add user information
        for order in orders:
            order.user = User.query.get(order.user_id)
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

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category and reassign its food items to General category"""
    try:
        category_to_delete = Category.query.get_or_404(category_id)
        
        # Prevent deletion of 'general' category
        if category_to_delete.name == 'general':
            flash('Cannot delete the General category as it serves as the default category.', 'error')
            return redirect(url_for('admin.categories'))
        
        # Ensure 'general' category exists
        general_category = Category.query.filter_by(name='general').first()
        if not general_category:
            general_category = Category(name='general', display_name='General')
            db.session.add(general_category)
            db.session.commit()
        
        # Get all food items in this category
        food_items_to_reassign = FoodItem.query.filter_by(category_id=category_id).all()
        
        # Reassign food items to general category
        for food_item in food_items_to_reassign:
            food_item.category_id = general_category.id
            food_item.category = 'general'  # Update string field too
        
        # Delete the category
        db.session.delete(category_to_delete)
        db.session.commit()
        
        flash(f'Category "{category_to_delete.display_name}" deleted successfully. {len(food_items_to_reassign)} food items moved to General category.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
        
    return redirect(url_for('admin.categories'))

@admin_bp.route('/food_items')
@login_required
@admin_required
def food_items():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    
    query = FoodItem.query
    
    # Exclude soft-deleted items (those with [DELETED] prefix)
    query = query.filter(~FoodItem.name.like('[DELETED]%'))
    
    if category != 'all':
        query = query.filter(FoodItem.category == category)
    
    food_items = query.order_by(FoodItem.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get all category names for filter dropdown
    categories_data = Category.query.order_by(Category.display_name).all()
    categories = ['all'] + [{
        'name': c.name, 
        'display_name': c.display_name
    } for c in categories_data]
    
    return render_template('admin/food_items.html', 
                         food_items=food_items, 
                         categories=categories, 
                         current_category=category,
                         current_category_display=Category.query.filter_by(name=category).first().display_name if category != 'all' else 'All Categories')

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
            db.session.flush()  # Flush to get the food_item ID
            
            # Add nutritional information if provided
            if form.add_nutrition.data and any([
                form.calories_per_serving.data,
                form.protein_g.data,
                form.carbohydrates_g.data,
                form.fat_g.data,
                form.sugar_g.data
            ]):
                # Create basic nutritional info object
                nutrition_info = NutritionalInfo(
                    food_item_id=food_item.id,
                    calories=form.calories_per_serving.data,
                    protein=form.protein_g.data,
                    carbohydrates=form.carbohydrates_g.data,
                    fat=form.fat_g.data
                )
                
                # Set additional fields
                if form.fiber_g.data is not None:
                    nutrition_info.fiber_g = form.fiber_g.data
                if form.sugar_g.data is not None:
                    nutrition_info.sugar_g = form.sugar_g.data
                if form.sodium_mg.data is not None:
                    nutrition_info.sodium_mg = form.sodium_mg.data
                if form.cholesterol_mg.data is not None:
                    nutrition_info.cholesterol_mg = form.cholesterol_mg.data
                if form.serving_size.data:
                    nutrition_info.serving_size = form.serving_size.data
                if form.allergens.data:
                    nutrition_info.allergens = form.allergens.data
                if form.ingredients.data:
                    nutrition_info.ingredients = form.ingredients.data
                db.session.add(nutrition_info)
            
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
    
    # Populate nutritional information if it exists
    try:
        nutrition = food_item.nutritional_info
        if nutrition:
            # Handle case where it might be a list or single object
            if isinstance(nutrition, list) and len(nutrition) > 0:
                nutrition = nutrition[0]
            elif not isinstance(nutrition, list):
                # It's already a single object
                pass
            else:
                nutrition = None
                
            if nutrition:
                form.add_nutrition.data = True
                form.calories_per_serving.data = nutrition.calories
                form.protein_g.data = nutrition.protein
                form.carbohydrates_g.data = nutrition.carbohydrates
                form.fat_g.data = nutrition.fat
                form.fiber_g.data = nutrition.fiber_g
                form.sugar_g.data = nutrition.sugar_g
                form.sodium_mg.data = nutrition.sodium_mg
                form.cholesterol_mg.data = nutrition.cholesterol_mg
                form.serving_size.data = nutrition.serving_size
                form.allergens.data = nutrition.allergens
                form.ingredients.data = nutrition.ingredients
    except Exception as e:
        print(f"Error loading nutritional info: {e}")
        # Continue without nutritional info
    
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
            
            # Handle nutritional information
            if form.add_nutrition.data and any([
                form.calories_per_serving.data,
                form.protein_g.data,
                form.carbohydrates_g.data,
                form.fat_g.data,
                form.sugar_g.data
            ]):
                # Update existing nutrition info or create new one
                nutrition_info = food_item.nutritional_info
                
                # Handle case where nutritional_info might be a list
                if isinstance(nutrition_info, list):
                    if len(nutrition_info) > 0:
                        nutrition_info = nutrition_info[0]
                    else:
                        nutrition_info = None
                
                if not nutrition_info:
                    nutrition_info = NutritionalInfo(food_item_id=food_item.id)
                    db.session.add(nutrition_info)
                
                nutrition_info.calories = form.calories_per_serving.data
                nutrition_info.protein = form.protein_g.data
                nutrition_info.carbohydrates = form.carbohydrates_g.data
                nutrition_info.fat = form.fat_g.data
                nutrition_info.fiber_g = form.fiber_g.data
                nutrition_info.sugar_g = form.sugar_g.data
                nutrition_info.sodium_mg = form.sodium_mg.data
                nutrition_info.cholesterol_mg = form.cholesterol_mg.data
                nutrition_info.serving_size = form.serving_size.data
                nutrition_info.allergens = form.allergens.data
                nutrition_info.ingredients = form.ingredients.data
                nutrition_info.updated_at = datetime.utcnow()
            elif not form.add_nutrition.data and food_item.nutritional_info:
                # Remove nutritional info if unchecked
                nutrition_info = food_item.nutritional_info
                if isinstance(nutrition_info, list):
                    for info in nutrition_info:
                        db.session.delete(info)
                else:
                    db.session.delete(nutrition_info)
            
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
    food_name = food_item.name
    
    try:
        # Force delete all related data in proper order to handle cascades properly
        from app.models import CartItem, OrderItem, NutritionalInfo
        
        # 1. Delete nutritional info
        nutritional_info = NutritionalInfo.query.filter_by(food_item_id=food_id).first()
        if nutritional_info:
            db.session.delete(nutritional_info)
        
        # 2. Remove cart items with this food item
        cart_items = CartItem.query.filter_by(food_item_id=food_id).all()
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        # 3. Handle order items - these cannot be deleted as they're part of order history
        order_items = OrderItem.query.filter_by(food_item_id=food_id).all()
        if order_items:
            # If food item is in existing orders, perform soft delete to preserve order history
            food_item.is_available = False
            food_item.name = f"[DELETED] {food_item.name}" if not food_item.name.startswith("[DELETED]") else food_item.name
            food_item.description = "This item has been removed from the menu."
            food_item.price = 0.0  # Set price to 0
            db.session.commit()
            flash(f'Food item "{food_name}" has been permanently removed from menu but preserved in order history.', 'success')
            return redirect(url_for('admin.food_items', deleted='success'))
        
        # 7. If no orders contain this item, safe to completely delete the food item
        db.session.delete(food_item)
        db.session.commit()
        
        flash(f'Food item "{food_name}" and all related data deleted permanently!', 'success')
        return redirect(url_for('admin.food_items', deleted='success'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"Error deleting food item: {error_msg}")  # For debugging
        
        # Enhanced error handling with specific messages
        if 'foreign key constraint' in error_msg.lower() or 'cannot delete' in error_msg.lower():
            flash(f'Cannot delete "{food_name}" - it has dependencies. The item has been disabled instead.', 'warning')
            # Fallback: disable the item
            try:
                food_item.is_available = False
                db.session.commit()
            except:
                pass
        elif 'IntegrityError' in error_msg:
            flash(f'Cannot delete "{food_name}" due to database constraints. Item has been disabled.', 'warning')
            try:
                food_item.is_available = False
                db.session.commit()
            except:
                pass
        else:
            flash(f'Error deleting food item: {error_msg}', 'error')
        
        return redirect(url_for('admin.food_items'))

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Comprehensive order management view with filtering by status"""
    # Get query parameters for filtering
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Base query
    query = Order.query

    # Apply status filter if specified
    if status != 'all':
        query = query.filter(Order.status == status)

    # Get total counts for different status tabs
    pending_count = Order.query.filter_by(status='pending').count()
    confirmed_count = Order.query.filter_by(status='confirmed').count()
    preparing_count = Order.query.filter_by(status='preparing').count()
    out_for_delivery_count = Order.query.filter_by(status='out_for_delivery').count()
    delivered_count = Order.query.filter_by(status='delivered').count()
    cancelled_count = Order.query.filter_by(status='cancelled').count()

    # Get paginated orders
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Status counts for tabs
    status_counts = {
        'all': Order.query.count(),
        'pending': pending_count,
        'confirmed': confirmed_count,
        'preparing': preparing_count,
        'out_for_delivery': out_for_delivery_count,
        'delivered': delivered_count,
        'cancelled': cancelled_count
    }

    return render_template(
        'admin/orders.html',
        orders=orders,
        current_status=status,
        status_counts=status_counts
    )

@admin_bp.route('/order/<int:order_id>')
@login_required
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)

    # Mark order as viewed by admin
    if not order.is_viewed_by_admin:
        order.is_viewed_by_admin = True
        db.session.commit()

    # Get only active delivery agents for assignment
    active_delivery_agents = User.query.filter_by(
        is_delivery_boy=True,
        is_active=True
    ).all()

    # Add pending orders count for each agent
    for agent in active_delivery_agents:
        agent.pending_orders = Order.query.filter_by(
            delivery_boy_id=agent.id
        ).filter(Order.status.in_(['confirmed', 'preparing', 'out_for_delivery'])).count()

    return render_template('admin/order_details.html',
                         order=order,
                         active_delivery_agents=active_delivery_agents)

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

    if new_status in ['confirmed', 'preparing', 'out_for_delivery', 'cancelled']:
        try:
            old_status = order.status
            order.status = new_status
            db.session.commit()

            # Create order status notification
            try:
                if order.user:
                    create_order_status_notification(order.user, order, new_status)
            except Exception as e:
                print(f"Error creating order status notification: {str(e)}")

            # If order is assigned to delivery boy, notify them too
            if new_status == 'out_for_delivery' and order.delivery_boy_id and order.delivery_boy:
                try:
                    create_delivery_assignment_notification(order.delivery_boy, order)
                except Exception as e:
                    print(f"Error creating delivery assignment notification: {str(e)}")

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
    # Filter out both admins and delivery agents to show only regular users
    users = User.query.filter_by(is_admin=False, is_delivery_boy=False).order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('admin/users.html', users=users)



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
            coupon.display_on_home = request.form.get('display_on_home') == 'on'

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
            coupon.display_on_home = request.form.get('display_on_home') == 'on'

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
    
    # Check if the customer is a registered user
    customer_user = User.query.filter_by(email=message.email).first()

    return render_template('admin/contact_message_detail.html', 
                         message=message, 
                         customer_user=customer_user)

@admin_bp.route('/reply-contact-message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def reply_contact_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)

    reply_text = request.form.get('reply')
    send_notification = request.form.get('send_notification') == 'on'

    if not reply_text:
        flash('Reply text is required.', 'error')
        return redirect(url_for('admin.contact_message_detail', message_id=message_id))

    try:
        message.admin_reply = reply_text
        message.replied_at = datetime.utcnow()
        message.replied_by = current_user.id
        message.is_read = True

        db.session.commit()

        # Send notification to user (notifications only, no email)
        if send_notification:
            try:
                # Check if the contact message email belongs to a registered user
                user = User.query.filter_by(email=message.email).first()
                if user:
                    # Create notification for registered user
                    notification = Notification(
                        user_id=user.id,
                        title=f'Response to your {message.subject_type.title()} inquiry',
                        content=f'Admin has replied to your message: "{message.message[:50]}..." \n\nReply: {reply_text}',
                        notification_type='admin_message',
                        reference_id=message.id
                    )
                    db.session.add(notification)
                    db.session.commit()
                    flash('Reply sent and notification delivered to user successfully!', 'success')
                else:
                    # User not registered, cannot send notification
                    flash('Reply saved. Note: User is not registered, so notification cannot be sent. They can view your reply by contacting support.', 'warning')
            except Exception as e:
                flash(f'Reply saved but notification failed: {str(e)}', 'warning')
        else:
            flash('Reply saved successfully! Notification was not sent as requested.', 'success')

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

@admin_bp.route('/delivery_agents')
@login_required
@admin_required
def delivery_agents():
    """Manage delivery agents with comprehensive statistics"""
    page = request.args.get('page', 1, type=int)

    agents = User.query.filter_by(is_delivery_boy=True).order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Get comprehensive statistics for each agent and enhance agent objects with additional attributes
    for agent in agents.items:
        # Add name attribute using username
        agent.name = agent.username
        
        # Get delivery statistics
        total_deliveries = Order.query.filter_by(
            delivery_boy_id=agent.id,
            status='delivered'
        ).count()

        pending_orders = Order.query.filter(
            Order.delivery_boy_id == agent.id,
            Order.status.in_(['confirmed', 'preparing', 'out_for_delivery'])
        ).count()

        total_earnings = db.session.query(db.func.sum(Order.delivery_charge)).filter(
            Order.delivery_boy_id == agent.id,
            Order.status == 'delivered'
        ).scalar() or 0

        # Add statistics directly to agent object for easier template access
        agent.total_deliveries = total_deliveries
        agent.pending_orders = pending_orders
        agent.total_earnings = total_earnings

    return render_template('admin/delivery_agents.html',
                         delivery_agents=agents)

@admin_bp.route('/delivery_agents/<int:agent_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_delivery_agent(agent_id):
    """Delete a delivery agent"""
    agent = User.query.get_or_404(agent_id)

    if not agent.is_delivery_boy:
        flash('User is not a delivery agent.', 'error')
        return redirect(url_for('admin.delivery_agents'))
        
    try:
        # Check if agent has any assigned orders
        assigned_orders = Order.query.filter_by(delivery_boy_id=agent_id).count()
        if assigned_orders > 0:
            flash(f'Cannot delete: This agent has {assigned_orders} order(s) assigned. Reassign the orders first.', 'error')
            return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))
            
        # Proceed with deletion
        username = agent.username
        db.session.delete(agent)
        db.session.commit()
        
        flash(f'Delivery agent "{username}" has been deleted successfully.', 'success')
        return redirect(url_for('admin.delivery_agents'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting delivery agent: {str(e)}', 'error')
        return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))

@admin_bp.route('/delivery_agents/<int:agent_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_delivery_agent_status(agent_id):
    """Toggle delivery agent active status"""
    agent = User.query.get_or_404(agent_id)
    is_ajax_request = request.headers.get('Content-Type') == 'application/json'

    if not agent.is_delivery_boy:
        if is_ajax_request:
            return jsonify({'success': False, 'error': 'User is not a delivery agent.'}), 400
        flash('User is not a delivery agent.', 'error')
        return redirect(url_for('admin.delivery_agents'))

    try:
        # If it's an AJAX request, get the status from the request body
        if is_ajax_request and request.json:
            new_status = request.json.get('active', False)
        else:
            # Traditional form submission - toggle the current status
            new_status = not agent.is_active
            
        agent.is_active = new_status
        db.session.commit()
        
        status_text = "activated" if new_status else "deactivated"
        
        if is_ajax_request:
            return jsonify({
                'success': True, 
                'is_active': new_status,
                'message': f'Delivery agent {agent.username} has been {status_text}.'
            })
            
        flash(f'Delivery agent {agent.username} has been {status_text}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error toggling agent status: {str(e)}")  # For debugging
        
        if is_ajax_request:
            return jsonify({'success': False, 'error': str(e)}), 500
            
        flash(f'Error updating delivery agent status: {str(e)}', 'error')

    return redirect(url_for('admin.delivery_agents'))

@admin_bp.route('/pay_commission/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def pay_commission(order_id):
    """Mark commission as paid for a specific order"""
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'delivered':
        flash('Commission can only be paid for delivered orders.', 'error')
        return redirect(request.referrer or url_for('admin.delivery_agents'))
    
    try:
        # Check if payment method requires reference
        payment_method = request.form.get('payment_method', 'cash')
        reference_id = request.form.get('reference_id', '').strip()
        
        if payment_method == 'online' and not reference_id:
            flash('Reference ID is required for online payments.', 'error')
            return redirect(request.referrer or url_for('admin.delivery_agents'))
        
        order.commission_paid = True
        order.commission_paid_at = datetime.utcnow()
        
        # Store payment method and reference if provided
        order.commission_payment_method = payment_method
        if reference_id:
            order.commission_reference_id = reference_id
            
        db.session.commit()
        
        flash(f'Commission marked as paid for Order #{order.id}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating commission status.', 'error')
    
    return redirect(request.referrer or url_for('admin.delivery_agents'))

@admin_bp.route('/pay_all_commission/<int:agent_id>', methods=['POST'])
@login_required
@admin_required
def pay_all_commission(agent_id):
    """Mark all pending commissions as paid for a specific agent"""
    payment_method = request.form.get('payment_method', 'cash')
    reference_id = request.form.get('reference_id', '').strip()
    
    # Check if payment method requires reference
    if payment_method == 'online' and not reference_id:
        flash('Reference ID is required for online payments.', 'error')
        return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))
    
    try:
        # Get all pending commission orders for this agent
        pending_orders = Order.query.filter_by(
            delivery_boy_id=agent_id,
            status='delivered',
            commission_paid=False
        ).all()
        
        if not pending_orders:
            flash('No pending commissions found for this agent.', 'warning')
            return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))
        
        # Mark all as paid
        for order in pending_orders:
            order.commission_paid = True
            order.commission_paid_at = datetime.utcnow()
            
            # Store payment method and reference
            order.commission_payment_method = payment_method
            if reference_id:
                order.commission_reference_id = reference_id
        
        db.session.commit()
        
        flash(f'All commissions paid successfully for {len(pending_orders)} orders.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating commission status.', 'error')
    
    return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))

@admin_bp.route('/pay_bulk_commission', methods=['POST'])
@login_required
@admin_required
def pay_bulk_commission():
    """Mark all pending commissions as paid for a specific agent"""
    agent_id = request.form.get('agent_id')
    payment_method = request.form.get('payment_method', 'cash')
    reference_id = request.form.get('reference_id', '').strip()
    
    if not agent_id:
        flash('Agent ID is required.', 'error')
        return redirect(request.referrer or url_for('admin.delivery_agents'))
    
    # Check if payment method requires reference
    if payment_method == 'online' and not reference_id:
        flash('Reference ID is required for online payments.', 'error')
        return redirect(request.referrer or url_for('admin.delivery_agent_profile', agent_id=agent_id))
    
    try:
        # Get all pending commission orders for this agent
        pending_orders = Order.query.filter_by(
            delivery_boy_id=agent_id,
            status='delivered',
            commission_paid=False
        ).all()
        
        if not pending_orders:
            flash('No pending commissions found for this agent.', 'warning')
            return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))
        
        # Mark all as paid
        for order in pending_orders:
            order.commission_paid = True
            order.commission_paid_at = datetime.utcnow()
            
            # Store payment method and reference
            order.commission_payment_method = payment_method
            if reference_id:
                order.commission_reference_id = reference_id
        
        db.session.commit()
        
        flash(f'Bulk commission payment completed for {len(pending_orders)} orders.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error processing bulk commission payment.', 'error')
    
    return redirect(url_for('admin.delivery_agent_profile', agent_id=agent_id))

@admin_bp.route('/download_invoice/<int:order_id>')
@login_required
@admin_required
def download_invoice(order_id):
    """Download invoice in properly formatted HTML"""
    order = Order.query.get_or_404(order_id)
    order_items = OrderItem.query.filter_by(order_id=order_id).all()

    # Create invoice HTML content with improved formatting
    invoice_html = render_template('admin/invoice_template.html',
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

@admin_bp.route('/email_invoice/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def email_invoice(order_id):
    """Email invoice to customer"""
    order = Order.query.get_or_404(order_id)

    if not order.user or not order.user.email:
        return jsonify({
            'success': False,
            'error': 'No customer email available'
        }), 400

    try:
        # Generate invoice HTML
        invoice_html = render_template('admin/invoice_template.html',
                                     order=order,
                                     order_items=order.order_items,
                                     current_date=datetime.now())

        # Here you would typically send the email using Flask-Mail
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'Invoice sent to {order.user.email}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/add_delivery_agent', methods=['GET', 'POST'])
@login_required
@admin_required
def add_delivery_agent():
    """Add a new delivery agent"""
    if request.method == 'POST':
        try:
            # Validate CSRF token
            csrf.protect()

            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            address = request.form.get('address')
            
            # Bank details
            bank_name = request.form.get('bank_name')
            account_number = request.form.get('account_number')
            ifsc_code = request.form.get('ifsc_code')
            account_holder_name = request.form.get('account_holder_name')
            upi_id = request.form.get('upi_id')

            # Validate required fields
            if not all([name, email, password, phone]):
                flash('Name, email, phone, and password are required.', 'error')
                return render_template('admin/add_delivery_agent.html')

            # Check if email already exists
            if User.query.filter_by(email=email).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('admin/add_delivery_agent.html')

            # Create new delivery agent user
            from werkzeug.security import generate_password_hash
            delivery_agent = User(
                username=name,
                email=email,
                is_delivery_boy=True,
                is_admin=False,
                phone=phone,
                address=address,
                bank_name=bank_name,
                account_number=account_number,
                ifsc_code=ifsc_code,
                account_holder_name=account_holder_name,
                upi_id=upi_id
            )
            delivery_agent.set_password(password)

            db.session.add(delivery_agent)
            db.session.commit()

            flash(f'Delivery agent "{name}" added successfully!', 'success')
            return redirect(url_for('admin.delivery_agents'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding delivery agent: {str(e)}', 'error')

    return render_template('admin/add_delivery_agent.html')

@admin_bp.route('/delivery_agent_profile/<int:agent_id>')
@login_required
@admin_required
def delivery_agent_profile(agent_id):
    """View detailed profile of a delivery agent"""
    agent = User.query.filter_by(id=agent_id, is_delivery_boy=True).first_or_404()

    # Get agent statistics
    total_deliveries = Order.query.filter_by(
        delivery_boy_id=agent.id,
        status='delivered'
    ).count()

    pending_orders = Order.query.filter_by(
        delivery_boy_id=agent.id
    ).filter(Order.status.in_(['confirmed', 'preparing', 'out_for_delivery'])).count()

    # Calculate commission details using proper formula
    def calculate_order_commission(order):
        """Calculate commission as percentage of order amount"""
        if order.status == 'delivered':
            commission = order.total_amount * 0.12  # 12% of order amount
        elif order.status in ['returned', 'cancelled']:
            commission = order.total_amount * 0.06  # 6% of order amount
        else:
            commission = 0
        return commission

    # Get all commission eligible orders (delivered, returned, cancelled)
    commission_eligible_orders = Order.query.filter(
        Order.delivery_boy_id == agent.id,
        Order.status.in_(['delivered', 'returned', 'cancelled'])
    ).all()

    total_commission_earned = sum(calculate_order_commission(order) for order in commission_eligible_orders)

    # All unpaid commission orders for display (including cancelled/returned for reference)
    pending_commission_orders = Order.query.filter(
        Order.delivery_boy_id == agent.id,
        Order.status.in_(['delivered', 'returned', 'cancelled']),
        Order.commission_paid == False
    ).all()
    
    # Only delivered orders eligible for commission payment
    payable_commission_orders = [order for order in pending_commission_orders if order.status == 'delivered']
    
    pending_commission = sum(calculate_order_commission(order) for order in pending_commission_orders)

    paid_commission = total_commission_earned - pending_commission

    # Recent orders
    recent_orders = Order.query.filter_by(
        delivery_boy_id=agent.id
    ).order_by(Order.created_at.desc()).limit(10).all()

    # Paid commission orders for history
    paid_commission_orders = Order.query.filter(
        Order.delivery_boy_id == agent.id,
        Order.commission_paid == True
    ).order_by(Order.commission_paid_at.desc()).limit(20).all()

    # Get delivered orders for earnings calculation
    delivered_orders = [order for order in commission_eligible_orders if order.status == 'delivered']
    
    # Calculate daily statistics for the current month
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_, extract
    
    current_date = datetime.now()
    start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Monthly earnings by payment method
    monthly_cash_orders = Order.query.filter(
        Order.delivery_boy_id == agent.id,
        Order.status == 'delivered',
        Order.payment_method == 'cash_on_delivery',
        Order.delivered_at >= start_of_month
    ).all()
    
    monthly_online_orders = Order.query.filter(
        Order.delivery_boy_id == agent.id,
        Order.status == 'delivered',
        Order.payment_method == 'online',
        Order.delivered_at >= start_of_month
    ).all()
    
    monthly_cash_commission = sum(calculate_order_commission(order) for order in monthly_cash_orders)
    monthly_online_commission = sum(calculate_order_commission(order) for order in monthly_online_orders)
    
    # Daily statistics for the current month
    daily_stats = []
    for i in range((current_date - start_of_month).days + 1):
        day = start_of_month + timedelta(days=i)
        day_orders = Order.query.filter(
            Order.delivery_boy_id == agent.id,
            Order.status == 'delivered',
            func.date(Order.delivered_at) == day.date()
        ).all()
        
        if day_orders:
            daily_stats.append({
                'date': day.strftime('%d %b %Y'),
                'orders': len(day_orders),
                'commission': sum(calculate_order_commission(order) for order in day_orders),
                'cash_orders': sum(calculate_order_commission(order) for order in day_orders if order.payment_method == 'cash_on_delivery'),
                'online_orders': sum(calculate_order_commission(order) for order in day_orders if order.payment_method == 'online')
            })
    
    stats = {
        'total_deliveries': total_deliveries,
        'pending_orders': pending_orders,
        'total_commission_earned': total_commission_earned,
        'pending_commission': pending_commission,
        'paid_commission': paid_commission,
        'total_earnings': sum(order.delivery_charge or 0 for order in delivered_orders),
        'monthly_cash_commission': monthly_cash_commission,
        'monthly_online_commission': monthly_online_commission,
        'daily_stats': daily_stats
    }

    # Calculate total orders and success rate for display
    total_orders = Order.query.filter_by(delivery_boy_id=agent.id).count()
    completed_orders = total_deliveries  # Same as delivered orders
    success_rate = round((completed_orders / total_orders * 100) if total_orders > 0 else 0, 1)

    return render_template('admin/delivery_agent_details.html',
                         agent=agent,
                         stats=stats,
                         total_orders=total_orders,
                         completed_orders=completed_orders,
                         success_rate=success_rate,
                         total_earnings=stats['total_earnings'],  # Pass total_earnings explicitly
                         recent_orders=recent_orders,
                         pending_commission_orders=pending_commission_orders,
                         unpaid_commissions=payable_commission_orders,
                         paid_commission_orders=paid_commission_orders)

@admin_bp.route('/edit_delivery_agent/<int:agent_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_delivery_agent(agent_id):
    """Edit delivery agent details"""
    agent = User.query.filter_by(id=agent_id, is_delivery_boy=True).first_or_404()

    if request.method == 'POST':
        try:
            # Validate CSRF token
            csrf.protect()

            # Get form data
            new_name = request.form.get('name', '').strip()
            new_username = new_name  # Use name as username for consistency
            
            # Check for duplicate username if it's being changed
            if new_username and new_username != agent.username:
                existing_user = User.query.filter(
                    User.username == new_username,
                    User.id != agent.id
                ).first()
                if existing_user:
                    flash(f'Username "{new_username}" is already taken. Please choose a different username.', 'error')
                    return render_template('admin/edit_delivery_agent.html', agent=agent)
                agent.username = new_username
                agent.name = new_name  # Update both username and name
            
            # Update other agent information
            if request.form.get('phone'):
                agent.phone = request.form.get('phone', '')
            if request.form.get('address'):
                agent.address = request.form.get('address', '')
            
            # Update bank details
            if request.form.get('bank_name'):
                agent.bank_name = request.form.get('bank_name', '')
            if request.form.get('account_number'):
                agent.account_number = request.form.get('account_number', '')
            if request.form.get('ifsc_code'):
                agent.ifsc_code = request.form.get('ifsc_code', '')
            if request.form.get('account_holder_name'):
                agent.account_holder_name = request.form.get('account_holder_name', '')
            if request.form.get('upi_id'):
                agent.upi_id = request.form.get('upi_id', '')

            # Update password if provided
            new_password = request.form.get('new_password')
            if new_password and new_password.strip():
                from werkzeug.security import generate_password_hash
                agent.password_hash = generate_password_hash(new_password)

            # Update status
            agent.is_active = request.form.get('is_active') == 'on'

            db.session.commit()
            flash(f'Delivery agent "{agent.username}" updated successfully!', 'success')
            return redirect(url_for('admin.delivery_agent_profile', agent_id=agent.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating delivery agent: {str(e)}', 'error')

    return render_template('admin/edit_delivery_agent.html', agent=agent)

@admin_bp.route('/assign_delivery_agent/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_delivery_agent(order_id):
    """Assign delivery agent to an order"""
    order = Order.query.get_or_404(order_id)
    
    # Only allow assignment for orders with 'preparing' status
    if order.status != 'preparing':
        flash('Only orders with "Preparing" status can be assigned to delivery agents', 'error')
        return redirect(url_for('admin.order_details', order_id=order_id))

    if request.method == 'POST':
        agent_id = request.form.get('delivery_agent_id')  # Changed from agent_id to delivery_agent_id to match form field
        if agent_id:
            agent = User.query.filter_by(id=agent_id, is_delivery_boy=True, is_active=True).first()
            if agent:
                order.delivery_boy_id = agent_id
                order.status = 'out_for_delivery'  # Update status to out for delivery when agent is assigned
                
                # Create notification for the delivery agent
                try:
                    create_delivery_assignment_notification(agent, order)
                except Exception as ne:
                    print(f"Could not create delivery agent notification: {str(ne)}")
                
                db.session.commit()
                flash(f'Order #{order.id} has been assigned to {agent.username} and status updated to "Out for Delivery"', 'success')
            else:
                flash('Invalid delivery agent selected', 'error')
        return redirect(url_for('admin.order_details', order_id=order_id))

    # Get available delivery agents (active agents only)
    available_agents = User.query.filter_by(
        is_delivery_boy=True,
        is_active=True
    ).all()
    
    # Add name attribute and pending orders count for each agent
    for agent in available_agents:
        agent.name = agent.username
        agent.pending_orders = Order.query.filter(
            Order.delivery_boy_id == agent.id,
            Order.status.in_(['confirmed', 'preparing', 'out_for_delivery'])
        ).count()

    return render_template('admin/assign_agent.html',
                         order=order,
                         available_agents=available_agents)

@admin_bp.route('/notifications/api/get')
@login_required
@admin_required
def get_admin_notifications():
    """API endpoint to get admin notifications"""
    try:
        # Get new orders (created in the last 24 hours and not viewed by admin)
        new_orders = Order.query.filter(
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24)),
            Order.is_viewed_by_admin == False
        ).count()

        # Get unread contact messages
        new_messages = ContactMessage.query.filter_by(is_read=False).count()

        # Get recent notifications for display
        notifications = []

        # Add recent orders
        recent_orders = Order.query.filter(
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24))
        ).order_by(Order.created_at.desc()).limit(3).all()
        
        for order in recent_orders:
            notifications.append({
                'type': 'order',
                'title': f'New Order #{order.id}',
                'content': f'{order.user.username if order.user else "Guest"} placed an order for ₹{order.total_amount:.2f}',
                'time_ago': (datetime.utcnow() - order.created_at).total_seconds() // 60,
                'url': url_for('admin.order_details', order_id=order.id)
            })

        # Add recent messages
        recent_messages = ContactMessage.query.filter_by(is_read=False).order_by(
            ContactMessage.created_at.desc()
        ).limit(3).all()
        
        for message in recent_messages:
            notifications.append({
                'type': 'message',
                'title': f'Message: {message.subject_type}',
                'content': f'From {message.name}: {message.message[:50]}...',
                'time_ago': (datetime.utcnow() - message.created_at).total_seconds() // 60,
                'url': url_for('admin.contact_message_detail', message_id=message.id)
            })

        # Sort by recency
        notifications.sort(key=lambda x: x['time_ago'])
        
        # Format time ago
        for notification in notifications:
            minutes = notification['time_ago']
            if minutes < 60:
                notification['time_ago'] = f"{int(minutes)}m ago"
            elif minutes < 1440:  # less than 24 hours
                notification['time_ago'] = f"{int(minutes // 60)}h ago"
            else:
                notification['time_ago'] = f"{int(minutes // 1440)}d ago"

        return jsonify({
            'new_orders': new_orders,
            'new_messages': new_messages,
            'notifications': notifications
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'new_orders': 0,
            'new_messages': 0,
            'notifications': []
        })
        
@admin_bp.route('/notifications/api/mark-all-read', methods=['POST'])
@login_required
@admin_required
def mark_all_admin_notifications_read():
    """Mark all admin notifications as read"""
    try:
        # Mark all recent orders as viewed
        recent_orders = Order.query.filter(
            Order.created_at >= (datetime.utcnow() - timedelta(hours=24)),
            Order.is_viewed_by_admin == False
        ).all()
        
        for order in recent_orders:
            order.is_viewed_by_admin = True
        
        # Mark all contact messages as read
        unread_messages = ContactMessage.query.filter_by(is_read=False).all()
        for message in unread_messages:
            message.is_read = True
        
        # Mark all general notifications as read (if any admin-related ones exist)
        admin_notifications = Notification.query.filter(
            Notification.notification_type.in_(['admin_message', 'system_alert']),
            Notification.is_read == False
        ).all()
        
        for notification in admin_notifications:
            notification.is_read = True
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    """View for admin notifications dashboard"""
    # Get recent notifications for display
    all_notifications = []
    order_notifications = []
    message_notifications = []
    
    # Add recent orders
    recent_orders = Order.query.filter(
        Order.created_at >= (datetime.utcnow() - timedelta(days=7))
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    for order in recent_orders:
        notification = {
            'type': 'order',
            'title': f'Order #{order.id} - {order.status.capitalize()}',
            'message': f'{order.customer.username} placed an order for ₹{order.total_amount:.2f}',
            'timestamp': order.created_at.strftime('%d %b %Y, %I:%M %p'),
            'link': url_for('admin.order_details', order_id=order.id)
        }
        all_notifications.append(notification)
        order_notifications.append(notification)
    
    # Add unread contact messages
    contact_messages = ContactMessage.query.filter_by().order_by(
        ContactMessage.created_at.desc()
    ).limit(10).all()
    
    for message in contact_messages:
        read_status = "" if message.is_read else "(Unread)"
        notification = {
            'type': 'message',
            'title': f'Contact Message {read_status}',
            'message': f'From {message.name}: {message.message[:50]}{"..." if len(message.message) > 50 else ""}',
            'timestamp': message.created_at.strftime('%d %b %Y, %I:%M %p'),
            'link': url_for('admin.contact_messages')
        }
        all_notifications.append(notification)
        message_notifications.append(notification)
    
    # Sort all notifications by timestamp (most recent first)
    all_notifications.sort(key=lambda x: datetime.strptime(x['timestamp'], '%d %b %Y, %I:%M %p'), reverse=True)
    
    return render_template('admin/notifications.html', 
                           all_notifications=all_notifications,
                           order_notifications=order_notifications,
                           message_notifications=message_notifications)

@admin_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
@admin_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification marked as read'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/delete_notification/<int:notification_id>', methods=['DELETE', 'POST'])
@login_required
@admin_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500




# Admin Messaging Routes
@admin_bp.route('/send_message', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message():
    """Send a message to specific users or all users."""
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            recipient_type = request.form.get('recipient_type', 'all')
            user_ids = request.form.getlist('user_ids')

            if not title or not message:
                flash('Title and message are required.', 'error')
                return redirect(url_for('admin.send_message'))

            recipients = []
            
            if recipient_type == 'all':
                # Send to all regular users (not admins or delivery boys)
                recipients = User.query.filter_by(is_admin=False, is_delivery_boy=False).all()
            elif recipient_type == 'specific' and user_ids:
                recipients = User.query.filter(User.id.in_(user_ids)).all()
            elif recipient_type == 'customers':
                recipients = User.query.filter_by(is_admin=False, is_delivery_boy=False).all()
            elif recipient_type == 'delivery_boys':
                recipients = User.query.filter_by(is_delivery_boy=True).all()
            
            if not recipients:
                flash('No recipients selected or found.', 'error')
                return redirect(url_for('admin.send_message'))

            # Create notifications for all recipients
            sent_count = 0
            for user in recipients:
                try:
                    create_admin_message_notification(user, title, message, current_user)
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending message to user {user.id}: {str(e)}")

            flash(f'Message sent successfully to {sent_count} users.', 'success')
            return redirect(url_for('admin.send_message'))

        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'error')
            return redirect(url_for('admin.send_message'))

    # GET request - show form
    users = User.query.filter_by(is_admin=False).order_by(User.username).all()
    regular_users = [u for u in users if not u.is_delivery_boy]
    delivery_users = [u for u in users if u.is_delivery_boy]
    
    return render_template('admin/send_message.html', 
                         regular_users=regular_users,
                         delivery_users=delivery_users)


@admin_bp.route('/user_notifications/<int:user_id>')
@login_required
@admin_required
def user_notifications(user_id):
    """View all notifications for a specific user."""
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    
    notifications = Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/user_notifications.html', 
                         user=user,
                         notifications=notifications)


@admin_bp.route('/bulk_message', methods=['POST'])
@login_required
@admin_required
def bulk_message():
    """Send bulk message via AJAX."""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        user_ids = data.get('user_ids', [])

        if not title or not message:
            return jsonify({'success': False, 'error': 'Title and message are required.'})

        if not user_ids:
            return jsonify({'success': False, 'error': 'No users selected.'})

        recipients = User.query.filter(User.id.in_(user_ids)).all()
        
        if not recipients:
            return jsonify({'success': False, 'error': 'No valid recipients found.'})

        # Create notifications for all recipients
        sent_count = 0
        for user in recipients:
            try:
                create_admin_message_notification(user, title, message, current_user)
                sent_count += 1
            except Exception as e:
                print(f"Error sending message to user {user.id}: {str(e)}")

        return jsonify({
            'success': True, 
            'message': f'Message sent successfully to {sent_count} users.'
        })

    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error sending message: {str(e)}'
        })


@admin_bp.route('/notification_stats')
@login_required
@admin_required
def notification_stats():
    """Show notification statistics."""
    try:
        # Total notifications
        total_notifications = Notification.query.count()
        
        # Unread notifications
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        # Notifications by type
        notification_types = db.session.query(
            Notification.notification_type,
            db.func.count(Notification.id).label('count')
        ).group_by(Notification.notification_type).all()
        
        # Recent notifications (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_notifications = Notification.query.filter(
            Notification.created_at >= seven_days_ago
        ).count()
        
        # Most active users (by notification count)
        active_users = db.session.query(
            User.id,
            User.username,
            db.func.count(Notification.id).label('notification_count')
        ).join(Notification, User.id == Notification.user_id)\
        .group_by(User.id, User.username)\
        .order_by(db.func.count(Notification.id).desc())\
        .limit(10).all()

        stats = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'read_notifications': total_notifications - unread_notifications,
            'recent_notifications': recent_notifications,
            'notification_types': notification_types,
            'active_users': active_users
        }

        return render_template('admin/notification_stats.html', stats=stats)

    except Exception as e:
        flash(f'Error loading notification statistics: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

# Slider Management Routes
@admin_bp.route('/slider-management')
@login_required
@admin_required
def slider_management():
    """Manage homepage slider images using database storage"""
    from app.models import SliderImage
    
    # Get ALL slider images from database (both active and inactive)
    all_sliders = SliderImage.query.order_by(SliderImage.display_order).all()
    
    # Convert to expected format for template
    slider_data = []
    for slider in all_sliders:
        slider_data.append({
            'id': slider.id,
            'filename': slider.image_filename,
            'title': slider.title,
            'subtitle': slider.subtitle,
            'path': f'uploads/sliders/{slider.image_filename}',
            'url': url_for('static', filename=f'uploads/sliders/{slider.image_filename}'),
            'exists': True,  # Since it's in DB, we assume it exists
            'size': 0,  # Can be calculated if needed
            'display_order': slider.display_order,
            'is_active': slider.is_active,
            'button_text': slider.button_text,
            'button_link': slider.button_link,
            'button_color': slider.button_color
        })
    
    return render_template('admin/slider_management.html', slider_images=slider_data)

@admin_bp.route('/slider-management/upload', methods=['POST'])
@login_required
@admin_required
def upload_slider_image():
    """Upload a new slider image"""
    """Upload a new slider image"""
    from app.models import SliderImage
    import os
    from werkzeug.utils import secure_filename
    
    if 'slider_image' not in request.files:
        flash('No image file provided', 'error')
        return redirect(url_for('admin.slider_management'))
    
    file = request.files['slider_image']
    title = request.form.get('title', 'Slider Image')
    subtitle = request.form.get('subtitle', '')
    button_text = request.form.get('button_text', 'ORDER NOW')
    button_link = request.form.get('button_link', '/menu')
    button_color = request.form.get('button_color', 'warning')
    offer_text = request.form.get('offer_text', '')
    display_order = request.form.get('display_order', type=int) or (SliderImage.query.count() + 1)
    is_active = 'is_active' in request.form
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.slider_management'))
    
    if file and allowed_file(file.filename):
        try:
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
            filename = f"{timestamp}{filename}"
            
            # Create sliders directory if it doesn't exist
            sliders_path = os.path.join(current_app.static_folder, 'uploads', 'sliders')
            os.makedirs(sliders_path, exist_ok=True)
            
            file_path = os.path.join(sliders_path, filename)
            file.save(file_path)
            
            # Save to database
            new_slider = SliderImage(
                title=title,
                subtitle=subtitle if subtitle else None,
                image_filename=filename,
                button_text=button_text,
                button_link=button_link,
                button_color=button_color,
                offer_text=offer_text if offer_text else None,
                display_order=display_order,
                is_active=is_active
            )
            db.session.add(new_slider)
            db.session.commit()
            
            flash(f'Slider image "{title}" uploaded successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading image: {str(e)}', 'error')
    else:
        flash('Invalid file type. Please upload a JPG, PNG, or GIF image.', 'error')
    
    return redirect(url_for('admin.slider_management'))

@admin_bp.route('/slider-management/delete/<int:slider_id>', methods=['POST'])
@login_required
@admin_required
def delete_slider_image(slider_id):
    """Delete a slider image"""
    from app.models import SliderImage
    import os
    
    try:
        slider = SliderImage.query.get_or_404(slider_id)
        
        # Delete file from filesystem
        file_path = os.path.join(current_app.static_folder, 'uploads', 'sliders', slider.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Mark as inactive in database instead of deleting
        slider.is_active = False
        db.session.commit()
        
        flash(f'Slider image "{slider.title}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(url_for('admin.slider_management'))

@admin_bp.route('/slider-management/toggle/<int:slider_id>', methods=['POST'])
@login_required
@admin_required
def toggle_slider(slider_id):
    """Toggle slider active status"""
    from app.models import SliderImage
    import json
    
    try:
        slider = SliderImage.query.get_or_404(slider_id)
        data = request.get_json()
        new_status = data.get('active', not slider.is_active)
        
        slider.is_active = new_status
        db.session.commit()
        
        status_text = 'activated' if new_status else 'deactivated'
        return jsonify({
            'success': True, 
            'message': f'Slider "{slider.title}" {status_text} successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error updating slider: {str(e)}'
        }), 500

@admin_bp.route('/slider-management/edit/<int:slider_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_slider(slider_id):
    """Edit slider details"""
    from app.models import SliderImage
    
    slider = SliderImage.query.get_or_404(slider_id)
    
    if request.method == 'POST':
        try:
            # Update slider details
            slider.title = request.form.get('title', slider.title)
            slider.subtitle = request.form.get('subtitle', slider.subtitle)
            slider.button_text = request.form.get('button_text', slider.button_text)
            slider.button_link = request.form.get('button_link', slider.button_link)
            slider.button_color = request.form.get('button_color', slider.button_color or 'warning')
            slider.offer_text = request.form.get('offer_text', slider.offer_text)
            slider.display_order = int(request.form.get('display_order', slider.display_order))
            slider.is_active = 'is_active' in request.form
            slider.updated_at = datetime.utcnow()
            
            # Handle image replacement if new image is uploaded
            if 'slider_image' in request.files:
                file = request.files['slider_image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old image file
                    if slider.image_filename:
                        old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'sliders', slider.image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'sliders')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    slider.image_filename = unique_filename
            
            db.session.commit()
            flash(f'Slider "{slider.title}" updated successfully!', 'success')
            return redirect(url_for('admin.slider_management'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating slider: {str(e)}', 'error')
            return redirect(url_for('admin.slider_management'))
    
    # GET request - return slider data for modal/edit form
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({
            'success': True,
            'slider': {
                'id': slider.id,
                'title': slider.title,
                'subtitle': slider.subtitle or '',
                'button_text': slider.button_text or 'ORDER NOW',
                'button_link': slider.button_link or '/menu',
                'offer_text': slider.offer_text or '',
                'display_order': slider.display_order,
                'is_active': slider.is_active,
                'image_filename': slider.image_filename
            }
        })
    
    return redirect(url_for('admin.slider_management'))

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """View detailed information about a specific user"""
    user = User.query.get_or_404(user_id)
    
    # Get user's orders
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Get user's reviews
    reviews = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc()).limit(10).all()
    
    # Calculate user statistics
    total_orders = Order.query.filter_by(user_id=user_id).count()
    total_spent = db.session.query(func.sum(Order.total_amount)).filter_by(user_id=user_id).scalar() or 0
    total_reviews = Review.query.filter_by(user_id=user_id).count()
    avg_rating_given = db.session.query(func.avg(Review.rating)).filter_by(user_id=user_id).scalar() or 0
    
    user_stats = {
        'total_orders': total_orders,
        'total_spent': float(total_spent),
        'total_reviews': total_reviews,
        'avg_rating_given': round(float(avg_rating_given), 1) if avg_rating_given else 0,
        'member_since': user.created_at.strftime('%B %Y') if user.created_at else 'Unknown'
    }
    
    return render_template('admin/user_details.html', 
                         user=user, 
                         orders=orders, 
                         reviews=reviews,
                         user_stats=user_stats)

@admin_bp.route('/food-items/<int:food_id>')
@login_required
@admin_required
def food_item_details(food_id):
    """View detailed information about a specific food item"""
    food_item = FoodItem.query.get_or_404(food_id)
    
    # Get food item reviews
    reviews = Review.query.filter_by(food_item_id=food_id).order_by(Review.created_at.desc()).limit(10).all()
    
    # Get recent orders containing this food item
    recent_orders = db.session.query(Order).join(OrderItem).filter(
        OrderItem.food_item_id == food_id
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    # Calculate food item statistics
    total_reviews = Review.query.filter_by(food_item_id=food_id).count()
    avg_rating = db.session.query(func.avg(Review.rating)).filter_by(food_item_id=food_id).scalar() or 0
    
    # Count sales
    total_sold = db.session.query(func.sum(OrderItem.quantity)).filter(
        OrderItem.food_item_id == food_id
    ).scalar() or 0
    
    # Revenue generated
    total_revenue = db.session.query(func.sum(OrderItem.quantity * OrderItem.unit_price)).filter(
        OrderItem.food_item_id == food_id
    ).scalar() or 0
    
    food_stats = {
        'total_reviews': total_reviews,
        'avg_rating': round(float(avg_rating), 1) if avg_rating else 0,
        'total_sold': int(total_sold),
        'total_revenue': float(total_revenue),
        'created_date': food_item.created_at.strftime('%B %d, %Y') if food_item.created_at else 'Unknown'
    }
    
    return render_template('admin/food_item_details.html', 
                         food_item=food_item, 
                         reviews=reviews, 
                         recent_orders=recent_orders,
                         food_stats=food_stats)

@admin_bp.route('/cancellations')
@login_required
@admin_required
def manage_cancellations():
    """Manage order cancellation requests"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = CancellationRequest.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    cancellations = query.order_by(CancellationRequest.created_at.desc()).paginate(
        page=page, 
        per_page=20, 
        error_out=False
    )
    
    # Get statistics
    stats = {
        'pending': CancellationRequest.query.filter_by(status='pending').count(),
        'approved': CancellationRequest.query.filter_by(status='approved').count(),
        'rejected': CancellationRequest.query.filter_by(status='rejected').count(),
        'total': CancellationRequest.query.count()
    }
    
    return render_template('admin/cancellations.html', 
                         cancellations=cancellations, 
                         stats=stats,
                         current_status=status_filter)

@admin_bp.route('/cancellations/<int:request_id>/review', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def review_cancellation(request_id):
    """Approve or reject cancellation request"""
    try:
        cancellation = CancellationRequest.query.get_or_404(request_id)
        
        if cancellation.status != 'pending':
            flash('This cancellation request has already been reviewed.', 'warning')
            return redirect(url_for('admin.manage_cancellations'))
        
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes', '')
        
        if action not in ['approve', 'reject']:
            flash('Invalid action.', 'error')
            return redirect(url_for('admin.manage_cancellations'))
        
        # Update cancellation request
        cancellation.status = 'approved' if action == 'approve' else 'rejected'
        cancellation.admin_notes = admin_notes
        cancellation.reviewed_at = datetime.utcnow()
        cancellation.reviewed_by = current_user.id
        
        # Update order status if approved
        if action == 'approve':
            order = cancellation.order
            order.status = 'cancelled'
            order.payment_status = 'refunded' if order.payment_method != 'cash' else order.payment_status
        
        db.session.commit()
        
        # Send notification to user
        try:
            from app.utils.email_utils import send_email
            
            send_email(
                to_email=cancellation.user.email,
                subject=f'Cancellation Request {"Approved" if action == "approve" else "Rejected"} - Order #{cancellation.order.id}',
                template='emails/cancellation_decision.html',
                user=cancellation.user,
                order=cancellation.order,
                cancellation=cancellation,
                decision=action
            )
        except Exception as e:
            current_app.logger.error(f'Failed to send cancellation decision email: {e}')
        
        flash(f'Cancellation request has been {"approved" if action == "approve" else "rejected"}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing cancellation request: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_cancellations'))


