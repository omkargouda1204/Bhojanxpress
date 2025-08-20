// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    // Quantity controls
    const quantityButtons = document.querySelectorAll('.quantity-btn');
    
    quantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const input = action === 'increase' ? 
                this.previousElementSibling : this.nextElementSibling;
            
            let currentValue = parseInt(input.value);
            
            if (action === 'increase' && currentValue < 10) {
                input.value = currentValue + 1;
            } else if (action === 'decrease' && currentValue > 1) {
                input.value = currentValue - 1;
            }
            
            // Trigger change event for auto-submit forms
            input.dispatchEvent(new Event('change'));
        });
    });
    
    // Auto-submit cart update forms
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity-input');
    cartQuantityInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.form.submit();
            }, 1000); // Wait 1 second after user stops typing
        });
    });
    
    // Update cart count in navbar
    updateCartCount();
});

function updateCartCount() {
    // This would typically make an AJAX call to get current cart count
    // For now, we'll just set it based on localStorage or make a simple fetch
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = data.count || 0;
                cartCountElement.style.display = data.count > 0 ? 'inline' : 'none';
            }
        })
        .catch(error => {
            console.log('Could not update cart count:', error);
        });
}

// Add to cart with animation
function addToCartWithAnimation(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = '<i class="fas fa-check"></i> Added!';
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-primary');
            button.disabled = false;
            updateCartCount();
        }, 1500);
    }, 500);
}

// Add event listeners for add to cart buttons
document.addEventListener('DOMContentLoaded', function() {
    const addToCartForms = document.querySelectorAll('form[action*="add_to_cart"]');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                addToCartWithAnimation(submitButton);
            }
        });
    });
});
