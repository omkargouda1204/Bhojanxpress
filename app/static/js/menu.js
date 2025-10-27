// Enhanced Menu functionality with auto-filtering and responsive design
document.addEventListener('DOMContentLoaded', function() {
    initializeMenu();
});

// Global variables for menu state
let allItems = [];
let filteredItems = [];
let activeFilters = {
    categories: [],
    minPrice: null,
    maxPrice: null,
    availability: 'all'
};

function initializeMenu() {
    // Store all items for filtering
    const foodItems = document.querySelectorAll('.food-item');
    allItems = Array.from(foodItems);
    filteredItems = [...allItems];

    // Initialize all event listeners
    initializeSidebarToggle();
    initializeFilters();
    initializeSorting();
    initializeCartFunctionality();
    
    // Apply initial filters if any
    applyFilters();
}

function initializeSidebarToggle() {
    // Desktop sidebar toggle
    const desktopToggle = document.getElementById('desktopSidebarToggle');
    const filterSidebar = document.getElementById('filterSidebar');
    const menuContent = document.getElementById('menuContent');

    if (desktopToggle && filterSidebar && menuContent) {
        desktopToggle.addEventListener('click', function() {
            filterSidebar.classList.toggle('d-none');
            
            // Adjust main content width
            if (filterSidebar.classList.contains('d-none')) {
                menuContent.classList.remove('col-lg-9');
                menuContent.classList.add('col-lg-12');
                this.innerHTML = '<i class="fas fa-bars me-2"></i>Show Filters';
            } else {
                menuContent.classList.remove('col-lg-12');
                menuContent.classList.add('col-lg-9');
                this.innerHTML = '<i class="fas fa-times me-2"></i>Hide Filters';
            }
        });
    }

    // Mobile filter toggle
    const mobileToggle = document.getElementById('toggleFiltersBtn');
    if (mobileToggle && filterSidebar) {
        mobileToggle.addEventListener('click', function() {
            filterSidebar.classList.toggle('show');
            
            // Update button text
            const isOpen = filterSidebar.classList.contains('show');
            this.innerHTML = isOpen ? 
                '<i class="fas fa-times me-2"></i>Close Filters' : 
                '<i class="fas fa-filter me-2"></i>Show Filters';
        });
    }
}

function initializeFilters() {
    // Clear all filters button
    const clearAllBtn = document.getElementById('clearAllFiltersBtn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllFilters);
    }

    // Category filters - auto-apply on change
    const categoryCheckboxes = document.querySelectorAll('input[name="categoryFilter"]');
    categoryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateActiveFilters();
            applyFilters();
            updateActiveFilterDisplay();
        });
    });

    // Price range filters - auto-apply on change
    const minPriceSelect = document.getElementById('minPriceSelect');
    const maxPriceSelect = document.getElementById('maxPriceSelect');
    
    if (minPriceSelect) {
        minPriceSelect.addEventListener('change', function() {
            updateActiveFilters();
            applyFilters();
            updateActiveFilterDisplay();
        });
    }
    
    if (maxPriceSelect) {
        maxPriceSelect.addEventListener('change', function() {
            updateActiveFilters();
            applyFilters();
            updateActiveFilterDisplay();
        });
    }

    // Availability filter
    const availabilitySelect = document.getElementById('availabilityFilter');
    if (availabilitySelect) {
        availabilitySelect.addEventListener('change', function() {
            updateActiveFilters();
            applyFilters();
            updateActiveFilterDisplay();
        });
    }
}

function initializeSorting() {
    // Sort dropdown options
    const sortOptions = document.querySelectorAll('.sort-option');
    sortOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const sortType = this.getAttribute('data-sort');
            const sortLabel = this.textContent.trim();
            
            // Update dropdown button text
            const sortButton = document.getElementById('sortLabel');
            if (sortButton) {
                sortButton.textContent = sortLabel;
            }
            
            sortItems(sortType);
        });
    });
}

function initializeCartFunctionality() {
    // Quantity increment/decrement buttons
    const quantityBtns = document.querySelectorAll('.quantity-btn');
    quantityBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.parentNode.querySelector('input[name="quantity"]');
            const action = this.getAttribute('data-action');
            
            let currentValue = parseInt(input.value) || 1;
            
            if (action === 'increase') {
                currentValue = Math.min(currentValue + 1, 10);
            } else if (action === 'decrease') {
                currentValue = Math.max(currentValue - 1, 1);
            }
            
            input.value = currentValue;
        });
    });

    // Add to cart form submissions
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const quantityInput = this.querySelector('input[name="quantity"]');
            if (!quantityInput.value || quantityInput.value < 1) {
                e.preventDefault();
                showNotification('Please select a valid quantity', 'warning');
                return;
            }
        });
    });
}

function updateActiveFilters() {
    // Update categories
    activeFilters.categories = [];
    const checkedCategories = document.querySelectorAll('input[name="categoryFilter"]:checked');
    checkedCategories.forEach(checkbox => {
        if (checkbox.value !== 'all') {
            activeFilters.categories.push(checkbox.value);
        }
    });

    // Update price range
    const minPriceSelect = document.getElementById('minPriceSelect');
    const maxPriceSelect = document.getElementById('maxPriceSelect');
    
    activeFilters.minPrice = minPriceSelect?.value ? parseFloat(minPriceSelect.value) : null;
    activeFilters.maxPrice = maxPriceSelect?.value ? parseFloat(maxPriceSelect.value) : null;

    // Update availability
    const availabilitySelect = document.getElementById('availabilityFilter');
    activeFilters.availability = availabilitySelect?.value || 'all';
}

function applyFilters() {
    filteredItems = allItems.filter(item => {
        // Category filter
        if (activeFilters.categories.length > 0) {
            const itemCategory = item.getAttribute('data-category');
            if (!activeFilters.categories.includes(itemCategory)) {
                return false;
            }
        }

        // Price filter
        const itemPrice = parseFloat(item.getAttribute('data-price'));
        if (activeFilters.minPrice !== null && itemPrice < activeFilters.minPrice) {
            return false;
        }
        if (activeFilters.maxPrice !== null && itemPrice > activeFilters.maxPrice) {
            return false;
        }

        // Availability filter
        const itemAvailable = item.getAttribute('data-available') === 'true';
        if (activeFilters.availability === 'available' && !itemAvailable) {
            return false;
        }
        if (activeFilters.availability === 'unavailable' && itemAvailable) {
            return false;
        }

        return true;
    });

    // Update display
    updateItemDisplay();
    updateResultsCount();
    
    // Hide mobile filters after applying
    closeMobileFilters();
}

function updateItemDisplay() {
    // Hide all items first
    allItems.forEach(item => {
        item.style.display = 'none';
    });

    // Show filtered items
    filteredItems.forEach(item => {
        item.style.display = 'block';
    });

    // Show no results message if needed
    updateNoResultsMessage();
}

function updateNoResultsMessage() {
    const container = document.getElementById('foodItemsContainer');
    if (!container) return;

    // Remove existing no results message
    const existingMessage = container.querySelector('.no-results-message');
    if (existingMessage) {
        existingMessage.remove();
    }

    // Add no results message if needed
    if (filteredItems.length === 0) {
        const noResultsDiv = document.createElement('div');
        noResultsDiv.className = 'no-results-message col-12 text-center py-5';
        noResultsDiv.innerHTML = `
            <div class="text-muted">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h4>No items found</h4>
                <p>Try adjusting your filters to see more results.</p>
                <button class="btn btn-outline-primary" onclick="clearAllFilters()">
                    <i class="fas fa-refresh me-2"></i>Clear All Filters
                </button>
            </div>
        `;
        container.appendChild(noResultsDiv);
    }
}

function updateResultsCount() {
    const resultText = document.querySelector('.results-count');
    if (resultText) {
        const itemText = filteredItems.length === 1 ? 'item' : 'items';
        resultText.textContent = `Showing ${filteredItems.length} ${itemText}`;
    }
}

function updateActiveFilterDisplay() {
    // Could add filter badges here in the future
    const clearBtn = document.getElementById('clearAllFiltersBtn');
    if (clearBtn) {
        const hasActiveFilters = activeFilters.categories.length > 0 || 
                               activeFilters.minPrice !== null || 
                               activeFilters.maxPrice !== null || 
                               activeFilters.availability !== 'all';
        
        clearBtn.style.display = hasActiveFilters ? 'block' : 'none';
    }
}

function clearAllFilters() {
    // Clear category checkboxes
    const categoryCheckboxes = document.querySelectorAll('input[name="categoryFilter"]');
    categoryCheckboxes.forEach(checkbox => {
        checkbox.checked = checkbox.value === 'all';
    });

    // Clear price selects
    const minPriceSelect = document.getElementById('minPriceSelect');
    const maxPriceSelect = document.getElementById('maxPriceSelect');
    if (minPriceSelect) minPriceSelect.value = '';
    if (maxPriceSelect) maxPriceSelect.value = '';

    // Clear availability filter
    const availabilitySelect = document.getElementById('availabilityFilter');
    if (availabilitySelect) availabilitySelect.value = 'all';

    // Update and apply filters
    updateActiveFilters();
    applyFilters();
    updateActiveFilterDisplay();

    showNotification('All filters cleared', 'info');
}

function sortItems(sortType) {
    const container = document.getElementById('foodItemsContainer');
    if (!container) return;

    const sortedItems = [...filteredItems].sort((a, b) => {
        switch (sortType) {
            case 'name':
                const nameA = a.querySelector('.card-title').textContent.trim().toLowerCase();
                const nameB = b.querySelector('.card-title').textContent.trim().toLowerCase();
                return nameA.localeCompare(nameB);
            
            case 'price-low':
                const priceA = parseFloat(a.getAttribute('data-price'));
                const priceB = parseFloat(b.getAttribute('data-price'));
                return priceA - priceB;
            
            case 'price-high':
                const priceC = parseFloat(a.getAttribute('data-price'));
                const priceD = parseFloat(b.getAttribute('data-price'));
                return priceD - priceC;
            
            case 'newest':
                // Keep original order for now
                return 0;
            
            default:
                return 0;
        }
    });

    // Re-arrange items in DOM
    sortedItems.forEach(item => {
        container.appendChild(item);
    });

    showNotification(`Sorted by ${sortType.replace('-', ' ')}`, 'info');
}

function closeMobileFilters() {
    const filterSidebar = document.getElementById('filterSidebar');
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    
    if (window.innerWidth < 992 && filterSidebar && filterSidebar.classList.contains('show')) {
        filterSidebar.classList.remove('show');
        
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-filter me-2"></i>Show Filters';
        }
    }
}

// Cart functionality
function quickAddToCart(foodId) {
    fetch(`/add_to_cart/${foodId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: 'quantity=1'
    })
    .then(response => {
        if (response.ok) {
            updateCartCount();
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

function addToCart(foodId, quantity = 1) {
    fetch(`/add_to_cart/${foodId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: `quantity=${quantity}`
    })
    .then(response => {
        if (response.ok) {
            updateCartCount();
            showNotification(`${quantity} item(s) added to cart!`, 'success');
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
                cartCount.textContent = data.count || 0;
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.menu-notification');
    existingNotifications.forEach(notification => notification.remove());

    // Create new notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${getBootstrapAlertClass(type)} alert-dismissible fade show position-fixed menu-notification`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
    notification.innerHTML = `
        <strong>${getNotificationIcon(type)}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 4 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

function getBootstrapAlertClass(type) {
    const classes = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return classes[type] || 'info';
}

function getNotificationIcon(type) {
    const icons = {
        'success': '<i class="fas fa-check-circle"></i>',
        'error': '<i class="fas fa-exclamation-circle"></i>',
        'warning': '<i class="fas fa-exclamation-triangle"></i>',
        'info': '<i class="fas fa-info-circle"></i>'
    };
    return icons[type] || '<i class="fas fa-info-circle"></i>';
}

// Window resize handler for responsive behavior
window.addEventListener('resize', function() {
    const filterSidebar = document.getElementById('filterSidebar');
    const desktopToggle = document.getElementById('desktopSidebarToggle');
    const menuContent = document.getElementById('menuContent');
    
    if (window.innerWidth >= 992) {
        // Desktop - ensure sidebar is visible and toggle button works
        if (filterSidebar && filterSidebar.classList.contains('show')) {
            filterSidebar.classList.remove('show');
        }
    } else {
        // Mobile - reset desktop sidebar state
        if (filterSidebar && filterSidebar.classList.contains('d-none')) {
            filterSidebar.classList.remove('d-none');
            if (menuContent) {
                menuContent.classList.remove('col-lg-12');
                menuContent.classList.add('col-lg-9');
            }
            if (desktopToggle) {
                desktopToggle.innerHTML = '<i class="fas fa-times me-2"></i>Hide Filters';
            }
        }
    }
});
