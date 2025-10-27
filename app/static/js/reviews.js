/**
 * Enhanced Review System JavaScript
 * Handles all review operations: submit, edit, delete, helpful votes, admin replies
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeReviewSystem();
});

function initializeReviewSystem() {
    // Initialize all review-related functionality
    initializeReviewSubmission();
    initializeReviewEditing();
    initializeReviewDeletion();
    initializeHelpfulVotes();
    initializeAdminReplySystem();
    initializeReviewModeration();
}

// Review Submission
function initializeReviewSubmission() {
    const reviewForms = document.querySelectorAll('.review-form, #reviewForm');

    reviewForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReview(this);
        });
    });
}

function submitReview(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    // Show loading state
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
    submitBtn.disabled = true;

    // Get form data
    const reviewData = {
        food_item_id: formData.get('food_item_id'),
        rating: formData.get('rating'),
        comment: formData.get('comment')
    };

    // Validate required fields
    if (!reviewData.rating) {
        showAlert('error', 'Please select a rating');
        resetButton(submitBtn, originalText);
        return;
    }

    fetch('/reviews/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(reviewData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);

            // Reset form
            form.reset();

            // Refresh the reviews section or redirect
            if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            } else {
                // Refresh reviews section if available
                refreshReviewsSection();
            }
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error submitting review:', error);
        showAlert('error', 'Failed to submit review. Please try again.');
    })
    .finally(() => {
        resetButton(submitBtn, originalText);
    });
}

// Review Editing
function initializeReviewEditing() {
    const editButtons = document.querySelectorAll('.edit-review-btn');

    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            openEditModal(reviewId);
        });
    });
}

function openEditModal(reviewId) {
    // Create or show edit modal
    let modal = document.getElementById('editReviewModal');
    if (!modal) {
        createEditModal();
        modal = document.getElementById('editReviewModal');
    }

    // Load review data
    fetch(`/reviews/edit/${reviewId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Populate modal with review data
            document.getElementById('editReviewId').value = data.review.id;
            document.getElementById('editRating').value = data.review.rating;
            document.getElementById('editComment').value = data.review.comment;

            // Update star ratings
            updateStarRating('editRating', data.review.rating);

            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error loading review:', error);
        showAlert('error', 'Failed to load review data.');
    });
}

function createEditModal() {
    const modalHTML = `
    <div class="modal fade" id="editReviewModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Review</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="editReviewForm">
                        <input type="hidden" id="editReviewId" name="review_id">

                        <div class="mb-3">
                            <label class="form-label">Rating</label>
                            <div class="star-rating" data-rating="0">
                                <span class="star" data-value="1">★</span>
                                <span class="star" data-value="2">★</span>
                                <span class="star" data-value="3">★</span>
                                <span class="star" data-value="4">★</span>
                                <span class="star" data-value="5">★</span>
                            </div>
                            <input type="hidden" id="editRating" name="rating" required>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Comment</label>
                            <textarea id="editComment" name="comment" class="form-control" rows="4" placeholder="Share your experience..."></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="saveEditedReview()">Save Changes</button>
                </div>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Initialize star rating for edit modal
    initializeStarRating('#editReviewModal .star-rating');
}

function saveEditedReview() {
    const form = document.getElementById('editReviewForm');
    const formData = new FormData(form);

    const reviewData = {
        rating: formData.get('rating'),
        comment: formData.get('comment')
    };

    const reviewId = formData.get('review_id');

    if (!reviewData.rating) {
        showAlert('error', 'Please select a rating');
        return;
    }

    fetch(`/reviews/edit/${reviewId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(reviewData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editReviewModal'));
            modal.hide();

            // Refresh the page or update the review display
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error updating review:', error);
        showAlert('error', 'Failed to update review. Please try again.');
    });
}

// Review Deletion
function initializeReviewDeletion() {
    const deleteButtons = document.querySelectorAll('.delete-review-btn');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            const reviewText = this.dataset.reviewText || 'this review';

            if (confirm(`Are you sure you want to delete ${reviewText}?`)) {
                deleteReview(reviewId);
            }
        });
    });
}

function deleteReview(reviewId) {
    fetch(`/reviews/${reviewId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);

            // Remove review element from DOM or redirect
            if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                // Remove the review element
                const reviewElement = document.querySelector(`[data-review-id="${reviewId}"]`);
                if (reviewElement) {
                    reviewElement.remove();
                }
            }
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting review:', error);
        showAlert('error', 'Failed to delete review. Please try again.');
    });
}

// Helpful Votes
function initializeHelpfulVotes() {
    const helpfulButtons = document.querySelectorAll('.helpful-btn');

    helpfulButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            markHelpful(reviewId, this);
        });
    });
}

function markHelpful(reviewId, button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    button.disabled = true;

    fetch(`/reviews/${reviewId}/helpful`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update helpful count display
            const countElement = button.querySelector('.helpful-count');
            if (countElement) {
                countElement.textContent = data.helpful_count;
            }

            // Update button text
            button.innerHTML = `<i class="fas fa-thumbs-up"></i> Helpful (${data.helpful_count})`;

            showAlert('success', data.message);
        } else {
            showAlert('error', data.message);
            button.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error marking review helpful:', error);
        showAlert('error', 'Failed to mark review as helpful.');
        button.innerHTML = originalText;
    })
    .finally(() => {
        button.disabled = false;
    });
}

// Admin Reply System
function initializeAdminReplySystem() {
    const replyButtons = document.querySelectorAll('.admin-reply-btn');

    replyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            openAdminReplyModal(reviewId);
        });
    });
}

function openAdminReplyModal(reviewId) {
    let modal = document.getElementById('adminReplyModal');
    if (!modal) {
        createAdminReplyModal();
        modal = document.getElementById('adminReplyModal');
    }

    // Set review ID
    document.getElementById('adminReplyReviewId').value = reviewId;
    document.getElementById('adminReplyText').value = '';

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function createAdminReplyModal() {
    const modalHTML = `
    <div class="modal fade" id="adminReplyModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Reply to Review</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="adminReplyForm">
                        <input type="hidden" id="adminReplyReviewId" name="review_id">
                        <div class="mb-3">
                            <label class="form-label">Admin Reply</label>
                            <textarea id="adminReplyText" name="admin_reply" class="form-control" rows="4"
                                      placeholder="Write your reply to this review..." required></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="sendAdminReply()">Send Reply</button>
                </div>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function sendAdminReply() {
    const form = document.getElementById('adminReplyForm');
    const formData = new FormData(form);
    const reviewId = formData.get('review_id');
    const adminReply = formData.get('admin_reply').trim();

    if (!adminReply) {
        showAlert('error', 'Please enter a reply message');
        return;
    }

    fetch(`/reviews/admin/reviews/${reviewId}/reply`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ admin_reply: adminReply })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('adminReplyModal'));
            modal.hide();

            // Refresh the page to show the reply
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending admin reply:', error);
        showAlert('error', 'Failed to send reply. Please try again.');
    });
}

// Review Moderation (Admin)
function initializeReviewModeration() {
    const moderationButtons = document.querySelectorAll('.moderate-btn');

    moderationButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            const action = this.dataset.action;
            moderateReview(reviewId, action);
        });
    });
}

function moderateReview(reviewId, action) {
    let confirmMessage = '';
    switch(action) {
        case 'approve':
            confirmMessage = 'Approve this review?';
            break;
        case 'reject':
            confirmMessage = 'Reject this review?';
            break;
        case 'delete':
            confirmMessage = 'Permanently delete this review?';
            break;
        case 'flag':
            confirmMessage = 'Flag this review for attention?';
            break;
    }

    if (!confirm(confirmMessage)) {
        return;
    }

    fetch(`/reviews/admin/moderate/${reviewId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);

            // Refresh the page or update the UI
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error moderating review:', error);
        showAlert('error', 'Failed to moderate review. Please try again.');
    });
}

// Star Rating System
function initializeStarRating(selector) {
    const starContainers = document.querySelectorAll(selector || '.star-rating');

    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const hiddenInput = container.parentNode.querySelector('input[type="hidden"]') ||
                           container.querySelector('input[type="hidden"]');

        stars.forEach(star => {
            star.addEventListener('click', function() {
                const rating = this.dataset.value;
                updateStarRating(container, rating);
                if (hiddenInput) {
                    hiddenInput.value = rating;
                }
            });

            star.addEventListener('mouseover', function() {
                const rating = this.dataset.value;
                highlightStars(container, rating);
            });
        });

        container.addEventListener('mouseleave', function() {
            const currentRating = hiddenInput ? hiddenInput.value : container.dataset.rating;
            highlightStars(container, currentRating);
        });
    });
}

function updateStarRating(container, rating) {
    if (typeof container === 'string') {
        container = document.querySelector(`#${container}`).parentNode.querySelector('.star-rating');
    }

    const stars = container.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
            star.style.color = '#ffc107';
        } else {
            star.classList.remove('active');
            star.style.color = '#ddd';
        }
    });

    container.dataset.rating = rating;
}

function highlightStars(container, rating) {
    const stars = container.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.style.color = '#ffc107';
        } else {
            star.style.color = '#ddd';
        }
    });
}

// Utility Functions
function showAlert(type, message, duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-auto-dismiss');
    existingAlerts.forEach(alert => alert.remove());

    const alertContainer = document.querySelector('#alert-container') || createAlertContainer();

    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show alert-auto-dismiss`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.appendChild(alertElement);

    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertElement.parentNode) {
            alertElement.remove();
        }
    }, duration);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function resetButton(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

function refreshReviewsSection() {
    // Refresh reviews if there's a reviews container
    const reviewsContainer = document.querySelector('.reviews-container, #reviewsSection');
    if (reviewsContainer) {
        location.reload(); // Simple refresh for now
    }
}

// Initialize star ratings on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeStarRating();
});

// CSS for star ratings
const starRatingCSS = `
<style>
.star-rating {
    display: inline-block;
    font-size: 1.5rem;
    cursor: pointer;
}

.star-rating .star {
    color: #ddd;
    transition: color 0.2s ease;
    cursor: pointer;
    margin-right: 2px;
}

.star-rating .star:hover,
.star-rating .star.active {
    color: #ffc107;
}

.star-rating .star:hover ~ .star {
    color: #ddd;
}

.review-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.review-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.helpful-btn {
    transition: all 0.2s ease;
}

.helpful-btn:hover {
    background-color: #0d6efd;
    color: white;
}

.admin-reply {
    background-color: #f8f9fa;
    border-left: 4px solid #0d6efd;
    padding: 15px;
    margin-top: 10px;
    border-radius: 5px;
}

.review-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.review-actions .btn {
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
}
</style>
`;

// Inject CSS
document.head.insertAdjacentHTML('beforeend', starRatingCSS);
