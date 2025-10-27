/**
 * Coupon functionality for BhojanXpress
 * Handles copying coupon codes and applying them to the cart
 */

// Copy coupon code to clipboard and show feedback
function copyCouponCode(code) {
    // Get the button that was clicked
    const btn = event ? event.target.closest('.copy-coupon-btn') : null;
    
    // Try multiple methods to copy the text to clipboard
    copyToClipboardWithFallbacks(code)
        .then(() => {
            // Show success message
            if (btn) {
                const originalText = btn.innerHTML;
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
            showToast('Could not copy coupon code. Please try manually copying: ' + code, 'error', 5000);
            
            // Display a modal with the coupon code for manual copying
            showCouponModal(code);
        });
}

/**
 * Robust implementation for copying text to clipboard with multiple fallbacks
 * @param {string} text - The text to copy to clipboard
 * @returns {Promise} - Resolves when copied successfully, rejects on failure
 */
function copyToClipboardWithFallbacks(text) {
    return new Promise((resolve, reject) => {
        // Method 1: Use Clipboard API if available (modern browsers)
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text)
                .then(resolve)
                .catch(err => {
                    console.warn('Clipboard API failed:', err);
                    // Try fallback methods
                    fallbackCopyToClipboard(text, resolve, reject);
                });
        } else {
            // Method 2-3: Try document.execCommand fallbacks
            fallbackCopyToClipboard(text, resolve, reject);
        }
    });
}

/**
 * Fallback methods for copying to clipboard
 */
function fallbackCopyToClipboard(text, resolve, reject) {
    try {
        // Create a temporary input element
        const tempInput = document.createElement('input');
        tempInput.value = text;
        tempInput.style.position = 'fixed';
        tempInput.style.left = '-9999px';
        tempInput.setAttribute('readonly', ''); // Prevent mobile keyboard from appearing
        document.body.appendChild(tempInput);

        // Method 2: Try execCommand('copy') for older browsers
        try {
            tempInput.select();
            tempInput.setSelectionRange(0, 99999); // For mobile devices

            const successful = document.execCommand('copy');
            if (successful) {
                resolve();
                document.body.removeChild(tempInput);
                return;
            }
        } catch (err) {
            console.warn('execCommand copy failed:', err);
        }

        // Method 3: Try textarea + focus + select for edge cases
        try {
            const tempTextarea = document.createElement('textarea');
            tempTextarea.value = text;
            tempTextarea.style.position = 'fixed';
            tempTextarea.style.left = '-9999px';
            document.body.removeChild(tempInput); // Remove the input
            document.body.appendChild(tempTextarea);
            
            tempTextarea.focus();
            tempTextarea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(tempTextarea);
            
            if (successful) {
                resolve();
                return;
            }
        } catch (err) {
            console.warn('textarea copy failed:', err);
        }
        
        // All methods failed
        reject(new Error('Could not copy text to clipboard'));
    } catch (err) {
        reject(err);
    }
}

/**
 * Show a modal with the coupon code for manual copying
 * as a last resort if all clipboard methods fail
 */
function showCouponModal(code) {
    // Create modal container if it doesn't exist
    let modalContainer = document.getElementById('couponModalContainer');
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.id = 'couponModalContainer';
        document.body.appendChild(modalContainer);
    }
    
    // Create modal content
    modalContainer.innerHTML = `
        <div class="modal fade" id="couponModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Your Coupon Code</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center">
                        <p>Please manually copy this coupon code:</p>
                        <div class="p-3 bg-light border rounded mb-3">
                            <h3 class="mb-0 user-select-all">${code}</h3>
                        </div>
                        <small class="text-muted">Triple-click the code above to select it</small>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Show the modal
    const couponModal = new bootstrap.Modal(document.getElementById('couponModal'));
    couponModal.show();
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
