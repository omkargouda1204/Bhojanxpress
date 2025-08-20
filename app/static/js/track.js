// Order tracking functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize order tracking if on tracking page
    if (document.getElementById('order-tracking')) {
        initializeOrderTracking();
    }
    
    // Auto-refresh order status
    if (document.querySelector('.order-status')) {
        startStatusPolling();
    }
    
    // Order timeline animations
    animateOrderTimeline();
});

function initializeOrderTracking() {
    const trackingContainer = document.getElementById('order-tracking');
    if (!trackingContainer) return;
    
    const orderId = trackingContainer.getAttribute('data-order-id');
    const orderStatus = trackingContainer.getAttribute('data-order-status');
    
    // Create tracking timeline
    createTrackingTimeline(orderStatus);
    
    // Start real-time updates
    if (['pending', 'confirmed', 'preparing'].includes(orderStatus)) {
        startRealTimeTracking(orderId);
    }
}

function createTrackingTimeline(currentStatus) {
    const statuses = [
        { key: 'pending', label: 'Order Placed', icon: 'fas fa-shopping-cart' },
        { key: 'confirmed', label: 'Order Confirmed', icon: 'fas fa-check-circle' },
        { key: 'preparing', label: 'Preparing Food', icon: 'fas fa-utensils' },
        { key: 'delivered', label: 'Delivered', icon: 'fas fa-truck' }
    ];
    
    const timeline = document.createElement('div');
    timeline.className = 'order-timeline';
    
    statuses.forEach((status, index) => {
        const isActive = getStatusIndex(currentStatus) >= index;
        const isCurrent = currentStatus === status.key;
        
        const timelineItem = document.createElement('div');
        timelineItem.className = `timeline-item ${isActive ? 'active' : ''} ${isCurrent ? 'current' : ''}`;
        
        timelineItem.innerHTML = `
            <div class="timeline-marker">
                <i class="${status.icon}"></i>
            </div>
            <div class="timeline-content">
                <h6>${status.label}</h6>
                <small class="text-muted">
                    ${isActive ? 'Completed' : 'Pending'}
                </small>
            </div>
        `;
        
        timeline.appendChild(timelineItem);
    });
    
    const trackingContainer = document.getElementById('order-tracking');
    trackingContainer.appendChild(timeline);
}

function getStatusIndex(status) {
    const statusOrder = ['pending', 'confirmed', 'preparing', 'delivered'];
    return statusOrder.indexOf(status);
}

function startRealTimeTracking(orderId) {
    const intervalId = setInterval(() => {
        fetch(`/api/order/${orderId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.status) {
                    updateOrderStatus(data.status, data.estimatedDelivery);
                    
                    // Stop polling if order is delivered or cancelled
                    if (['delivered', 'cancelled'].includes(data.status)) {
                        clearInterval(intervalId);
                    }
                }
            })
            .catch(error => {
                console.log('Error fetching order status:', error);
            });
    }, 30000); // Check every 30 seconds
    
    // Store interval ID to clear it later
    window.orderTrackingInterval = intervalId;
}

function updateOrderStatus(newStatus, estimatedDelivery) {
    // Update status badge
    const statusBadge = document.querySelector('.order-status-badge');
    if (statusBadge) {
        statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
        statusBadge.className = `badge badge-${newStatus} order-status-badge`;
    }
    
    // Update timeline
    const timeline = document.querySelector('.order-timeline');
    if (timeline) {
        timeline.remove();
        createTrackingTimeline(newStatus);
    }
    
    // Update estimated delivery time
    if (estimatedDelivery) {
        const deliveryTimeElement = document.getElementById('estimated-delivery');
        if (deliveryTimeElement) {
            deliveryTimeElement.textContent = estimatedDelivery;
        }
    }
    
    // Show notification
    showStatusNotification(newStatus);
}

function showStatusNotification(status) {
    const messages = {
        confirmed: 'Your order has been confirmed!',
        preparing: 'Your food is being prepared!',
        delivered: 'Your order has been delivered! Enjoy your meal!'
    };
    
    if (messages[status]) {
        showToast(messages[status], 'success');
    }
}

function startStatusPolling() {
    // Only poll for active orders
    const activeOrders = document.querySelectorAll('.order-card[data-status="pending"], .order-card[data-status="confirmed"], .order-card[data-status="preparing"]');
    
    if (activeOrders.length === 0) return;
    
    const intervalId = setInterval(() => {
        activeOrders.forEach(orderCard => {
            const orderId = orderCard.getAttribute('data-order-id');
            
            fetch(`/api/order/${orderId}/status`)
                .then(response => response.json())
                .then(data => {
                    if (data.status) {
                        const statusBadge = orderCard.querySelector('.order-status');
                        if (statusBadge) {
                            statusBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                            statusBadge.className = `badge badge-${data.status} order-status`;
                        }
                        
                        orderCard.setAttribute('data-status', data.status);
                    }
                })
                .catch(error => {
                    console.log('Error polling order status:', error);
                });
        });
    }, 60000); // Check every minute
    
    window.statusPollingInterval = intervalId;
}

function animateOrderTimeline() {
    const timelineItems = document.querySelectorAll('.timeline-item');
    
    timelineItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            item.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, 50);
        }, index * 200);
    });
}

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container or create one
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1080';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Clean up intervals when leaving page
window.addEventListener('beforeunload', function() {
    if (window.orderTrackingInterval) {
        clearInterval(window.orderTrackingInterval);
    }
    if (window.statusPollingInterval) {
        clearInterval(window.statusPollingInterval);
    }
});
