from datetime import datetime, timedelta
from flask import flash
import re

def format_currency(amount):
    """Format amount as currency."""
    return f"₹{amount:.2f}"

def calculate_delivery_time(preparation_time=30):
    """Calculate estimated delivery time."""
    current_time = datetime.now()
    delivery_time = current_time + timedelta(minutes=preparation_time + 30)  # 30 min for delivery
    return delivery_time

def validate_phone_number(phone):
    """Validate Indian phone number format."""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def flash_errors(form):
    """Flash form validation errors."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'error')

def get_cart_total(cart_items):
    """Calculate total amount for cart items."""
    total = 0
    for item in cart_items:
        total += item.food_item.price * item.quantity
    return total

def get_order_summary(order):
    """Get order summary for display."""
    return {
        'id': order.id,
        'total_amount': format_currency(order.total_amount),
        'status': order.status.title(),
        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M'),
        'estimated_delivery': order.estimated_delivery.strftime('%Y-%m-%d %H:%M') if order.estimated_delivery else 'TBD',
        'items_count': len(order.order_items)
    }

def paginate_query(query, page, per_page=10):
    """Paginate SQLAlchemy query."""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def search_food_items(query, category=None):
    """Search food items by name and optionally filter by category."""
    from app.models import FoodItem
    
    search_query = FoodItem.query.filter(FoodItem.is_available == True)
    
    if query:
        search_query = search_query.filter(
            FoodItem.name.ilike(f'%{query}%') |
            FoodItem.description.ilike(f'%{query}%')
        )
    
    if category and category != 'all':
        search_query = search_query.filter(FoodItem.category == category)
    
    return search_query.all()
