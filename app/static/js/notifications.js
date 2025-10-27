/**
 * Notifications JavaScript for BhojanXpress
 * 
 * This script handles the loading and management of user notifications
 * in the navbar dropdown. It fetches notifications from the server,
 * displays them, and provides functionality to mark them as read.
 */

// Wait for DOM content to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in by looking for notifications dropdown
    const notificationsDropdown = document.getElementById('notificationsDropdown');
    if (!notificationsDropdown) return;

    const notificationsContainer = document.getElementById('notificationsContainer');
    const notificationBadge = document.querySelector('.notification-badge');
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    
    // Variable to track if notifications have been loaded
    let notificationsLoaded = false;

    // Function to load notifications
    function loadNotifications() {
        if (notificationsLoaded) return;
        
        fetch('/notifications/api/get')
            .then(response => response.json())
            .then(data => {
                notificationsLoaded = true;
                
                // Track if we have new unread notifications
                const previousCount = parseInt(notificationBadge.textContent) || 0;
                const newCount = data.unread_count;
                const hasNewNotifications = newCount > previousCount;
                
                // Update the badge with unread count
                if (data.unread_count > 0) {
                    notificationBadge.textContent = data.unread_count;
                    notificationBadge.style.display = 'inline-block';
                    
                    // Play sound for new notifications if we have more than before
                    if (hasNewNotifications) {
                        // Initialize audio context if needed (needs user interaction)
                        if (typeof initAudioContext === 'function') {
                            initAudioContext();
                        }
                        
                        // Play notification sound
                        if (window.BhojanNotifications) {
                            // Get the first unread notification type to determine sound
                            const firstUnread = data.notifications.find(n => !n.is_read);
                            if (firstUnread) {
                                window.BhojanNotifications.play('USER', firstUnread.type);
                            } else {
                                window.BhojanNotifications.play('USER', 'default');
                            }
                        } else {
                            // Fallback sound using simple audio API
                            playFallbackNotificationSound();
                        }
                    }
                } else {
                    notificationBadge.style.display = 'none';
                }
                
                // Clear the loading indicator
                notificationsContainer.innerHTML = '';
                
                // Check if we have any notifications
                if (data.notifications.length === 0) {
                    notificationsContainer.innerHTML = `
                        <div class="text-center py-4">
                            <i class="bi bi-bell-slash fs-3 text-muted"></i>
                            <p class="mb-0 mt-2">No notifications</p>
                        </div>
                    `;
                    return;
                }
                
                // Create a list group to hold the notifications
                const listGroup = document.createElement('div');
                listGroup.className = 'list-group list-group-flush';
                
                // Add each notification to the list
                data.notifications.forEach(notification => {
                    // Create the notification item
                    const item = document.createElement('a');
                    item.href = '#';
                    item.className = `list-group-item list-group-item-action ${notification.is_read ? '' : 'bg-light'}`;
                    item.dataset.id = notification.id;
                    
                    // Set the content based on notification type
                    let icon = '';
                    switch (notification.type) {
                        case 'review_reply':
                            icon = '<i class="bi bi-chat-text text-primary me-2"></i>';
                            break;
                        case 'order_update':
                            icon = '<i class="bi bi-truck text-success me-2"></i>';
                            break;
                        case 'admin_message':
                            icon = '<i class="bi bi-megaphone text-info me-2"></i>';
                            break;
                        default:
                            icon = '<i class="bi bi-bell text-secondary me-2"></i>';
                    }
                    
                    // Construct notification content
                    item.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1 ${notification.is_read ? '' : 'fw-bold'}">
                                ${icon}${notification.title}
                            </h6>
                            <small class="text-muted">${notification.created_at}</small>
                        </div>
                        <p class="mb-1 text-truncate">${notification.content}</p>
                    `;
                    
                    // Add click event to mark as read when clicked
                    item.addEventListener('click', function(e) {
                        e.preventDefault();
                        
                        // Determine the redirect URL based on notification type
                        let redirectUrl = '/notifications';
                        if (notification.type === 'review_reply' && notification.reference_id) {
                            redirectUrl = `/food/${notification.reference_id}`;
                        } else if (notification.type === 'order_update' && notification.reference_id) {
                            redirectUrl = `/my-orders/${notification.reference_id}`;
                        }
                        
                        // Mark as read and redirect
                        markAsRead(notification.id, function() {
                            window.location.href = redirectUrl;
                        });
                    });
                    
                    listGroup.appendChild(item);
                });
                
                notificationsContainer.appendChild(listGroup);
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
                notificationsContainer.innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-exclamation-circle text-danger"></i>
                        <p class="mb-0 mt-2">Failed to load notifications</p>
                    </div>
                `;
            });
    }
    
    // Function to mark a notification as read
    function markAsRead(id, callback) {
        fetch(`/notifications/${id}/mark-read`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the UI
                const notificationItem = document.querySelector(`[data-id="${id}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('bg-light');
                    const title = notificationItem.querySelector('h6');
                    if (title) {
                        title.classList.remove('fw-bold');
                    }
                }
                
                // Update the badge count
                const currentCount = parseInt(notificationBadge.textContent) || 0;
                if (currentCount > 1) {
                    notificationBadge.textContent = currentCount - 1;
                } else {
                    notificationBadge.style.display = 'none';
                }
                
                // Call the callback if provided
                if (typeof callback === 'function') {
                    callback();
                }
            }
        })
        .catch(error => {
            console.error('Error marking notification as read:', error);
        });
    }
    
    // Function to mark all notifications as read
    function markAllAsRead() {
        fetch('/notifications/mark-all-read', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                const unreadItems = document.querySelectorAll('.list-group-item.bg-light');
                unreadItems.forEach(item => {
                    item.classList.remove('bg-light');
                    const title = item.querySelector('h6');
                    if (title) {
                        title.classList.remove('fw-bold');
                    }
                });
                
                // Hide the badge
                notificationBadge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error marking all notifications as read:', error);
        });
    }
    
    // Event listeners
    notificationsDropdown.addEventListener('click', loadNotifications);
    
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent closing the dropdown
            markAllAsRead();
        });
    }
    
    // Fallback notification sound function
    function playFallbackNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/user-notification.mp3');
            audio.volume = 0.5;
            audio.play().catch(e => {
                console.log('Could not play notification sound:', e);
            });
        } catch (e) {
            console.log('Audio not supported');
        }
    }

    // Enable auto-refresh of notifications every 30 seconds
    setInterval(loadNotifications, 30000);
    
    // Check for notifications on page load (optional - uncomment if desired)
    // setTimeout(function() {
    //     fetch('/notifications/api/get?limit=1')
    //         .then(response => response.json())
    //         .then(data => {
    //             if (data.unread_count > 0) {
    //                 notificationBadge.textContent = data.unread_count;
    //                 notificationBadge.style.display = 'inline-block';
    //             }
    //         })
    //         .catch(error => console.error('Error checking notifications:', error));
    // }, 2000);
    
    // Load notifications immediately (if you want them to load without clicking)
    setTimeout(loadNotifications, 1000);
});