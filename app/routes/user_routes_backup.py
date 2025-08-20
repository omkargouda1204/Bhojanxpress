from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import FoodItem, CartItem, Order, OrderItem, Coupon, UserProfile
from app.forms import SearchForm, CartForm, OrderForm
from app.utils.helpers import search_food_items, get_cart_total, calculate_delivery_time, format_currency, validate_phone_number, flash_errors
from datetime import datetime, timedelta

user_bp = Blueprint('user', __name__)

@user_bp.route('/my-orders')
@login_required
def my_orders():
    """Display user's order history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    orders = Order.query.filter_by(user_id=current_user.id)\
                       .order_by(Order.created_at.desc())\
                       .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('my_orders.html', orders=orders)

@user_bp.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    """Display order details"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_details.html', order=order)

@user_bp.route('/cancel-order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if order.status not in ['pending', 'confirmed']:
        return jsonify({'success': False, 'message': 'Order cannot be cancelled at this stage'})
    
    order.status = 'cancelled'
    db.session.commit()
    
    flash('Order cancelled successfully', 'success')
    return jsonify({'success': True, 'message': 'Order cancelled successfully'})

@user_bp.route('/place-order', methods=['POST'])
@login_required
def place_order():
    """Place an order from cart"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('user.cart'))
    
    try:
        # Get form data
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        delivery_address = request.form.get('delivery_address')
        payment_method = request.form.get('payment_method')
        special_instructions = request.form.get('special_instructions', '')
        
        # Calculate totals from session (checkout summary)
        checkout_summary = session.get('checkout_summary', {})
        
        # Create order
        order = Order(
            user_id=current_user.id,
            customer_name=full_name,
            phone_number=phone_number,
            delivery_address=delivery_address,
            payment_method=payment_method,
            special_instructions=special_instructions,
            subtotal=checkout_summary.get('subtotal', 0),
            discount_amount=checkout_summary.get('discount_amount', 0),
            coupon_discount=checkout_summary.get('coupon_discount', 0),
            gst_amount=checkout_summary.get('gst_amount', 0),
            delivery_charge=checkout_summary.get('delivery_charge', 0),
            total_amount=checkout_summary.get('total_amount', 0),
            status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                food_item_id=cart_item.food_item_id,
                quantity=cart_item.quantity,
                price=cart_item.food_item.price
            )
            db.session.add(order_item)
        
        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        
        # Clear session data
        session.pop('applied_coupon', None)
        session.pop('checkout_summary', None)
        
        db.session.commit()
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('user.order_details', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to place order. Please try again.', 'error')
        return redirect(url_for('user.checkout'))


@user_bp.route('/')
def home():
    # Get featured food items (latest 6 items)
    featured_items = FoodItem.query.filter_by(is_available=True).order_by(FoodItem.created_at.desc()).limit(6).all()
    return render_template('home.html', featured_items=featured_items)

@user_bp.route('/menu')
def menu():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    
    query = FoodItem.query.filter_by(is_available=True)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    food_items = query.paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = ['all', 'appetizer', 'main_course', 'dessert', 'beverage', 'snacks']
    
    return render_template('menu.html', food_items=food_items, categories=categories, current_category=category)

@user_bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = []
    
    if form.validate_on_submit():
        query = form.query.data
        category = form.category.data
        results = search_food_items(query, category)
        
        if not results:
            flash(f'No results found for "{query}".', 'info')
    
    elif request.method == 'GET' and request.args.get('q'):
        query = request.args.get('q')
        category = request.args.get('category', 'all')
        results = search_food_items(query, category)
        form.query.data = query
        form.category.data = category
    
    return render_template('search_results.html', form=form, results=results)

@user_bp.route('/add_to_cart/<int:food_id>', methods=['POST'])
@login_required
def add_to_cart(food_id):
    food_item = FoodItem.query.get_or_404(food_id)
    
    if not food_item.is_available:
        flash('This item is currently not available.', 'error')
        return redirect(url_for('user.menu'))
    
    quantity = int(request.form.get('quantity', 1))
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, food_item_id=food_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user.id, food_item_id=food_id, quantity=quantity)
        db.session.add(cart_item)
    
    try:
        db.session.commit()
        flash(f'{food_item.name} added to cart!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding item to cart.', 'error')
    
    return redirect(request.referrer or url_for('user.menu'))

@user_bp.route('/cart/count')
@login_required
def cart_count():
    count = CartItem.query.filter_by(user_id=current_user.id).with_entities(db.func.sum(CartItem.quantity)).scalar() or 0
    return jsonify({'count': int(count)})

@user_bp.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        return render_template('cart.html', cart_items=[], cart_summary={})
    
    # Calculate cart totals
    subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
    
    # Delivery charges: Free above ₹200, ₹30 below ₹200
    delivery_charge = 0 if subtotal >= 200 else 30
    
    # Special discounts based on subtotal
    discount_rate = 0
    if subtotal < 200:
        discount_rate = 0.02  # 2%
    elif subtotal < 1000:
        discount_rate = 0.04  # 4%
    else:
        discount_rate = 0.06  # 6%
    
    discount_amount = subtotal * discount_rate
    
    #  calculation (5% on food items)
    gst_rate = 0.05
    amount_after_discount = subtotal - discount_amount
    gst_amount = amount_after_discount * gst_rate
    
    # Total calculation
    total_amount = amount_after_discount + gst_amount + delivery_charge
    
    cart_summary = {
        'subtotal': subtotal,
        'discount_rate': discount_rate * 100,
        'discount_amount': discount_amount,
        'gst_rate': gst_rate * 100,
        'gst_amount': gst_amount,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
        'item_count': sum(item.quantity for item in cart_items)
    }
    
    return render_template('cart.html', cart_items=cart_items, cart_summary=cart_summary)

@user_bp.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = CartItem.query.get_or_404(cart_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('user.cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(cart_item)
        flash('Item removed from cart.', 'info')
    else:
        cart_item.quantity = quantity
        flash('Cart updated.', 'success')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Error updating cart.', 'error')
    
    return redirect(url_for('user.cart'))

@user_bp.route('/apply_coupon', methods=['POST'])
@login_required
def apply_coupon():
    coupon_code = request.form.get('coupon_code', '').upper().strip()
    
    if not coupon_code:
        return jsonify({'success': False, 'message': 'Please enter a coupon code'})
    
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    
    if not coupon or not coupon.is_valid():
        return jsonify({'success': False, 'message': 'Invalid or expired coupon code'})
    
    # Get cart total
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
    
    if subtotal < coupon.min_order_amount:
        return jsonify({
            'success': False, 
            'message': f'Minimum order amount ₹{coupon.min_order_amount} required for this coupon'
        })
    
    # Calculate coupon discount
    if coupon.discount_type == 'percentage':
        coupon_discount = subtotal * (coupon.discount_value / 100)
        if coupon.max_discount_amount:
            coupon_discount = min(coupon_discount, coupon.max_discount_amount)
    else:  # fixed
        coupon_discount = coupon.discount_value
    
    # Store coupon in session
    session['applied_coupon'] = {
        'code': coupon.code,
        'discount': coupon_discount,
        'description': coupon.description
    }
    
    return jsonify({
        'success': True, 
        'message': f'Coupon applied! You saved ₹{coupon_discount:.2f}',
        'discount': coupon_discount
    })

@user_bp.route('/remove_coupon', methods=['POST'])
@login_required
def remove_coupon():
    session.pop('applied_coupon', None)
    return jsonify({'success': True, 'message': 'Coupon removed'})

@user_bp.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('user.menu'))
    
    # Calculate totals with coupon
    subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
    delivery_charge = 0 if subtotal >= 200 else 30
    
    # Special discounts
    discount_rate = 0
    if subtotal < 200:
        discount_rate = 0.02
    elif subtotal < 1000:
        discount_rate = 0.04
    else:
        discount_rate = 0.06
    
    discount_amount = subtotal * discount_rate
    
    # Apply coupon if available
    applied_coupon = session.get('applied_coupon')
    coupon_discount = applied_coupon['discount'] if applied_coupon else 0
    
    # GST calculation
    amount_after_discount = subtotal - discount_amount - coupon_discount
    gst_amount = amount_after_discount * 0.05
    total_amount = amount_after_discount + gst_amount + delivery_charge
    
    checkout_summary = {
        'subtotal': subtotal,
        'discount_rate': discount_rate * 100,
        'discount_amount': discount_amount,
        'coupon_discount': coupon_discount,
        'applied_coupon': applied_coupon,
        'gst_amount': gst_amount,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
        'item_count': sum(item.quantity for item in cart_items)
    }
    
    # Get user profile for shipping address
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         checkout_summary=checkout_summary,
                         user_profile=user_profile)

@user_bp.route('/profile')
@login_required
def profile():
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not user_profile:
        user_profile = UserProfile(user_id=current_user.id)
        db.session.add(user_profile)
        db.session.commit()
    
    # Get recent orders
    recent_orders = Order.query.filter_by(user_id=current_user.id)\
                              .order_by(Order.created_at.desc())\
                              .limit(5).all()
    
    return render_template('profile.html', 
                         user_profile=user_profile,
                         recent_orders=recent_orders)

@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not user_profile:
        user_profile = UserProfile(user_id=current_user.id)
        db.session.add(user_profile)
    
    # Update profile fields
    user_profile.full_name = request.form.get('full_name')
    user_profile.phone = request.form.get('phone')
    user_profile.alternate_phone = request.form.get('alternate_phone')
    user_profile.address_line1 = request.form.get('address_line1')
    user_profile.address_line2 = request.form.get('address_line2')
    user_profile.city = request.form.get('city')
    user_profile.state = request.form.get('state')
    user_profile.zip_code = request.form.get('zip_code')
    
    # Update user email if provided
    email = request.form.get('email')
    if email and email != current_user.email:
        current_user.email = email
    
    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'error')
    
    return redirect(url_for('user.profile'))

@user_bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('user.menu'))
    
    # Get form data
    payment_method = request.form.get('payment_method')
    delivery_address = request.form.get('delivery_address')
    phone_number = request.form.get('phone_number')
    special_instructions = request.form.get('special_instructions', '')
    
    # Calculate totals
    subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
    delivery_charge = 0 if subtotal >= 200 else 30
    
    # Special discounts
    discount_rate = 0
    if subtotal < 200:
        discount_rate = 0.02
    elif subtotal < 1000:
        discount_rate = 0.04
    else:
        discount_rate = 0.06
    
    discount_amount = subtotal * discount_rate
    
    # Apply coupon if available
    applied_coupon = session.get('applied_coupon')
    coupon_discount = applied_coupon['discount'] if applied_coupon else 0
    
    # GST calculation
    amount_after_discount = subtotal - discount_amount - coupon_discount
    gst_amount = amount_after_discount * 0.05
    total_amount = amount_after_discount + gst_amount + delivery_charge
    
    try:
        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            delivery_address=delivery_address,
            phone_number=phone_number,
            special_instructions=special_instructions,
            estimated_delivery=datetime.utcnow() + timedelta(minutes=45)
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                food_item_id=cart_item.food_item_id,
                quantity=cart_item.quantity,
                price=cart_item.food_item.price
            )
            db.session.add(order_item)
        
        # Update coupon usage if applied
        if applied_coupon:
            coupon = Coupon.query.filter_by(code=applied_coupon['code']).first()
            if coupon:
                coupon.used_count += 1
                session.pop('applied_coupon', None)
        
        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        flash(f'Order placed successfully! Order ID: #{order.id}', 'success')
        return redirect(url_for('user.order_details', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error placing order. Please try again.', 'error')
        return redirect(url_for('user.checkout'))
    
    return redirect(url_for('user.cart'))

@user_bp.route('/remove_from_cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = CartItem.query.get_or_404(cart_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('user.cart'))
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing item from cart.', 'error')
    
    return redirect(url_for('user.cart'))

@user_bp.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.orders'))
    
    return render_template('order_confirmation.html', order=order)

@user_bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('orders.html', orders=orders)

@user_bp.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.orders'))
    
    return render_template('order_details.html', order=order)

@user_bp.route('/contact')
def contact():
    return render_template('contact.html')

@user_bp.route('/track_order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.orders'))
    
    return render_template('track_order.html', order=order)
