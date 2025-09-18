from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import FoodItem, Order, OrderItem, User  # Import from models/__init__.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new models directly from the main models.py file
import importlib.util
spec = importlib.util.spec_from_file_location("main_models", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models.py"))
main_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_models)

# Get the models from the main models.py file
Review = main_models.Review
ReviewImage = main_models.ReviewImage
NutritionalInfo = main_models.NutritionalInfo

from app.forms import ReviewForm
import os
from werkzeug.utils import secure_filename
import uuid

review_bp = Blueprint('reviews', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@review_bp.route('/add/<int:food_item_id>')
@login_required
def add_review(food_item_id):
    """Show form to add a new review"""
    food_item = FoodItem.query.get_or_404(food_item_id)

    # Check if user has ordered this item (optional verification)
    order_id = request.args.get('order_id')
    verified_purchase = False

    if order_id:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
        if order:
            order_item = OrderItem.query.filter_by(
                order_id=order.id,
                food_item_id=food_item_id
            ).first()
            if order_item:
                verified_purchase = True

    form = ReviewForm()
    form.food_item_id.data = food_item_id
    if order_id:
        form.order_id.data = order_id

    return render_template('reviews/add_review.html',
                         form=form,
                         food_item=food_item,
                         verified_purchase=verified_purchase)

@review_bp.route('/submit', methods=['POST'])
@login_required
def submit_review():
    """Submit a new review"""
    form = ReviewForm()

    if form.validate_on_submit():
        food_item_id = form.food_item_id.data
        food_item = FoodItem.query.get_or_404(food_item_id)

        # Check if user has already reviewed this item (allow multiple reviews)
        # Create new review
        review = Review(
            user_id=current_user.id,
            food_item_id=food_item_id,
            order_id=form.order_id.data if form.order_id.data else None,
            rating=int(form.rating.data),
            title=form.title.data,
            comment=form.comment.data,
            is_verified_purchase=bool(form.order_id.data)
        )

        db.session.add(review)
        db.session.flush()  # Get the review ID

        # Handle multiple image uploads
        uploaded_files = request.files.getlist('images')
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)

                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
                os.makedirs(upload_dir, exist_ok=True)

                # Save file
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)

                # Create review image record
                review_image = ReviewImage(
                    review_id=review.id,
                    image_url=f'/static/uploads/reviews/{filename}',
                    image_filename=filename
                )
                db.session.add(review_image)

        db.session.commit()
        flash('Your review has been submitted successfully!', 'success')
        return redirect(url_for('user.food_item_details', id=food_item_id))

    # If form validation fails, redirect back with errors
    food_item_id = form.food_item_id.data
    if food_item_id:
        return redirect(url_for('review.add_review', food_item_id=food_item_id))

    flash('Error submitting review. Please try again.', 'error')
    return redirect(url_for('user.home'))

@review_bp.route('/edit/<int:review_id>')
@login_required
def edit_review(review_id):
    """Show form to edit an existing review"""
    review = Review.query.get_or_404(review_id)

    # Check if current user owns this review
    if review.user_id != current_user.id:
        flash('You can only edit your own reviews.', 'error')
        return redirect(url_for('user.food_item_details', id=review.food_item_id))

    form = ReviewForm(obj=review)
    form.food_item_id.data = review.food_item_id
    form.order_id.data = review.order_id
    form.rating.data = str(review.rating)

    return render_template('reviews/edit_review.html',
                         form=form,
                         review=review,
                         food_item=review.food_item)

@review_bp.route('/update/<int:review_id>', methods=['POST'])
@login_required
def update_review(review_id):
    """Update an existing review"""
    review = Review.query.get_or_404(review_id)

    # Check if current user owns this review
    if review.user_id != current_user.id:
        flash('You can only edit your own reviews.', 'error')
        return redirect(url_for('user.food_item_details', id=review.food_item_id))

    form = ReviewForm()

    if form.validate_on_submit():
        # Update review fields
        review.rating = int(form.rating.data)
        review.title = form.title.data
        review.comment = form.comment.data
        review.updated_at = datetime.utcnow()

        # Handle new image uploads
        uploaded_files = request.files.getlist('images')
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)

                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
                os.makedirs(upload_dir, exist_ok=True)

                # Save file
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)

                # Create review image record
                review_image = ReviewImage(
                    review_id=review.id,
                    image_url=f'/static/uploads/reviews/{filename}',
                    image_filename=filename
                )
                db.session.add(review_image)

        db.session.commit()
        flash('Your review has been updated successfully!', 'success')
        return redirect(url_for('user.food_item_details', id=review.food_item_id))

    flash('Error updating review. Please try again.', 'error')
    return redirect(url_for('review.edit_review', review_id=review_id))

@review_bp.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    review = Review.query.get_or_404(review_id)

    # Check if current user owns this review
    if review.user_id != current_user.id:
        flash('You can only delete your own reviews.', 'error')
        return redirect(url_for('user.food_item_details', id=review.food_item_id))

    food_item_id = review.food_item_id

    # Delete associated images from filesystem
    for image in review.review_images:
        if image.image_filename:
            image_path = os.path.join(
                current_app.root_path,
                'static', 'uploads', 'reviews',
                image.image_filename
            )
            if os.path.exists(image_path):
                os.remove(image_path)

    # Delete review (images will be deleted via cascade)
    db.session.delete(review)
    db.session.commit()

    flash('Your review has been deleted.', 'success')
    return redirect(url_for('user.food_item_details', id=food_item_id))

@review_bp.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_review_image(image_id):
    """Delete a specific review image"""
    image = ReviewImage.query.get_or_404(image_id)
    review = image.review

    # Check if current user owns this review
    if review.user_id != current_user.id:
        flash('You can only delete images from your own reviews.', 'error')
        return redirect(url_for('user.food_item_details', id=review.food_item_id))

    # Delete image from filesystem
    if image.image_filename:
        image_path = os.path.join(
            current_app.root_path,
            'static', 'uploads', 'reviews',
            image.image_filename
        )
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete image record
    db.session.delete(image)
    db.session.commit()

    flash('Image deleted successfully.', 'success')
    return redirect(url_for('review.edit_review', review_id=review.id))

@review_bp.route('/food_item/<int:food_item_id>')
def view_reviews(food_item_id):
    """View all reviews for a food item"""
    food_item = FoodItem.query.get_or_404(food_item_id)
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'newest')  # newest, oldest, highest_rated, lowest_rated

    # Base query
    query = Review.query.filter_by(food_item_id=food_item_id)

    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(Review.created_at.asc())
    elif sort_by == 'highest_rated':
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_by == 'lowest_rated':
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    else:  # newest (default)
        query = query.order_by(Review.created_at.desc())

    reviews = query.paginate(
        page=page, per_page=10, error_out=False
    )

    # Calculate review statistics
    all_reviews = Review.query.filter_by(food_item_id=food_item_id).all()
    total_reviews = len(all_reviews)
    avg_rating = sum(r.rating for r in all_reviews) / total_reviews if total_reviews > 0 else 0

    # Rating distribution
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in all_reviews:
        rating_counts[review.rating] += 1

    # Check if current user has reviewed this item
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            user_id=current_user.id,
            food_item_id=food_item_id
        ).first()

    stats = {
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_counts': rating_counts
    }

    return render_template('reviews/view_reviews.html',
                         food_item=food_item,
                         reviews=reviews,
                         stats=stats,
                         sort_by=sort_by,
                         user_review=user_review)

@review_bp.route('/my_reviews')
@login_required
def my_reviews():
    """View current user's reviews"""
    page = request.args.get('page', 1, type=int)

    reviews = Review.query.filter_by(user_id=current_user.id)\
                         .order_by(Review.created_at.desc())\
                         .paginate(page=page, per_page=10, error_out=False)

    return render_template('reviews/my_reviews.html', reviews=reviews)
