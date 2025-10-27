from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
from datetime import datetime, timedelta

from app import db
from app.models import Review, ReviewImage, ReviewHelpful, FoodItem, User, Order, OrderItem
from app.forms import ReviewForm, EditReviewForm, AdminReplyForm, ReviewModerationForm, ReviewFilterForm

review_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_review_image(image_file, review_id):
    """Save and process review image - Fixed to match database schema"""
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        image_file.save(filepath)
        
        try:
            with Image.open(filepath) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                max_size = (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(filepath, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            current_app.logger.error(f"Error processing image: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return None
        
        # Create ReviewImage with correct field names to match database
        review_image = ReviewImage(
            review_id=review_id,
            # New fields
            filename=unique_filename,           # Matches filename field in model
            original_filename=filename,         # Matches original_filename field in model
            file_size=os.path.getsize(filepath),  # Matches file_size field in model
            # Legacy fields (for backward compatibility)
            image_path=f"/static/uploads/reviews/{unique_filename}",  # For legacy image_path column
            image_name=filename,                # For legacy image_name column
            image_size=os.path.getsize(filepath)  # For legacy image_size column
        )
        db.session.add(review_image)
        return review_image
    return None

@review_bp.route('/food/<int:food_item_id>')
def view_reviews(food_item_id):
    """View all reviews for a food item"""
    food_item = FoodItem.query.get_or_404(food_item_id)
    
    # Create filter form with current values
    filter_form = ReviewFilterForm()
    sort_by = request.args.get('sort_by', 'newest')
    rating_filter = request.args.get('rating', type=int)
    verified_only = request.args.get('verified_only', type=bool, default=False)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Set form default values
    filter_form.sort_by.data = sort_by
    if rating_filter:
        filter_form.rating.data = str(rating_filter)
    filter_form.verified_only.data = verified_only
    
    query = Review.query.filter_by(food_item_id=food_item_id, is_approved=True)
    
    if rating_filter:
        query = query.filter_by(rating=rating_filter)
    
    if verified_only:
        query = query.filter_by(is_verified_purchase=True)
    
    if sort_by == 'oldest':
        query = query.order_by(Review.created_at.asc())
    elif sort_by == 'highest_rating':
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_by == 'lowest_rating':
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    elif sort_by == 'most_helpful':
        query = query.order_by(Review.helpful_count.desc(), Review.created_at.desc())
    else:
        query = query.order_by(Review.created_at.desc())
    
    reviews = query.paginate(page=page, per_page=per_page, error_out=False)
    
    rating_stats = db.session.query(
        Review.rating,
        func.count(Review.id).label('count')
    ).filter_by(
        food_item_id=food_item_id,
        is_approved=True
    ).group_by(Review.rating).all()
    
    rating_counts = {i: 0 for i in range(1, 6)}
    for rating, count in rating_stats:
        rating_counts[rating] = count
    
    # Calculate average rating and total reviews
    total_reviews = sum(rating_counts.values())
    if total_reviews > 0:
        weighted_sum = sum(rating * count for rating, count in rating_counts.items())
        average_rating = weighted_sum / total_reviews
    else:
        average_rating = 0.0

    can_add_review = False
    existing_review = None
    if current_user.is_authenticated:
        existing_review = Review.query.filter_by(
            user_id=current_user.id,
            food_item_id=food_item_id
        ).first()
        can_add_review = existing_review is None

    return render_template('reviews/view_reviews.html',
                         food_item=food_item,
                         reviews=reviews,
                         rating_distribution=rating_counts,
                         average_rating=average_rating,
                         total_reviews=total_reviews,
                         can_add_review=can_add_review,
                         existing_review=existing_review,
                         filter_form=filter_form,
                         current_filters={
                             'sort_by': sort_by,
                             'rating': rating_filter,
                             'verified_only': verified_only
                         })

@review_bp.route('/add/<int:food_item_id>', methods=['GET', 'POST'])
@login_required
def add_review(food_item_id):
    """Add a new review"""
    food_item = FoodItem.query.get_or_404(food_item_id)
    
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        food_item_id=food_item_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this item.', 'warning')
        return redirect(url_for('reviews.view_reviews', food_item_id=food_item_id))
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        verified_purchase = False
        order = Order.query.filter_by(user_id=current_user.id, status='delivered').first()
        if order:
            order_item = OrderItem.query.filter_by(
                order_id=order.id,
                food_item_id=food_item_id
            ).first()
            if order_item:
                verified_purchase = True
        
        review = Review(
            user_id=current_user.id,
            food_item_id=food_item_id,
            rating=form.rating.data,
            comment=form.comment.data,
            is_verified_purchase=verified_purchase,
            is_approved=True
        )
        
        db.session.add(review)
        db.session.flush()
        
        images_saved = 0
        for image_file in form.images.data:
            if image_file:
                saved_image = save_review_image(image_file, review.id)
                if saved_image:
                    images_saved += 1
        
        db.session.commit()
        
        flash(f'Review submitted successfully! {images_saved} images uploaded.', 'success')
        return redirect(url_for('reviews.view_reviews', food_item_id=food_item_id))
    
    return render_template('reviews/add_review.html', form=form, food_item=food_item)

@review_bp.route('/edit/<int:review_id>', methods=['GET', 'POST', 'PUT'])
@login_required
def edit_review(review_id):
    """Edit an existing review - Fixed to handle both POST and PUT methods"""
    review = Review.query.get_or_404(review_id)
    
    # Check if the current user owns this review
    if review.user_id != current_user.id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'You can only edit your own reviews.'}), 403
        flash('You can only edit your own reviews.', 'error')
        return redirect(url_for('reviews.view_reviews', food_item_id=review.food_item_id))
    
    # Handle both POST and PUT methods for AJAX requests
    if request.method in ['POST', 'PUT']:
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
                rating = data.get('rating')
                comment = data.get('comment', '').strip()
            else:
                rating = request.form.get('rating')
                comment = request.form.get('comment', '').strip()

            if not rating:
                return jsonify({
                    'success': False,
                    'message': 'Rating is required'
                }), 400

            # Update the existing review (don't create new one)
            review.rating = int(rating)
            review.comment = comment
            review.updated_at = datetime.utcnow()
            
            # Handle image uploads if present
            images_saved = 0
            if request.files:
                files = request.files.getlist('images')
                for file in files[:5]:  # Limit to 5 images
                    if file and allowed_file(file.filename):
                        review_image = save_review_image(file, review.id)
                        if review_image:
                            images_saved += 1
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': f'Review updated successfully! {images_saved} images added.',
                    'review': {
                        'id': review.id,
                        'rating': review.rating,
                        'comment': review.comment,
                        'updated_at': review.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
            
            flash(f'Review updated successfully! {images_saved} images added.', 'success')
            return redirect(url_for('user.food_detail', food_id=review.food_item_id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating review {review_id}: {str(e)}")
            
            if request.is_json:
                return jsonify({'success': False, 'message': 'Failed to update review.'}), 500

            flash('Failed to update review.', 'error')

    # GET request - return review data for editing
    if request.method == 'GET' and request.is_json:
        return jsonify({
            'success': True,
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'food_item_id': review.food_item_id
            }
        })

    # Regular GET request - show edit form
    form = EditReviewForm(obj=review)
    return render_template('reviews/edit_review.html', form=form, review=review)

@review_bp.route('/admin/reviews/<int:review_id>/reply', methods=['POST'])
@login_required
def admin_reply_review(review_id):
    """Admin reply to a review"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
    review = Review.query.get_or_404(review_id)
    
    try:
        data = request.get_json()
        admin_reply = data.get('admin_reply', '').strip()
        
        if not admin_reply:
            return jsonify({'success': False, 'message': 'Reply text is required'})
        
        # Update the review with admin reply
        review.admin_reply = admin_reply
        review.admin_reply_at = datetime.utcnow()
        review.replied_by_admin_id = current_user.id
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Reply sent successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error replying to review {review_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while sending the reply'})

@review_bp.route('/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful or unhelpful"""
    try:
        review = Review.query.get_or_404(review_id)

        # Check if user already marked this review
        existing = ReviewHelpful.query.filter_by(
            user_id=current_user.id,
            review_id=review_id
        ).first()

        if existing:
            # Toggle the helpful status
            existing.is_helpful = not existing.is_helpful
            action = 'marked helpful' if existing.is_helpful else 'unmarked as helpful'
        else:
            # Create new helpful record
            helpful = ReviewHelpful(
                user_id=current_user.id,
                review_id=review_id,
                is_helpful=True
            )
            db.session.add(helpful)
            action = 'marked helpful'

        # Update helpful count
        helpful_count = ReviewHelpful.query.filter_by(
            review_id=review_id,
            is_helpful=True
        ).count()

        review.helpful_count = helpful_count
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Review {action}',
            'helpful_count': helpful_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error marking review helpful: {e}')
        return jsonify({
            'success': False,
            'message': 'Failed to update helpful status'
        }), 500

@review_bp.route('/<int:review_id>/delete', methods=['DELETE', 'POST'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    try:
        review = Review.query.get_or_404(review_id)

        if review.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'You can only delete your own reviews'
            }), 403

        food_item_id = review.food_item_id

        # Delete associated images
        for image in review.images:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews', image.filename)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    current_app.logger.error(f'Error deleting image file: {e}')

        # Delete the review (cascade will handle related records)
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review deleted successfully',
            'redirect_url': url_for('reviews.view_reviews', food_item_id=food_item_id)
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting review: {e}')
        return jsonify({
            'success': False,
            'message': 'Failed to delete review'
        }), 500

@review_bp.route('/submit', methods=['POST'])
@login_required
def submit_review():
    """Submit a new review or update existing review via AJAX with image upload support"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            food_item_id = data.get('food_item_id')
            rating = data.get('rating')
            comment = data.get('comment', '').strip()
            edit_review_id = data.get('edit_review_id')
        else:
            food_item_id = request.form.get('food_item_id')
            rating = request.form.get('rating')
            comment = request.form.get('comment', '').strip()
            edit_review_id = request.form.get('edit_review_id')

        if not food_item_id or not rating:
            return jsonify({
                'success': False,
                'message': 'Food item and rating are required'
            }), 400

        food_item = FoodItem.query.get_or_404(food_item_id)

        # Check if this is an edit request
        if edit_review_id and edit_review_id.strip():
            # Handle edit mode - update existing review
            review = Review.query.get_or_404(edit_review_id)
            
            # Verify ownership
            if review.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'You can only edit your own reviews'
                }), 403
            
            # Update existing review
            review.rating = int(rating)
            review.comment = comment
            review.updated_at = datetime.utcnow()
            
            operation = 'updated'
        else:
            # Handle new review mode - check for duplicates first
            existing_review = Review.query.filter_by(
                user_id=current_user.id,
                food_item_id=food_item_id
            ).first()
            
            if existing_review:
                return jsonify({
                    'success': False,
                    'message': 'You have already reviewed this item. Use the edit option to update your review.'
                }), 400

            # Check if it's a verified purchase
            verified_purchase = False
            order = Order.query.filter_by(user_id=current_user.id, status='delivered').first()
            if order:
                order_item = OrderItem.query.filter_by(
                    order_id=order.id,
                    food_item_id=food_item_id
                ).first()
                if order_item:
                    verified_purchase = True

            # Create new review
            review = Review(
                user_id=current_user.id,
                food_item_id=food_item_id,
                rating=int(rating),
                comment=comment,
                is_verified_purchase=verified_purchase,
                is_approved=True
            )

            db.session.add(review)
            operation = 'submitted'

        db.session.flush()  # Get the review ID for image uploads

        # Handle image uploads if present
        images_saved = 0
        if request.files:
            files = request.files.getlist('images')
            for file in files[:5]:  # Limit to 5 images
                if file and allowed_file(file.filename):
                    review_image = save_review_image(file, review.id)
                    if review_image:
                        images_saved += 1

        db.session.commit()

        message = f'Review {operation} successfully!'
        if images_saved > 0:
            message += f' {images_saved} images uploaded.'

        return jsonify({
            'success': True,
            'message': message,
            'review_id': review.id,
            'redirect_url': url_for('user.food_detail', food_id=food_item_id)
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error submitting review: {e}')
        return jsonify({
            'success': False,
            'message': 'Failed to submit review. Please try again.'
        }), 500

@review_bp.route('/admin')
@login_required
def admin_reviews():
    """Admin review management page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    per_page = 20

    # Base query with joins
    query = Review.query.join(FoodItem).join(User)

    # Apply status filter
    if status_filter == 'pending':
        query = query.filter(Review.is_approved == False)
    elif status_filter == 'approved':
        query = query.filter(Review.is_approved == True)
    elif status_filter == 'flagged':
        query = query.filter(Review.is_flagged == True)

    # Get reviews with pagination
    reviews_pagination = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Calculate statistics
    total_reviews = Review.query.count()
    average_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
    recent_reviews_count = Review.query.filter(
        Review.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    unreplied_count = Review.query.filter(
        db.or_(Review.admin_reply.is_(None), Review.admin_reply == '')
    ).count()

    # Prepare review data with user and food item info
    reviews_data = []
    for review in reviews_pagination.items:
        review_data = {
            'review': review,
            'user': review.user,
            'food_item': review.food_item
        }
        reviews_data.append(review_data)

    return render_template('admin/manage_reviews.html',
                         reviews=reviews_data,
                         pagination=reviews_pagination,
                         status_filter=status_filter,
                         total_reviews=total_reviews,
                         average_rating=average_rating,
                         recent_reviews_count=recent_reviews_count,
                         unreplied_count=unreplied_count)

@review_bp.route('/admin/moderate/<int:review_id>', methods=['POST'])
@login_required
def moderate_review(review_id):
    """Moderate a review (approve/reject/delete)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    review = Review.query.get_or_404(review_id)

    try:
        data = request.get_json()
        action = data.get('action')

        if action == 'approve':
            review.is_approved = True
            review.is_flagged = False
            message = 'Review approved successfully.'
        elif action == 'reject':
            review.is_approved = False
            message = 'Review rejected.'
        elif action == 'flag':
            review.is_flagged = True
            message = 'Review flagged for attention.'
        elif action == 'delete':
            # Delete associated image files
            for image in review.images:
                filepath = os.path.join(
                    current_app.root_path,
                    'static', 'uploads', 'reviews',
                    image.filename
                )
                if os.path.exists(filepath):
                    os.remove(filepath)

            db.session.delete(review)
            message = 'Review deleted successfully.'
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400

        db.session.commit()
        return jsonify({'success': True, 'message': message})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error moderating review {review_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while processing the request'})

@review_bp.route('/api/get/<int:food_item_id>')
def get_reviews_api(food_item_id):
    """Get reviews for a food item via API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        reviews_query = Review.query.filter_by(
            food_item_id=food_item_id,
            is_approved=True
        ).order_by(Review.created_at.desc())

        reviews = reviews_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        reviews_data = []
        for review in reviews.items:
            review_data = {
                'id': review.id,
                'user_name': review.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
                'helpful_count': review.helpful_count or 0,
                'is_verified_purchase': review.is_verified_purchase,
                'admin_reply': review.admin_reply,
                'admin_reply_at': review.admin_reply_at.strftime('%Y-%m-%d %H:%M') if review.admin_reply_at else None
            }
            reviews_data.append(review_data)

        return jsonify({
            'success': True,
            'reviews': reviews_data,
            'pagination': {
                'page': reviews.page,
                'pages': reviews.pages,
                'per_page': reviews.per_page,
                'total': reviews.total,
                'has_next': reviews.has_next,
                'has_prev': reviews.has_prev
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error getting reviews for food item {food_item_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load reviews'
        }), 500

@review_bp.route('/admin/reviews/<int:review_id>/reply', methods=['POST'])
@login_required
def admin_reply_to_review(review_id):
    """Admin reply to a specific review"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    review = Review.query.get_or_404(review_id)

    try:
        data = request.get_json()
        reply_text = data.get('reply', '').strip()

        if not reply_text:
            return jsonify({'success': False, 'message': 'Reply text is required'}), 400

        # Update review with admin reply
        review.admin_reply = reply_text
        review.admin_reply_date = datetime.utcnow()
        review.admin_reply_by = current_user.id

        db.session.commit()

        # Send notification to the user who wrote the review
        try:
            from app.models import Notification
            notification = Notification(
                user_id=review.user_id,
                title='Admin replied to your review',
                content=f'Admin has replied to your review for {review.food_item.name}: "{reply_text[:100]}..."',
                notification_type='admin_review_reply',
                reference_id=review_id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"Failed to send notification: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Reply added successfully',
            'reply': reply_text
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding admin reply: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add reply'}), 500

@review_bp.route('/admin/reviews/<int:review_id>/delete-reply', methods=['DELETE'])
@login_required
def delete_admin_reply(review_id):
    """Delete admin reply from a review"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    review = Review.query.get_or_404(review_id)

    try:
        review.admin_reply = None
        review.admin_reply_date = None
        review.admin_reply_by = None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Reply deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting admin reply: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete reply'}), 500

@review_bp.route('/admin/reviews/<int:review_id>/delete', methods=['DELETE'])
@login_required
def admin_delete_review(review_id):
    """Delete a review completely (Admin function)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    review = Review.query.get_or_404(review_id)

    try:
        # Delete associated review images
        for image in review.images:
            try:
                image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews', image.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to delete image file: {str(e)}")

        # Delete the review and all associated data
        db.session.delete(review)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting review: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete review'}), 500

@review_bp.route('/admin/reviews/<int:review_id>/flag', methods=['POST'])
@login_required
def flag_review(review_id):
    """Flag a review for attention"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    review = Review.query.get_or_404(review_id)

    try:
        review.is_flagged = True
        review.flagged_by = current_user.id
        review.flagged_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review flagged successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error flagging review: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to flag review'}), 500
