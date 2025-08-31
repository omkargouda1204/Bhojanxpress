from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import FoodItem, CartItem, Order, OrderItem, Coupon, UserProfile, Category, Rating, ContactMessage, ReviewImage
from app.models.special_offers import SpecialOffer
from sqlalchemy import func

from app.forms import SearchForm, CartForm, OrderForm
from app.utils.helpers import search_food_items, get_cart_total, calculate_delivery_time, format_currency, validate_phone_number, flash_errors
from app.utils.paypal_utils import PayPalClient
from app.utils.payment_config import PAYPAL_CLIENT_ID
from datetime import datetime, timedelta
from flask_mail import Message
from flask import current_app
import io
import json
from flask import send_file
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

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
    
    return render_template('components/my_orders.html', orders=orders)

@user_bp.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    """Display order details"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('components/order_details.html', order=order, timedelta=timedelta)

@user_bp.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    """Payment page for order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('components/payment.html', order=order, paypal_client_id=PAYPAL_CLIENT_ID)

@user_bp.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('components/order_confirmation.html', order=order)

@user_bp.route('/cancel-order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order - only allowed within 10 minutes of placement"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    # Calculate time difference between now and order creation
    time_diff = datetime.utcnow() - order.created_at
    cancellation_limit_minutes = 10  # Allow cancellation within 10 minutes

    # Check if order can be cancelled based on status and time
    if order.status in ['pending', 'confirmed']:
        # Check if within cancellation time limit
        if time_diff.total_seconds() <= (cancellation_limit_minutes * 60):
            try:
                order.status = 'cancelled'
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Order cancelled successfully'
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Error cancelling order'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Order cannot be cancelled after {cancellation_limit_minutes} minutes of placement'
            })
    else:
        return jsonify({
            'success': False,
            'message': 'Order cannot be cancelled at this stage'
        })

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
        
        # Redirect based on payment method
        if payment_method in ['card_payment', 'paypal', 'upi_payment']:
            # For online payments, redirect to payment page
            flash('Please complete your payment to confirm your order.', 'info')
            return redirect(url_for('user.payment', order_id=order.id))
        else:
            # For cash on delivery, mark as confirmed immediately
            order.status = 'confirmed'
            db.session.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('user.order_confirmation', order_id=order.id))

    except Exception as e:
        db.session.rollback()
        flash('Failed to place order. Please try again.', 'error')
        return redirect(url_for('user.checkout'))


@user_bp.route('/')
def home():
    # Get featured food items (latest 6 items)
    # Featured Menu Items - Show all available items (max 18 for 3 rows)
    featured_items = FoodItem.query.filter_by(is_available=True).order_by(FoodItem.created_at.desc()).limit(18).all()

    # Get all categories for dynamic display
    categories = Category.query.all()

    # Get ALL active coupons (remove limit)
    active_coupons = Coupon.query.filter(
        Coupon.is_active == True,
        Coupon.display_on_home == True,  # Admin permission to display
        Coupon.valid_until > datetime.now()
    ).order_by(Coupon.created_at.desc()).all()  # Get ALL, not limited
    
    # Get special offers
    special_offers = SpecialOffer.query.filter(
        SpecialOffer.is_active == True,
        SpecialOffer.valid_until > datetime.now()
    ).all()
    
    # Get most popular food items (based on order count) - Limited to 10 items
    popular_items = db.session.query(
        FoodItem, func.sum(OrderItem.quantity).label('total_ordered')
    ).join(OrderItem).group_by(FoodItem).filter(
        FoodItem.is_available == True
    ).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()
    
    # Extract just the food items from the query result
    popular_food_items = [item[0] for item in popular_items]

    return render_template('home.html',
                         featured_items=featured_items,
                         active_coupons=active_coupons,
                         special_offers=special_offers,
                         popular_items=popular_food_items,
                         categories=categories)

@user_bp.route('/menu')
def menu():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    query = FoodItem.query.filter_by(is_available=True)

    # Fix category filtering - use both string category and category_id
    if category != 'all':
        query = query.filter(
            db.or_(
                FoodItem.category == category,
                FoodItem.category_rel.has(Category.name == category)
            )
        )

    food_items = query.paginate(
        page=page, per_page=12, error_out=False
    )

    # Get actual categories from database
    db_categories = Category.query.all()
    # Create a simple list for filtering, but pass the actual category objects to template
    categories_list = ['all'] + [cat.name for cat in db_categories]

    return render_template('components/menu.html', food_items=food_items, categories=db_categories, current_category=category)

@user_bp.route('/search_suggestions')
def search_suggestions():
    """Returns search suggestions for autocomplete"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Base query
    search_query = FoodItem.query.filter(FoodItem.is_available == True)
    
    # Apply filters
    search_query = search_query.filter(
        FoodItem.name.ilike(f'%{query}%') |
        FoodItem.description.ilike(f'%{query}%')
    )
    
    if category and category != 'all':
        search_query = search_query.filter(FoodItem.category == category)
        
    if price_min:
        search_query = search_query.filter(FoodItem.price >= float(price_min))
        
    if price_max:
        search_query = search_query.filter(FoodItem.price <= float(price_max))
    
    # Get limited results for suggestions
    results = search_query.limit(8).all()
    
    suggestions = []
    for item in results:
        # Determine image URL properly
        image_url = None
        if hasattr(item, 'image_url') and item.image_url:
            image_url = item.image_url
        elif hasattr(item, 'image_path') and item.image_path:
            image_url = url_for('static', filename=item.image_path)
        else:
            image_url = url_for('static', filename='images/food-placeholder.png')
            
        # Get category display name
        category_name = item.category.replace('_', ' ').title() if item.category else 'General'
        if hasattr(item, 'category_rel') and item.category_rel and hasattr(item.category_rel, 'display_name'):
            category_name = item.category_rel.display_name
            
        suggestions.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'category': category_name,
            'image_url': image_url,
            'description': item.description[:50] + '...' if item.description and len(item.description) > 50 else item.description or ''
        })
    
    return jsonify(suggestions)

@user_bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = []
    
    if form.validate_on_submit():
        query = form.query.data
        category = form.category.data
        price_min = form.price_min.data
        price_max = form.price_max.data
        
        # Use the search function with filters
        results = search_food_items(query, category)
        
        # Additional filtering by price if needed
        if price_min or price_max:
            filtered_results = []
            for item in results:
                if (not price_min or item.price >= price_min) and \
                   (not price_max or item.price <= price_max):
                    filtered_results.append(item)
            results = filtered_results
        
        if not results:
            flash(f'No results found for "{query}".', 'info')

    elif request.method == 'GET' and (request.args.get('q') or request.args.get('query')):
        # Handle both 'q' parameter (from autocomplete) and 'query' parameter (from form)
        query = request.args.get('q') or request.args.get('query')
        category = request.args.get('category', 'all')
        price_min = request.args.get('price_min')
        price_max = request.args.get('price_max')
        
        form.query.data = query
        form.category.data = category
        if price_min: form.price_min.data = float(price_min)
        if price_max: form.price_max.data = float(price_max)
        
        # Get search results with filters
        results = search_food_items(query, category)
        
        # Additional filtering by price
        if price_min or price_max:
            filtered_results = []
            for item in results:
                if (not price_min or item.price >= float(price_min)) and \
                   (not price_max or item.price <= float(price_max)):
                    filtered_results.append(item)
            results = filtered_results
    
    return render_template('components/search_results.html', form=form, results=results)

@user_bp.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment for an order"""
    order_id = request.args.get('order_id')
    payment_method = request.form.get('payment_method')

    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    # Update the order's payment method
    order.payment_method = payment_method

    if payment_method == 'cash_on_delivery':
        order.status = 'confirmed'
        db.session.commit()
        flash('Your order has been confirmed!', 'success')
        return redirect(url_for('user.order_confirmation', order_id=order.id))
    elif payment_method == 'paypal':
        # For PayPal, we should redirect to create the order via AJAX
        # This route should not handle PayPal directly
        flash('Please use the PayPal payment option properly.', 'error')
        return redirect(url_for('user.payment', order_id=order.id))
    elif payment_method == 'card_payment':
        # Get card details from form
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        card_name = request.form.get('card_name')

        # Validate card details
        if not card_number or not expiry_date or not cvv or not card_name:
            flash('Please provide all required card details', 'error')
            return redirect(url_for('user.payment', order_id=order.id))

        # In a real system, you would process the payment through a payment gateway
        # For demonstration, we're simulating a successful payment

        # Store payment reference (last 4 digits of card)
        order.payment_reference = f"CARD-{card_number.strip()[-4:]}"
        order.status = 'confirmed'

        db.session.commit()
        flash('Your card payment has been processed successfully!', 'success')
        return redirect(url_for('user.order_confirmation', order_id=order.id))
    elif payment_method == 'upi_payment':
        # Get UPI ID
        upi_id = request.form.get('upi_id')

        # Validate UPI ID
        if not upi_id:
            flash('Please provide a valid UPI ID', 'error')
            return redirect(url_for('user.payment', order_id=order.id))

        # In a real system, you would initiate a UPI payment request
        # For demonstration, we're simulating a successful payment

        # Store payment reference
        order.payment_reference = f"UPI-{upi_id}"
        order.status = 'confirmed'

        db.session.commit()
        flash('Your UPI payment has been processed successfully!', 'success')
        return redirect(url_for('user.order_confirmation', order_id=order.id))
    else:
        flash('Invalid payment method selected', 'error')
        return redirect(url_for('user.payment', order_id=order.id))

@user_bp.route('/create_paypal_order/<int:order_id>', methods=['POST'])
@login_required
def create_paypal_order(order_id):
    """Create a PayPal order based on an existing BhojanXpress order"""
    try:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

        # Explicitly query order items instead of using relationship
        order_items = OrderItem.query.filter_by(order_id=order.id).all()

        if not order_items:
            current_app.logger.error(f"No order items found for order {order_id}")
            return jsonify({
                'success': False,
                'error': 'No items found in this order'
            })

        # Format order items for PayPal
        paypal_order_items = []
        for item in order_items:
            try:
                # Get the food item details
                food_item = FoodItem.query.get(item.food_item_id)
                if not food_item:
                    current_app.logger.warning(f"Food item {item.food_item_id} not found for order item {item.id}")
                    continue

                paypal_order_items.append({
                    'name': food_item.name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                })
            except Exception as e:
                current_app.logger.error(f"Error processing order item {item.id}: {str(e)}")
                continue

        if not paypal_order_items:
            return jsonify({
                'success': False,
                'error': 'No valid items found for PayPal order'
            })

        # Prepare order data for PayPal with correct return URLs
        order_data = {
            'order_id': order.id,
            'items': paypal_order_items,
            'subtotal': float(order.subtotal or 0),
            'discount_amount': float(order.discount_amount or 0),
            'coupon_discount': float(order.coupon_discount or 0),
            'gst_amount': float(order.gst_amount or 0),
            'delivery_charge': float(order.delivery_charge or 0),
            'total_amount': float(order.total_amount),
            'return_url': url_for('user.paypal_return', _external=True),
            'cancel_url': url_for('user.paypal_cancel', _external=True)
        }

        # Log the order data for debugging
        current_app.logger.info(f"Creating PayPal order for order {order_id} with {len(paypal_order_items)} items")
        current_app.logger.info(f"Order data: {order_data}")

        # Create PayPal order
        paypal_client = PayPalClient()
        result = paypal_client.create_order(order_data)

        if result['success']:
            # Store PayPal order ID in our order
            order.payment_reference = result['order_id']
            order.payment_method = 'paypal'

            # Add payment status field if it exists
            if hasattr(order, 'payment_status'):
                order.payment_status = 'pending'

            db.session.commit()

            return jsonify({
                'success': True,
                'order_id': result['order_id'],
                'approval_url': result['approval_url']
            })
        else:
            current_app.logger.error(f"PayPal order creation failed: {result}")
            error_msg = "Failed to create PayPal order"
            err = result.get('error')
            # Handle currency not supported specifically
            if isinstance(err, dict) and 'details' in err:
                for detail in err['details']:
                    if detail.get('issue') == 'CURRENCY_NOT_SUPPORTED':
                        error_msg = "PayPal cannot process payments in this currency. Please choose a different payment method."
                        break
                else:
                    # Fallback to first detail description
                    if err['details']:
                        error_msg = err['details'][0].get('description', error_msg)
            elif isinstance(err, dict) and 'message' in err:
                error_msg = err['message']
            elif isinstance(err, str):
                error_msg = err
            return jsonify({'success': False, 'error': error_msg})

    except Exception as e:
        current_app.logger.error(f"Exception in create_paypal_order: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred while creating PayPal order'
        })

@user_bp.route('/capture_paypal_payment/<path:paypal_order_id>', methods=['POST'])
@login_required
def capture_paypal_payment(paypal_order_id):
    """Capture an approved PayPal payment"""
    # Find our order using the PayPal order ID
    order = Order.query.filter_by(payment_reference=paypal_order_id).first()

    if not order:
        return jsonify({'success': False, 'error': 'Order not found'})

    if order.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'})

    # Capture the payment
    paypal_client = PayPalClient()
    result = paypal_client.capture_payment(paypal_order_id)

    if result['success']:
        # Update order status
        order.status = 'confirmed'
        order.payment_status = 'paid'
        order.payment_details = json.dumps(result['details'])
        db.session.commit()

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to capture payment')})

@user_bp.route('/paypal_return')
@login_required
def paypal_return():
    """Handle PayPal payment return (success or cancel)"""
    token = request.args.get('token')  # PayPal order ID
    payer_id = request.args.get('PayerID')  # PayPal payer ID

    if not token:
        flash('Invalid PayPal return. Please try again.', 'error')
        return redirect(url_for('user.my_orders'))

    # Find our order using the PayPal order ID
    order = Order.query.filter_by(payment_reference=token).first()

    if not order:
        flash('Order not found. Please contact support.', 'error')
        return redirect(url_for('user.my_orders'))

    if order.user_id != current_user.id:
        flash('Unauthorized access to order.', 'error')
        return redirect(url_for('user.my_orders'))

    if payer_id:  # Payment was approved
        # Capture the payment
        paypal_client = PayPalClient()
        result = paypal_client.capture_payment(token)

        if result['success']:
            # Update order status
            order.status = 'confirmed'
            order.payment_status = 'paid'
            order.payment_details = json.dumps(result['details'])
            db.session.commit()

            flash('Payment completed successfully! Your order has been confirmed.', 'success')
            return redirect(url_for('user.order_confirmation', order_id=order.id))
        else:
            flash(f'Payment capture failed: {result.get("error", "Unknown error")}', 'error')
            return redirect(url_for('user.payment', order_id=order.id))
    else:
        # Payment was cancelled
        flash('Payment was cancelled. You can try again or choose a different payment method.', 'warning')
        return redirect(url_for('user.payment', order_id=order.id))

@user_bp.route('/paypal_cancel')
@login_required
def paypal_cancel():
    """Handle PayPal payment cancellation and restore cart"""
    token = request.args.get('token')  # PayPal order ID
    if token:
        order = Order.query.filter_by(payment_reference=token, payment_method='paypal').first()
        if order and order.user_id == current_user.id:
            # Restore cart items
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            for oi in order_items:
                existing = CartItem.query.filter_by(user_id=current_user.id, food_item_id=oi.food_item_id).first()
                if existing:
                    existing.quantity += oi.quantity
                else:
                    db.session.add(CartItem(user_id=current_user.id, food_item_id=oi.food_item_id, quantity=oi.quantity))
            # Delete order and its items
            OrderItem.query.filter_by(order_id=order.id).delete()
            db.session.delete(order)
            db.session.commit()
            flash('Payment was cancelled. Your order was removed and cart restored.', 'warning')
            return redirect(url_for('user.cart'))
    flash('Payment was cancelled. You can try again or choose a different payment method.', 'warning')
    return redirect(url_for('user.cart'))

@user_bp.route('/add_to_cart/<int:food_id>', methods=['POST'])
@login_required
def add_to_cart(food_id):
    food_item = FoodItem.query.get_or_404(food_id)

    quantity = int(request.form.get('quantity', 1) if not request.is_json else request.json.get('quantity', 1))

    # Allow adding unavailable items but with a notice
    availability_message = ""
    if not food_item.is_available:
        availability_message = " (Note: This item is currently marked as unavailable)"

    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, food_item_id=food_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user.id, food_item_id=food_id, quantity=quantity)
        db.session.add(cart_item)

    try:
        db.session.commit()
        # Get updated cart count
        cart_count = CartItem.query.filter_by(user_id=current_user.id).with_entities(db.func.sum(CartItem.quantity)).scalar() or 0

        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'{food_item.name} added to cart!{availability_message}',
                'cart_count': int(cart_count)
            })
        flash(f'{food_item.name} added to cart!{availability_message}', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error adding item to cart.'})
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
        return render_template('components/cart.html', cart_items=[], cart_summary={})

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
    
    # GST calculation (5% on food items)
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
    
    return render_template('components/cart.html', cart_items=cart_items, cart_summary=cart_summary)

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
    
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'})

    if not coupon.is_active:
        return jsonify({'success': False, 'message': 'This coupon is no longer active'})

    # Check expiration
    if coupon.valid_until < datetime.utcnow():
        return jsonify({'success': False, 'message': 'This coupon has expired'})

    # Check usage limit if the attribute exists
    try:
        if hasattr(coupon, 'usage_limit') and coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return jsonify({'success': False, 'message': 'This coupon has reached its usage limit'})
    except AttributeError:
        # Skip usage limit check if column doesn't exist
        pass

    # Get cart total
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({'success': False, 'message': 'Your cart is empty'})

    subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
    
    if subtotal < coupon.min_order_amount:
        return jsonify({
            'success': False, 
            'message': f'Minimum order amount ₹{coupon.min_order_amount} required for this coupon'
        })
    
    # Calculate coupon discount
    if coupon.discount_type == 'percentage':
        coupon_discount = subtotal * (coupon.discount_value / 100)
        if hasattr(coupon, 'max_discount_amount') and coupon.max_discount_amount and coupon_discount > coupon.max_discount_amount:
            coupon_discount = coupon.max_discount_amount
    else:  # fixed
        coupon_discount = coupon.discount_value
    
    # Round to 2 decimal places
    coupon_discount = round(coupon_discount, 2)

    # Store coupon in session
    session['applied_coupon'] = {
        'id': coupon.id,
        'code': coupon.code,
        'discount': coupon_discount,
        'discount_type': coupon.discount_type,
        'discount_value': coupon.discount_value,
        'description': coupon.description or f"Coupon: {coupon.code}"
    }

    return jsonify({
        'success': True,
        'message': f'Coupon applied! You saved ₹{coupon_discount:.2f}',
        'discount': coupon_discount,
        'code': coupon.code
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
    
    # Store checkout summary in session for place_order
    session['checkout_summary'] = checkout_summary

    # Get user profile for shipping address
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()

    return render_template('components/checkout.html',
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
    
    return render_template('components/profile.html',
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

@user_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('components/contact.html')

@user_bp.route('/send-contact-message', methods=['POST'])
def send_contact_message():
    """Send contact form message to bhojanxpress@gmail.com"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', 'Not provided')
        subject_type = request.form.get('subject')
        message = request.form.get('message')
        
        # Map the subject type to a more descriptive subject
        subject_mapping = {
            'order': 'Order Issue',
            'delivery': 'Delivery Query',
            'feedback': 'Customer Feedback',
            'other': 'General Inquiry'
        }

        subject = f"BhojanXpress Contact: {subject_mapping.get(subject_type, 'Contact Form')}"

        # Format the email body
        email_body = f"""
        New message from BhojanXpress contact form:
        
        Name: {name}
        Email: {email}
        Phone: {phone}
        Subject: {subject_mapping.get(subject_type, 'Not specified')}
        
        Message:
        {message}
        """

        # Save contact message to database
        contact_message = ContactMessage(
            name=name,
            email=email,
            phone=phone,
            subject_type=subject_type,  # Fixed: use subject_type instead of subject
            message=message,
            created_at=datetime.utcnow()
        )
        db.session.add(contact_message)
        db.session.commit()

        # Use Flask-Mail to send the email
        msg = Message(
            subject=subject,
            recipients=['bhojanaxpress@gmail.com'],
            body=email_body,
            sender=email
        )
        current_app.extensions['mail'].send(msg)

        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('user.contact'))

    except Exception as e:
        current_app.logger.error(f"Error sending contact email: {str(e)}")
        flash('There was an error sending your message. Please try again later.', 'error')
        return redirect(url_for('user.contact'))

@user_bp.route('/receipt/<int:order_id>')
@login_required
def receipt(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    download = request.args.get('download')
    if download and REPORTLAB_AVAILABLE:
        # Generate PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 40
        p.setFont("Helvetica-Bold", 18)
        p.drawString(40, y, "BhojanXpress Invoice")
        p.setFont("Helvetica", 12)
        y -= 40
        p.drawString(40, y, f"Order ID: {order.id}")
        y -= 20
        p.drawString(40, y, f"Date: {order.created_at.strftime('%d-%m-%Y %H:%M')}")
        y -= 20
        p.drawString(40, y, f"Customer: {order.customer_name}")
        y -= 20
        p.drawString(40, y, f"Phone: {order.phone_number}")
        y -= 20
        p.drawString(40, y, f"Shipping Address: {order.delivery_address}")
        y -= 30
        p.setFont("Helvetica-Bold", 14)
        p.drawString(40, y, "Order Items:")
        y -= 20
        p.setFont("Helvetica", 12)
        for item in order.order_items:
            p.drawString(50, y, f"{item.food_item.name} (x{item.quantity}) - ₹{item.price:.2f} each")
            y -= 18
            if y < 100:
                p.showPage()
                y = height - 40
        y -= 10
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, f"Subtotal: ₹{order.subtotal:.2f}")
        y -= 18
        p.drawString(40, y, f"Discount: -₹{order.discount_amount + order.coupon_discount:.2f}")
        y -= 18
        p.drawString(40, y, f"GST: ₹{order.gst_amount:.2f}")
        y -= 18
        p.drawString(40, y, f"Delivery: ₹{order.delivery_charge:.2f}")
        y -= 18
        p.setFont("Helvetica-Bold", 14)
        p.drawString(40, y, f"Total: ₹{order.total_amount:.2f}")
        p.showPage()
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"invoice_{order.id}.pdf", mimetype='application/pdf')
    # Fallback: render HTML invoice
    return render_template('components/receipt.html', order=order)

@user_bp.route('/track_order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.my_orders'))
    
    return render_template('components/track_order.html', order=order)

@user_bp.route('/food/<int:food_id>', methods=['GET', 'POST'])
def food_detail(food_id):
    """Display food item details and handle rating submissions"""
    food_item = FoodItem.query.get_or_404(food_id)

    # Get all ratings for this food item
    ratings = Rating.query.filter_by(food_item_id=food_id).order_by(Rating.created_at.desc()).all()

    # Calculate average rating
    avg_rating = 0
    if ratings:
        avg_rating = sum(r.rating for r in ratings) / len(ratings)

    # Check if the current user has already rated this item
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(food_item_id=food_id, user_id=current_user.id).first()

    # Get similar food items from the same category
    similar_items = FoodItem.query.filter(
        FoodItem.category_id == food_item.category_id,
        FoodItem.id != food_item.id,
        FoodItem.is_available == True
    ).order_by(db.func.random()).limit(4).all()

    # Handle rating submission
    if request.method == 'POST' and current_user.is_authenticated:
        try:
            rating_value = int(request.form.get('rating', 0))
            if 1 <= rating_value <= 5:
                comment = request.form.get('comment', '')

                # Update existing rating or create new one
                if user_rating:
                    # Delete existing images
                    for img in user_rating.images:
                        db.session.delete(img)
                    
                    user_rating.rating = rating_value
                    user_rating.comment = comment
                    user_rating.updated_at = datetime.utcnow()
                    flash('Your rating has been updated!', 'success')
                else:
                    new_rating = Rating(
                        user_id=current_user.id,
                        food_item_id=food_id,
                        rating=rating_value,
                        comment=comment
                    )
                    db.session.add(new_rating)
                    flash('Your rating has been submitted!', 'success')
                    user_rating = new_rating

                # Handle image uploads
                uploaded_files = request.files.getlist('reviewImages')
                if uploaded_files:
                    import os
                    from werkzeug.utils import secure_filename
                    
                    # Create uploads directory if it doesn't exist
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    
                    for i, file in enumerate(uploaded_files[:3]):  # Limit to 3 images
                        if file and file.filename and '.' in file.filename:
                            file_ext = file.filename.rsplit('.', 1)[1].lower()
                            if file_ext in allowed_extensions:
                                # Generate unique filename
                                filename = f"review_{user_rating.id if hasattr(user_rating, 'id') and user_rating.id else 'temp'}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                                filepath = os.path.join(upload_folder, filename)
                                
                                # Save file
                                file.save(filepath)
                                
                                # Create ReviewImage record
                                review_image = ReviewImage(
                                    rating_id=user_rating.id if hasattr(user_rating, 'id') and user_rating.id else None,
                                    image_url=f"/static/uploads/reviews/{filename}",
                                    image_filename=file.filename
                                )
                                db.session.add(review_image)

                db.session.commit()
                
                # Update rating_id for images if it was a new rating
                if not hasattr(user_rating, 'id') or not user_rating.id:
                    db.session.refresh(user_rating)
                    for img in db.session.query(ReviewImage).filter_by(rating_id=None).all():
                        img.rating_id = user_rating.id
                    db.session.commit()
                
                return redirect(url_for('user.food_detail', food_id=food_id))
            else:
                flash('Please provide a valid rating (1-5 stars).', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting rating: {str(e)}', 'error')

    return render_template('components/food_detail.html',
                          food=food_item,
                          ratings=ratings,
                          avg_rating=avg_rating,
                          user_rating=user_rating,
                          similar_items=similar_items)

@user_bp.route('/review/<int:review_id>/delete', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """Delete a user's review"""
    try:
        rating = Rating.query.filter_by(id=review_id, user_id=current_user.id).first()
        if not rating:
            return jsonify({'success': False, 'message': 'Review not found or you don\'t have permission to delete it'})
        
        # Delete associated images
        import os
        for image in rating.images:
            if image.image_url and image.image_url.startswith('/static/uploads/'):
                file_path = os.path.join(current_app.root_path, image.image_url.lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            db.session.delete(image)
        
        # Delete the rating
        db.session.delete(rating)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Review deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting review: {str(e)}'})

@user_bp.route('/review/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful or not helpful"""
    try:
        data = request.get_json()
        helpful = data.get('helpful', True)
        
        rating = Rating.query.get_or_404(review_id)
        
        # Initialize helpful_count if not exists
        if not hasattr(rating, 'helpful_count') or rating.helpful_count is None:
            rating.helpful_count = 0
        
        # For simplicity, just increment/decrement the count
        # In a full implementation, you'd track individual user votes
        if helpful:
            rating.helpful_count = (rating.helpful_count or 0) + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'helpful_count': rating.helpful_count or 0,
            'message': 'Thank you for your feedback!'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error recording feedback: {str(e)}'})
