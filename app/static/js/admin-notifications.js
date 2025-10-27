/**
 * Admin Notifications JavaScript for BhojanXpress
 * 
 * This script handles the loading and management of admin notifications
 * in the navbar dropdown. It fetches notifications from the server,
 * displays them, and provides functionality to mark them as read.
 * It also integrates with the notification sound system.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add admin role class to body for sound notifications system
    document.body.classList.add('admin-role');

    // Initialize notification counts
    let newOrders = 0;
    let newMessages = 0;
    let newReviews = 0;
    
    // Check for admin notification elements
    const notificationsContainer = document.getElementById('adminNotificationsContainer');
    if (!notificationsContainer) return;
    
    // Update notification badges
    function updateNotificationBadges() {
        const orderBadge = document.getElementById('orderNotificationBadge');
        const messageBadge = document.getElementById('messageNotificationBadge');
        const reviewBadge = document.getElementById('reviewNotificationBadge');
        const adminBadge = document.getElementById('adminNotificationBadge');
        
        // Update admin main badge
        const totalCount = newOrders + newMessages + newReviews;
        if (adminBadge && totalCount > 0) {
            adminBadge.textContent = totalCount;
            adminBadge.style.display = 'inline-block';
        } else if (adminBadge) {
            adminBadge.style.display = 'none';
        }
        
        // Update orders badge
        if (orderBadge && newOrders > 0) {
            orderBadge.textContent = newOrders;
            orderBadge.style.display = 'inline-block';
        } else if (orderBadge) {
            orderBadge.style.display = 'none';
        }
        
        // Update messages badge
        if (messageBadge && newMessages > 0) {
            messageBadge.textContent = newMessages;
            messageBadge.style.display = 'inline-block';
        } else if (messageBadge) {
            messageBadge.style.display = 'none';
        }
        
        // Update reviews badge
        if (reviewBadge && newReviews > 0) {
            reviewBadge.textContent = newReviews;
            reviewBadge.style.display = 'inline-block';
        } else if (reviewBadge) {
            reviewBadge.style.display = 'none';
        }
    }
    
    // Fetch admin notifications
    function fetchAdminNotifications() {
        // Make a fetch request to get admin notifications
        fetch('/admin/notifications/api/get')
            .then(response => response.json())
            .then(data => {
                // Process order notifications
                if (data.new_orders && data.new_orders > 0) {
                    const newOrderCount = data.new_orders - newOrders;
                    newOrders = data.new_orders;
                    
                    // Play notification sound for new orders
                    if (newOrderCount > 0 && window.BhojanNotifications) {
                        window.BhojanNotifications.play('ADMIN', 'newOrder');
                    }
                }
                
                // Process message notifications
                if (data.new_messages && data.new_messages > 0) {
                    const newMessageCount = data.new_messages - newMessages;
                    newMessages = data.new_messages;
                    
                    // Play notification sound for new messages
                    if (newMessageCount > 0 && window.BhojanNotifications) {
                        window.BhojanNotifications.play('ADMIN', 'userMessage');
                    }
                }
                
                // Process review notifications
                if (data.new_reviews && data.new_reviews > 0) {
                    const newReviewCount = data.new_reviews - newReviews;
                    newReviews = data.new_reviews;
                    
                    // Play notification sound for new reviews
                    if (newReviewCount > 0 && window.BhojanNotifications) {
                        window.BhojanNotifications.play('ADMIN', 'newReview');
                    }
                }
                
                // Update all badges
                updateNotificationBadges();
                
                // Update notifications container if it exists
                if (notificationsContainer) {
                    // Display recent notifications
                    notificationsContainer.innerHTML = '';
                    
                    if (data.notifications && data.notifications.length > 0) {
                        const listGroup = document.createElement('div');
                        listGroup.className = 'list-group list-group-flush';
                        
                        data.notifications.forEach(notification => {
                            const item = document.createElement('a');
                            item.href = notification.url || '#';
                            item.className = 'list-group-item list-group-item-action';
                            
                            let icon = '';
                            switch (notification.type) {
                                case 'order':
                                    icon = '<i class="fas fa-shopping-cart text-success"></i>';
                                    break;
                                case 'message':
                                    icon = '<i class="fas fa-envelope text-primary"></i>';
                                    break;
                                case 'review':
                                    icon = '<i class="fas fa-star text-warning"></i>';
                                    break;
                                default:
                                    icon = '<i class="fas fa-bell text-secondary"></i>';
                            }
                            
                            item.innerHTML = `
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">${icon} ${notification.title}</h6>
                                    <small>${notification.time_ago}</small>
                                </div>
                                <p class="mb-1">${notification.content}</p>
                            `;
                            
                            listGroup.appendChild(item);
                        });
                        
                        notificationsContainer.appendChild(listGroup);
                    } else {
                        notificationsContainer.innerHTML = `
                            <div class="text-center py-4">
                                <i class="fas fa-bell-slash fs-3 text-muted"></i>
                                <p class="mb-0 mt-2">No new notifications</p>
                            </div>
                        `;
                    }
                }
            })
            .catch(error => console.error('Error fetching admin notifications:', error));
    }
    
    // Mark all notifications as read
    function markAllNotificationsAsRead() {
        fetch('/admin/notifications/api/mark-all-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset notification counts
                newOrders = 0;
                newMessages = 0;
                newReviews = 0;
                
                // Update badges
                updateNotificationBadges();
                
                // Update notification dropdown
                fetchAdminNotifications();
            }
        })
        .catch(error => console.error('Error marking notifications as read:', error));
    }
    
    // Set up mark all read button
    const markAllReadBtn = document.getElementById('adminMarkAllReadBtn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            markAllNotificationsAsRead();
        });
    }
    
    // Check for notifications periodically
    fetchAdminNotifications();
    setInterval(fetchAdminNotifications, 60000); // Check every minute
});