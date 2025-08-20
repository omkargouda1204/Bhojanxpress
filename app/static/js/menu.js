// Menu functionality
document.addEventListener('DOMContentLoaded', function() {
    // Category filter functionality
    const categoryLinks = document.querySelectorAll('.category-filter');
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.getAttribute('data-category');
            window.location.href = `/menu?category=${category}`;
        });
    });
    
    // Add to cart functionality
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const quantityInput = this.querySelector('input[name="quantity"]');
            if (!quantityInput.value || quantityInput.value < 1) {
                e.preventDefault();
                alert('Please select a valid quantity');
                return;
            }
        });
    });
    
    // Quantity increment/decrement
    const quantityBtns = document.querySelectorAll('.quantity-btn');
    quantityBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.parentNode.querySelector('input[name="quantity"]');
            const action = this.getAttribute('data-action');
            
            let currentValue = parseInt(input.value) || 0;
            
            if (action === 'increase') {
                currentValue = Math.min(currentValue + 1, 10);
            } else if (action === 'decrease') {
                currentValue = Math.max(currentValue - 1, 1);
            }
            
            input.value = currentValue;
        });
    });
    
    // Search functionality
    const searchForm = document.querySelector('#searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="query"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a search term');
                return;
            }
        });
    }
});

// Quick add to cart function
function quickAddToCart(foodId) {
    fetch(`/add_to_cart/${foodId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: 'quantity=1'
    })
    .then(response => {
        if (response.ok) {
            // Update cart count
            updateCartCount();
            // Show success message
            showNotification('Item added to cart!', 'success');
        } else {
            showNotification('Error adding item to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding item to cart', 'error');
    });
}

function updateCartCount() {
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}
