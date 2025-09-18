/**
 * Coupon functionality for BhojanXpress
 * Handles copying coupon codes and applying them to the cart
 */

// Copy coupon code to clipboard and show feedback
function copyCouponCode(code) {
    // Create a temporary input element
    const tempInput = document.createElement('input');
    tempInput.value = code;
    document.body.appendChild(tempInput);

    // Select the text
    tempInput.select();
    tempInput.setSelectionRange(0, 99999); // For mobile devices

    // Copy the text to clipboard
    navigator.clipboard.writeText(code)
        .then(() => {
            // Show success message
            const btn = event.target.closest('.copy-coupon-btn');
            if (btn) {
                const originalText = btn.textContent;
                btn.innerHTML = '<i class="fas fa-check me-1"></i> Copied!';
                btn.classList.add('btn-success');
                btn.classList.remove('btn-light');

                // Restore original state after 2 seconds
                setTimeout(() => {
                    btn.innerHTML = '<i class="fas fa-copy me-1"></i> Copy Code';
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-light');
                }, 2000);
            }

            // Display toast notification
            showToast(`Coupon ${code} copied to clipboard!`, 'success');

            // If we're on the checkout page, offer to apply the coupon
            if (window.location.href.includes('checkout') || window.location.href.includes('cart')) {
                const couponInput = document.getElementById('coupon_code');
                if (couponInput) {
                    couponInput.value = code;
                    showToast('Coupon added! Click "Apply" to use it.', 'info', 5000);
                }
            } else {
                // Offer to go to cart with coupon
                showActionToast(
                    'Coupon copied! Apply it to your cart?',
                    'Go to Cart',
                    () => {
                        // Store coupon in localStorage to auto-apply it
                        localStorage.setItem('pendingCoupon', code);
                        window.location.href = '/cart';
                    }
                );
            }
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            showToast('Could not copy coupon code. Please try again.', 'error');
        });

    // Remove the temporary input
    document.body.removeChild(tempInput);
}

// Show a toast notification
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('id', toastId);

    // Create toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    // Add toast to container
    toastContainer.appendChild(toast);

    // Initialize and show toast
    const toastElement = new bootstrap.Toast(toast, {
        delay: duration,
        autohide: true
    });
    toastElement.show();

    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Show a toast with an action button
function showActionToast(message, actionText, actionCallback, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('id', toastId);

    // Create toast content with action button
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <div class="me-2 m-auto">
                <button type="button" class="btn btn-sm btn-light action-btn">${actionText}</button>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    // Add toast to container
    toastContainer.appendChild(toast);

    // Add action button event listener
    toast.querySelector('.action-btn').addEventListener('click', function() {
        if (typeof actionCallback === 'function') {
            actionCallback();
        }
        bootstrap.Toast.getInstance(toast).hide();
    });

    // Initialize and show toast
    const toastElement = new bootstrap.Toast(toast, {
        delay: duration,
        autohide: true
    });
    toastElement.show();

    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Auto-apply coupon from localStorage if available (for cart page)
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the cart page
    if (window.location.href.includes('cart') || window.location.href.includes('checkout')) {
        const pendingCoupon = localStorage.getItem('pendingCoupon');
        if (pendingCoupon) {
            // Try to find the coupon input field
            const couponInput = document.getElementById('coupon_code');
            if (couponInput) {
                couponInput.value = pendingCoupon;

                // Show notification
                showToast(`Coupon ${pendingCoupon} applied! Click "Apply" to use it.`, 'info', 5000);

                // Clear the pending coupon
                localStorage.removeItem('pendingCoupon');

                // Try to find and click the apply button
                const applyButton = document.querySelector('.apply-coupon-btn');
                if (applyButton) {
                    setTimeout(() => {
                        applyButton.click();
                    }, 500);
                }
            }
        }
    }
});
