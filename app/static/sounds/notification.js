// Notification Sound Generator
// This creates a simple notification beep sound using Web Audio API as fallback

class NotificationSound {
    constructor() {
        this.audioContext = null;
        this.initAudio();
    }

    initAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Web Audio API not supported');
        }
    }

    playBeep(frequency = 800, duration = 200, type = 'sine') {
        if (!this.audioContext) return;

        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.frequency.value = frequency;
        oscillator.type = type;

        gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);

        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration / 1000);
    }

    playNotificationSound() {
        // Play a pleasant notification sound sequence
        this.playBeep(659.25, 100); // E note
        setTimeout(() => this.playBeep(783.99, 100), 100); // G note
        setTimeout(() => this.playBeep(880.00, 150), 200); // A note
    }

    playSuccessSound() {
        this.playBeep(523.25, 100); // C note
        setTimeout(() => this.playBeep(659.25, 100), 100); // E note
        setTimeout(() => this.playBeep(783.99, 200), 200); // G note
    }

    playErrorSound() {
        this.playBeep(200, 300, 'sawtooth');
    }
}

// Export for use in other scripts
window.NotificationSound = NotificationSound;
