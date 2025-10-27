/**
 * Enhanced Notification System JavaScript
 * Handles notification deletion, mark as read, and admin management
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeNotificationSystem();
});

function initializeNotificationSystem() {
    // Initialize notification deletion
    initializeNotificationDeletion();

    // Initialize mark as read functionality
    initializeMarkAsRead();

    // Initialize mark all as read
    initializeMarkAllAsRead();

    // Initialize admin notification management
    initializeAdminNotificationManagement();
}

// Notification Deletion
function initializeNotificationDeletion() {
    const deleteButtons = document.querySelectorAll('.delete-notification-btn, .notification-delete');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const notificationId = this.dataset.notificationId || this.dataset.id;
            const confirmMessage = this.dataset.confirmMessage || 'Are you sure you want to delete this notification?';

            if (confirm(confirmMessage)) {
                deleteNotification(notificationId, this);
            }
        });
    });
}

function deleteNotification(notificationId, buttonElement) {
    const originalText = buttonElement.innerHTML;
    buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    buttonElement.disabled = true;

    fetch(`/notifications/${notificationId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove notification from DOM
            const notificationElement = buttonElement.closest('.notification-item, .list-group-item, .card');
            if (notificationElement) {
                notificationElement.style.transition = 'all 0.3s ease';
                notificationElement.style.opacity = '0';
                notificationElement.style.transform = 'translateX(100%)';

                setTimeout(() => {
                    notificationElement.remove();
                    updateNotificationBadge();
                }, 300);
            }

            showNotificationAlert('success', 'Notification deleted successfully');
        } else {
            showNotificationAlert('error', data.message || 'Failed to delete notification');
            buttonElement.innerHTML = originalText;
            buttonElement.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error deleting notification:', error);
        showNotificationAlert('error', 'Failed to delete notification');
        buttonElement.innerHTML = originalText;
        buttonElement.disabled = false;
    });
}

// Mark as Read Functionality
function initializeMarkAsRead() {
    const markReadButtons = document.querySelectorAll('.mark-read-btn, .notification-mark-read');

    markReadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const notificationId = this.dataset.notificationId || this.dataset.id;
            markNotificationAsRead(notificationId, this);
        });
    });

    // Also mark as read when notification is clicked
    const notificationItems = document.querySelectorAll('.notification-item, .notification-link');
    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId || this.dataset.id;
            if (notificationId && !this.classList.contains('read')) {
                markNotificationAsRead(notificationId, null, false); // Silent marking
            }
        });
    });
}

function markNotificationAsRead(notificationId, buttonElement, showAlert = true) {
    fetch(`/notifications/${notificationId}/mark-read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update notification appearance
            const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"], [data-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.classList.remove('unread', 'bg-light');
                notificationElement.classList.add('read');

                // Update text styling
                const titleElement = notificationElement.querySelector('.notification-title, h6');
                if (titleElement) {
                    titleElement.classList.remove('fw-bold');
                }

                // Hide mark as read button
                if (buttonElement) {
                    buttonElement.style.display = 'none';
                }
            }

            updateNotificationBadge();

            if (showAlert) {
                showNotificationAlert('success', 'Notification marked as read');
            }
        } else {
            if (showAlert) {
                showNotificationAlert('error', data.message || 'Failed to mark notification as read');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
        if (showAlert) {
            showNotificationAlert('error', 'Failed to mark notification as read');
        }
    });
}

// Mark All as Read
function initializeMarkAllAsRead() {
    const markAllReadButtons = document.querySelectorAll('.mark-all-read-btn, #markAllReadBtn');

    markAllReadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (confirm('Mark all notifications as read?')) {
                markAllNotificationsAsRead(this);
            }
        });
    });
}

function markAllNotificationsAsRead(buttonElement) {
    const originalText = buttonElement.innerHTML;
    buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Marking all as read...';
    buttonElement.disabled = true;

    fetch('/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update all notification appearances
            const unreadNotifications = document.querySelectorAll('.notification-item.unread, .list-group-item.bg-light');
            unreadNotifications.forEach(notification => {
                notification.classList.remove('unread', 'bg-light');
                notification.classList.add('read');

                const titleElement = notification.querySelector('.notification-title, h6');
                if (titleElement) {
                    titleElement.classList.remove('fw-bold');
                }
            });

            // Hide all mark as read buttons
            const markReadButtons = document.querySelectorAll('.mark-read-btn');
            markReadButtons.forEach(btn => btn.style.display = 'none');

            updateNotificationBadge();
            showNotificationAlert('success', 'All notifications marked as read');
        } else {
            showNotificationAlert('error', data.message || 'Failed to mark all notifications as read');
        }
    })
    .catch(error => {
        console.error('Error marking all notifications as read:', error);
        showNotificationAlert('error', 'Failed to mark all notifications as read');
    })
    .finally(() => {
        buttonElement.innerHTML = originalText;
        buttonElement.disabled = false;
    });
}

// Admin Notification Management
function initializeAdminNotificationManagement() {
    // Bulk actions
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    bulkActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const selectedNotifications = getSelectedNotifications();

            if (selectedNotifications.length === 0) {
                showNotificationAlert('warning', 'Please select notifications to perform bulk actions');
                return;
            }

            if (confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${selectedNotifications.length} selected notifications?`)) {
                performBulkAction(action, selectedNotifications);
            }
        });
    });

    // Select all checkbox
    const selectAllCheckbox = document.querySelector('#selectAllNotifications');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.notification-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
}

function getSelectedNotifications() {
    const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
    return Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
}

function performBulkAction(action, notificationIds) {
    fetch('/admin/notifications/bulk-action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            action: action,
            notification_ids: notificationIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotificationAlert('success', data.message);
            // Refresh the page to show updated notifications
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotificationAlert('error', data.message || 'Bulk action failed');
        }
    })
    .catch(error => {
        console.error('Error performing bulk action:', error);
        showNotificationAlert('error', 'Bulk action failed');
    });
}

// Update Notification Badge
function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge, #notificationBadge');
    if (!badge) return;

    fetch('/notifications/api/get?limit=1')
    .then(response => response.json())
    .then(data => {
        if (data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error updating notification badge:', error);
    });
}

// Utility Functions
function showNotificationAlert(type, message, duration = 3000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.notification-alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertContainer = document.querySelector('#notification-alert-container') || createNotificationAlertContainer();

    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show notification-alert`;
    alertElement.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
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

function createNotificationAlertContainer() {
    const container = document.createElement('div');
    container.id = 'notification-alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '10000';
    document.body.appendChild(container);
    return container;
}

function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// Auto-refresh notifications every 30 seconds
setInterval(updateNotificationBadge, 30000);

// Real-time notification updates (if WebSocket is available)
if (typeof io !== 'undefined') {
    const socket = io();

    socket.on('new_notification', function(data) {
        updateNotificationBadge();
        showNotificationAlert('info', 'You have a new notification!');
    });
}
