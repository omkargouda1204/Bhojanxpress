// AJAX Add to Cart functionality
function addToCart(foodId, foodName, foodPrice, quantity = 1) {
    // Get CSRF token - check both meta tag and input field to ensure compatibility
    let csrfToken = null;
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfInput = document.querySelector('input[name="csrf_token"]');

    if (csrfMeta) {
        csrfToken = csrfMeta.getAttribute('content');
    } else if (csrfInput) {
        csrfToken = csrfInput.value;
    }

    // If button was clicked, show loading state
    let button = null;
    if (event && event.target) {
        button = event.target.closest('button') || event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        button.disabled = true;

        // Store original text for later
        button.setAttribute('data-original-text', originalText);
    }

    // Prepare headers
    const headers = {
        'Content-Type': 'application/json'
    };

    // Add CSRF token if available
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    fetch(`/add_to_cart/${foodId}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            quantity: quantity
        })
    })
    .then(response => {
        if (response.redirected) {
            // User is not logged in, redirect to login
            window.location.href = response.url;
            return { success: false };
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update cart count badge
            updateCartCount(data.cart_count);

            // Show success message
            showNotification(data.message || `${foodName} added to cart!`, 'success');

            // Update button with success indicator if it exists
            if (button) {
                button.innerHTML = '<i class="fas fa-check"></i> Added!';
                button.classList.remove('btn-primary', 'btn-warning');
                button.classList.add('btn-success');

                setTimeout(() => {
                    const originalText = button.getAttribute('data-original-text');
                    button.innerHTML = originalText;
                    button.disabled = false;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-warning');
                }, 2000);
            }
        } else {
            // Show error message
            showNotification(data.message || 'Error adding item to cart', 'error');

            // Restore button if it exists
            if (button) {
                const originalText = button.getAttribute('data-original-text');
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding item to cart', 'error');

        // Restore button if it exists
        if (button) {
            const originalText = button.getAttribute('data-original-text');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    });
}

// Update cart count badge
function updateCartCount(count) {
    const cartBadges = document.querySelectorAll('.cart-count, #cartCount');
    if (cartBadges.length > 0) {
        cartBadges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        });
    }
}

// Show notification toast
function showNotification(message, type = 'info') {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    // Add toast to container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Initialize and show toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Initialize cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in (you can set this variable in your base template)
    const cartCountElements = document.querySelectorAll('.cart-count, #cartCount');
    if (cartCountElements.length > 0) {
        fetch('/cart/count')
            .then(response => response.json())
            .then(data => updateCartCount(data.count))
            .catch(error => console.error('Error loading cart count:', error));
    }
});
