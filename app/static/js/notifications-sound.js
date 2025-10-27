/**
 * Sound Notification System for BhojanXpress
 * 
 * This script handles notification sounds for different types of alerts
 * across user roles (customer, admin, delivery agent)
 */

// Notification sound types
const NotificationSounds = {
    USER: {
        orderUpdate: '/static/sounds/user-order-update.mp3',
        adminMessage: '/static/sounds/user-admin-message.mp3',
        reviewReply: '/static/sounds/user-review-reply.mp3',
        default: '/static/sounds/user-notification.mp3'
    },
    ADMIN: {
        newOrder: '/static/sounds/admin-new-order.mp3',
        userMessage: '/static/sounds/admin-user-message.mp3',
        newReview: '/static/sounds/admin-new-review.mp3',
        default: '/static/sounds/admin-notification.mp3'
    },
    DELIVERY: {
        newAssignment: '/static/sounds/delivery-new-assignment.mp3',
        paymentUpdate: '/static/sounds/delivery-payment.mp3',
        default: '/static/sounds/delivery-notification.mp3'
    }
};

// Audio context for playing sounds
let audioContext;
let notificationsMuted = false;

// Initialize Web Audio API (needs to be triggered by user interaction)
function initAudioContext() {
    if (!audioContext) {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Check if user has muted notifications in localStorage
            notificationsMuted = localStorage.getItem('notificationsMuted') === 'true';
            
            // Update mute button state
            const muteBtn = document.getElementById('notificationsMuteBtn');
            if (muteBtn) {
                updateMuteButtonState(muteBtn);
            }
        } catch (e) {
            console.error('Web Audio API is not supported in this browser', e);
        }
    }
}

// Play notification sound
async function playNotificationSound(role, type) {
    // Don't play if muted
    if (notificationsMuted) return;
    
    // Initialize audio context if not already done
    if (!audioContext) {
        initAudioContext();
    }
    
    // If still no audio context, use synthetic sound directly
    if (!audioContext) {
        // Try basic fallback without audio context
        try {
            const soundMap = NotificationSounds[role] || NotificationSounds.USER;
            const soundUrl = soundMap[type] || soundMap.default;
            const audio = new Audio(soundUrl);
            audio.play().catch(() => {
                // If that fails too, we can't play any sound
                console.log('Unable to play notification sounds - audio context and HTML5 audio both failed');
            });
        } catch (e) {
            console.log('Unable to play notification sounds:', e);
        }
        return;
    }
    
    try {
        // Determine which sound to play
        const soundMap = NotificationSounds[role] || NotificationSounds.USER;
        const soundUrl = soundMap[type] || soundMap.default;
        
        // Try to fetch the audio file
        const response = await fetch(soundUrl);
        
        // If file doesn't exist (404), use synthetic sound
        if (!response.ok) {
            createSyntheticNotificationSound(role, type);
            return;
        }
        
        const arrayBuffer = await response.arrayBuffer();
        
        // Decode the audio data
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Create and play the sound
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(0);
    } catch (error) {
        console.log('Audio file not available, using synthetic sound:', error);
        // Fall back to synthetic sound
        createSyntheticNotificationSound(role, type);
    }
}

// Fallback audio method using HTML5 Audio and synthetic sounds
function playFallbackSound(role, type) {
    if (notificationsMuted) return;
    
    try {
        const soundMap = NotificationSounds[role] || NotificationSounds.USER;
        const soundUrl = soundMap[type] || soundMap.default;
        
        // Try to load the audio file first
        const audio = new Audio(soundUrl);
        audio.play().catch(e => {
            console.log('Audio file not found, using synthetic sound:', e);
            // Use Web Audio API to create a synthetic notification sound
            createSyntheticNotificationSound(role, type);
        });
    } catch (error) {
        console.error('Fallback audio playback failed:', error);
        // Use Web Audio API to create a synthetic notification sound
        createSyntheticNotificationSound(role, type);
    }
}

// Create synthetic notification sounds using Web Audio API
function createSyntheticNotificationSound(role, type) {
    if (notificationsMuted || !audioContext) return;
    
    try {
        // Create different sound patterns based on role and type
        let frequencies = [800, 1000]; // Default frequencies
        let duration = 0.2;
        
        // Customize sounds based on role
        switch(role) {
            case 'ADMIN':
                frequencies = [600, 800, 1000]; // Admin gets three-tone alert
                duration = 0.15;
                break;
            case 'DELIVERY':
                frequencies = [1000, 1200]; // Delivery gets higher pitch
                duration = 0.25;
                break;
            case 'USER':
            default:
                frequencies = [800, 1000]; // Users get standard two-tone
                duration = 0.2;
                break;
        }
        
        // Customize based on notification type
        switch(type) {
            case 'newOrder':
            case 'orderUpdate':
                frequencies = frequencies.map(f => f * 1.1); // Slightly higher for orders
                break;
            case 'newReview':
            case 'reviewReply':
                frequencies = frequencies.map(f => f * 0.9); // Slightly lower for reviews
                break;
            case 'userMessage':
            case 'adminMessage':
                frequencies = frequencies.map(f => f * 1.05); // Slightly higher for messages
                break;
        }
        
        // Play each frequency in sequence
        frequencies.forEach((frequency, index) => {
            setTimeout(() => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
                oscillator.type = 'sine';
                
                // Create envelope (fade in/out)
                gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration - 0.01);
                gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + duration);
            }, index * duration * 1000 * 0.3); // Stagger the tones
        });
    } catch (error) {
        console.error('Failed to create synthetic notification sound:', error);
    }
}

// Toggle notification mute state
function toggleNotificationMute() {
    notificationsMuted = !notificationsMuted;
    localStorage.setItem('notificationsMuted', notificationsMuted);
    
    // Update UI if mute button exists
    const muteBtn = document.getElementById('notificationSoundToggle');
    if (muteBtn) {
        updateMuteButtonState(muteBtn);
    }
    
    // Play test sound if unmuting
    if (!notificationsMuted) {
        // Use timeout to allow audio context to initialize first
        setTimeout(() => {
            // Get user role
            const isAdmin = document.body.classList.contains('admin-role');
            const isDelivery = document.body.classList.contains('delivery-role');
            
            let role = 'USER';
            if (isAdmin) role = 'ADMIN';
            if (isDelivery) role = 'DELIVERY';
            
            playNotificationSound(role, 'default');
        }, 100);
    }
}

// Update mute button state (with visible icons)
function updateMuteButtonState(button) {
    const icon = document.getElementById('soundIcon');
    if (notificationsMuted) {
        if (icon) icon.className = 'fas fa-volume-mute';
        button.className = 'btn btn-sm btn-outline-warning';
        button.setAttribute('title', 'Unmute Notifications');
    } else {
        if (icon) icon.className = 'fas fa-volume-up';
        button.className = 'btn btn-sm btn-outline-secondary';
        button.setAttribute('title', 'Mute Notifications');
    }
}

// Add event listener to initialize audio on first user interaction
document.addEventListener('DOMContentLoaded', function() {
    // Use existing sound toggle button in notification dropdown instead of creating new one
    const existingButton = document.getElementById('notificationSoundToggle');
    if (existingButton) {
        // Set initial state
        notificationsMuted = localStorage.getItem('notificationsMuted') === 'true';
        updateMuteButtonState(existingButton);
        
        // Add click handler
        existingButton.addEventListener('click', toggleNotificationMute);
    }
    
    // Initialize audio context on first user interaction
    const initOnUserAction = function() {
        initAudioContext();
        document.removeEventListener('click', initOnUserAction);
        document.removeEventListener('touchstart', initOnUserAction);
    };
    document.addEventListener('click', initOnUserAction);
    document.addEventListener('touchstart', initOnUserAction);
});

// Export functions for use by other scripts
window.BhojanNotifications = {
    play: playNotificationSound,
    toggle: toggleNotificationMute,
    isMuted: () => notificationsMuted
};