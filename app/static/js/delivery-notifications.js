// Delivery Agent Notifications

// Constants
const NOTIFICATION_CHECK_INTERVAL = 30000; // 30 seconds
const NOTIFICATION_SOUND = new Audio('/static/sounds/notification.mp3');
let notificationMuted = localStorage.getItem('deliveryNotificationMuted') === 'true';

// Function to format date/time nicely
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const options = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return date.toLocaleDateString('en-US', options);
}

// Update the mute button state
function updateMuteButtonState() {
    const muteButton = document.getElementById('toggleNotificationSoundDelivery');
    if (muteButton) {
        muteButton.innerHTML = notificationMuted ? 
            '<i class="fas fa-volume-mute"></i>' : 
            '<i class="fas fa-volume-up"></i>';
        muteButton.setAttribute('title', notificationMuted ? 'Unmute notifications' : 'Mute notifications');
    }
}

// Toggle notification sound
function toggleNotificationSound() {
    notificationMuted = !notificationMuted;
    localStorage.setItem('deliveryNotificationMuted', notificationMuted);
    updateMuteButtonState();
}

// Play notification sound if not muted
function playNotificationSound() {
    if (!notificationMuted) {
        NOTIFICATION_SOUND.play().catch(e => {
            console.log('Failed to play notification sound:', e);
        });
    }
}

// Fetch notifications from the API
function fetchNotifications() {
    fetch('/delivery/notifications/api/get')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateNotificationBadge(data.total_notifications);
                updateNotificationDropdown(data.notifications);
            }
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
        });
}

// Update the notification badge with count
function updateNotificationBadge(count) {
    const badge = document.getElementById('agentNotificationBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Update the notification dropdown with notifications
function updateNotificationDropdown(notifications) {
    const container = document.getElementById('agentNotificationsContainer');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="text-center py-3 text-muted">No notifications</div>';
        return;
    }
    
    let html = '';
    notifications.forEach(notification => {
        let icon = 'fas fa-bell';
        
        if (notification.type === 'order') {
            icon = 'fas fa-box';
        } else if (notification.type === 'update') {
            icon = 'fas fa-info-circle';
        } else if (notification.type === 'payment') {
            icon = 'fas fa-money-bill-wave';
        }
        
        html += `
        <a href="${notification.link}" class="dropdown-item p-2 border-bottom">
            <div class="d-flex align-items-center">
                <div class="notification-icon bg-light rounded-circle p-2 me-3">
                    <i class="${icon} text-primary"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-0">${notification.title}</h6>
                    <p class="text-muted mb-0 small">${notification.message}</p>
                    <small class="text-muted">${formatDateTime(notification.timestamp)}</small>
                </div>
            </div>
        </a>`;
    });
    
    container.innerHTML = html;
}

// Initialize notifications
document.addEventListener('DOMContentLoaded', function() {
    updateMuteButtonState();
    
    // Add event listener to mute/unmute button
    const muteButton = document.getElementById('toggleNotificationSoundDelivery');
    if (muteButton) {
        muteButton.addEventListener('click', toggleNotificationSound);
    }
    
    // Initial fetch
    fetchNotifications();
    
    // Set up interval to check for new notifications
    setInterval(fetchNotifications, NOTIFICATION_CHECK_INTERVAL);
});