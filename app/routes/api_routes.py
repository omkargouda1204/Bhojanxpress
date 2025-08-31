from flask import Blueprint, request, jsonify
from app.models import FoodItem

api_bp = Blueprint('api', __name__)

@api_bp.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    """Returns search suggestions for autocomplete"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
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
    
    suggestions = [{
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
        'category': item.category,
        'image': item.image_path if hasattr(item, 'image_path') and item.image_path else None
    } for item in results]
    
    return jsonify({'suggestions': suggestions})
