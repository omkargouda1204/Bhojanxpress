// BhojanXpress Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initializeBootstrap();
    
    // Initialize cart functionality
    initializeCart();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize animations
    initializeAnimations();
});

// Initialize Bootstrap components
function initializeBootstrap() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Cart functionality
function initializeCart() {
    updateCartCount();
    
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const foodId = this.dataset.foodId;
            const foodName = this.dataset.foodName;
            addToCart(foodId, foodName);
        });
    });
    
    // Quantity controls
    document.querySelectorAll('.quantity-btn').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const itemId = this.dataset.itemId;
            updateQuantity(itemId, action);
        });
    });
}

// Add item to cart
function addToCart(foodId, foodName, foodPrice, quantity = 1) {
    // Find button - try multiple selectors to ensure we find the right element
    let button = null;
    // If event is available, use the event target
    if (event && event.target) {
        button = event.target.closest('button') || event.target;
    }
    // Otherwise try to find by data attribute
    else {
        button = document.querySelector(`[data-food-id="${foodId}"]`);
    }

    let originalText = '';

    // Only modify button if found
    if (button) {
        originalText = button.innerHTML;
        // Show loading state
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
        button.disabled = true;
    }

    // Get CSRF token
    const csrfToken = getCSRFToken();

    // Prepare headers
    const headers = {
        'Content-Type': 'application/json'
    };

    // Add CSRF token if available
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    // Send request to add item to cart
    fetch('/add_to_cart/' + foodId, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            quantity: quantity
        })
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return { success: false };
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showAlert('success', `${foodName} added to cart!`);
            updateCartCount(data.cart_count);

            // Update button state if button exists
            if (button) {
                button.innerHTML = '<i class="fas fa-check"></i> Added';
                button.classList.remove('btn-primary', 'btn-warning');
                button.classList.add('btn-success');

                // Reset button after 2 seconds
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-warning');
                    button.disabled = false;
                }, 2000);
            }
        } else {
            throw new Error(data.message || 'Failed to add item to cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', error.message || 'Failed to add item to cart');

        // Reset button if button exists
        if (button) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    });
}

// Update item quantity
function updateQuantity(itemId, action) {
    fetch('/cart/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            item_id: itemId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update quantity display
            const quantityElement = document.querySelector(`#quantity-${itemId}`);
            if (quantityElement) {
                quantityElement.textContent = data.quantity;
            }

            // Update total price
            const totalElement = document.querySelector(`#total-${itemId}`);
            if (totalElement) {
                totalElement.textContent = `$${data.item_total.toFixed(2)}`;
            }
            
            // Update cart total
            const cartTotalElement = document.querySelector('#cart-total');
            if (cartTotalElement) {
                cartTotalElement.textContent = `$${data.cart_total.toFixed(2)}`;
            }
            
            updateCartCount();
            
            // Remove item if quantity is 0
            if (data.quantity === 0) {
                const itemElement = document.querySelector(`#cart-item-${itemId}`);
                if (itemElement) {
                    itemElement.remove();
                }
            }
        } else {
            showAlert('error', data.message || 'Failed to update quantity');
        }
    })
    .catch(error => {
        showAlert('error', 'Failed to update quantity');
    });
}

// Update cart count in navbar
function updateCartCount() {
    fetch('/cart/count')
    .then(response => response.json())
    .then(data => {
        const cartCountElement = document.querySelector('#cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = data.count;
            cartCountElement.style.display = data.count > 0 ? 'inline' : 'none';
        }
    })
    .catch(error => {
        console.error('Failed to update cart count:', error);
    });
}

// Smooth scrolling for anchor links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Form validation
function initializeFormValidation() {
    // Custom validation for forms
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation feedback
    document.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    });
}

// Initialize animations
function initializeAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements with animation class
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Utility functions
function showAlert(type, message, duration = 5000) {
    const alertContainer = document.querySelector('#alert-container') || createAlertContainer();
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
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

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('#search-input');
    const searchResults = document.querySelector('#search-results');
    let searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            } else {
                clearSearchResults();
            }
        });
    }
}

function performSearch(query) {
    fetch(`/search?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        displaySearchResults(data.results);
    })
    .catch(error => {
        console.error('Search failed:', error);
    });
}

function displaySearchResults(results) {
    const searchResults = document.querySelector('#search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="text-muted">No results found</div>';
        return;
    }
    
    const resultsHTML = results.map(item => `
        <div class="search-result-item p-2 border-bottom">
            <div class="d-flex align-items-center">
                <img src="${item.image_url || '/static/images/placeholder.jpg'}" 
                     alt="${item.name}" class="rounded me-3" style="width: 50px; height: 50px; object-fit: cover;">
                <div>
                    <h6 class="mb-1">${item.name}</h6>
                    <small class="text-muted">${item.category}</small>
                    <div class="text-primary fw-bold">$${item.price.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    searchResults.innerHTML = resultsHTML;
}

function clearSearchResults() {
    const searchResults = document.querySelector('#search-results');
    if (searchResults) {
        searchResults.innerHTML = '';
    }
}

// Initialize additional features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();

    // Initialize auto-scrolling for special offers
    initializeSpecialOffersAutoScroll();
});

// Auto-scroll special offers section
function initializeSpecialOffersAutoScroll() {
    const specialOffersContainer = document.querySelector('.special-offers-container');
    const specialOffersScroll = document.querySelector('.special-offers-scroll-area');

    if (specialOffersContainer && specialOffersScroll) {
        // Only initialize auto-scroll if there are enough items to scroll
        if (specialOffersScroll.scrollWidth > specialOffersContainer.clientWidth) {
            let scrollPosition = 0;
            const scrollSpeed = 1; // pixels per frame
            const scrollPauseAtEnd = 2000; // pause at the end for 2 seconds
            let isPaused = false;
            let direction = 1; // 1 for right, -1 for left

            function autoScroll() {
                if (!isPaused) {
                    scrollPosition += scrollSpeed * direction;

                    // If reached the end, pause and then change direction
                    if (scrollPosition >= (specialOffersScroll.scrollWidth - specialOffersContainer.clientWidth)) {
                        isPaused = true;
                        setTimeout(() => {
                            direction = -1;
                            isPaused = false;
                        }, scrollPauseAtEnd);
                    }
                    // If scrolled back to start, pause and then change direction
                    else if (scrollPosition <= 0) {
                        isPaused = true;
                        setTimeout(() => {
                            direction = 1;
                            isPaused = false;
                        }, scrollPauseAtEnd);
                    }

                    specialOffersContainer.scrollLeft = scrollPosition;
                }

                requestAnimationFrame(autoScroll);
            }

            // Start auto-scrolling
            autoScroll();

            // Pause scrolling when user interacts with the section
            specialOffersContainer.addEventListener('mouseenter', function() {
                isPaused = true;
            });

            specialOffersContainer.addEventListener('mouseleave', function() {
                isPaused = false;
            });

            // Handle touch events for mobile
            specialOffersContainer.addEventListener('touchstart', function() {
                isPaused = true;
            });

            specialOffersContainer.addEventListener('touchend', function() {
                // Resume auto-scroll after a short delay
                setTimeout(() => {
                    isPaused = false;
                }, 2000);
            });
        }
    }
}
