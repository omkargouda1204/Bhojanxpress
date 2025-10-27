/**
 * Advanced Mouse-Tracking Spotlight Background System
 * Creates interactive spotlight effect that follows cursor movement
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAdvancedBackground();
});

function initializeAdvancedBackground() {
    // Create the animated background element
    createBackgroundElement();

    // Create custom cursor spotlight
    createCursorSpotlight();

    // Initialize advanced mouse tracking
    initializeMouseTracking();

    // Add interactive elements enhancement
    enhanceInteractiveElements();

    // Initialize page-specific effects
    addPageSpecificEffects();
}

function createBackgroundElement() {
    // Check if background element already exists
    if (document.querySelector('.animated-background')) {
        return;
    }

    const backgroundElement = document.createElement('div');
    backgroundElement.className = 'animated-background';
    document.body.insertBefore(backgroundElement, document.body.firstChild);
}

function createCursorSpotlight() {
    // Create custom cursor spotlight element
    const spotlight = document.createElement('div');
    spotlight.className = 'cursor-spotlight';
    document.body.appendChild(spotlight);

    return spotlight;
}

function initializeMouseTracking() {
    let mouseX = 50;
    let mouseY = 50;
    let targetX = 50;
    let targetY = 50;

    const spotlight = document.querySelector('.cursor-spotlight');

    // Smooth mouse tracking with easing
    function updateMousePosition() {
        mouseX += (targetX - mouseX) * 0.1;
        mouseY += (targetY - mouseY) * 0.1;

        // Update CSS custom properties for spotlight effect
        document.documentElement.style.setProperty('--mouse-x', mouseX + '%');
        document.documentElement.style.setProperty('--mouse-y', mouseY + '%');

        // Update custom cursor position
        if (spotlight) {
            spotlight.style.left = (targetX * window.innerWidth / 100) + 'px';
            spotlight.style.top = (targetY * window.innerHeight / 100) + 'px';
        }

        requestAnimationFrame(updateMousePosition);
    }

    // Start the animation loop
    updateMousePosition();

    // Track mouse movement
    document.addEventListener('mousemove', function(e) {
        targetX = (e.clientX / window.innerWidth) * 100;
        targetY = (e.clientY / window.innerHeight) * 100;
    });

    // Handle mouse enter/leave for spotlight intensity
    document.addEventListener('mouseenter', function() {
        if (spotlight) {
            spotlight.style.opacity = '1';
            spotlight.style.transform = 'translate(-50%, -50%) scale(1)';
        }
    });

    document.addEventListener('mouseleave', function() {
        if (spotlight) {
            spotlight.style.opacity = '0.5';
            spotlight.style.transform = 'translate(-50%, -50%) scale(0.5)';
        }
    });
    
    // Add touch support for mobile devices
    document.addEventListener('touchmove', function(e) {
        if (e.touches.length > 0) {
            const touch = e.touches[0];
            targetX = (touch.clientX / window.innerWidth) * 100;
            targetY = (touch.clientY / window.innerHeight) * 100;
        }
    });

    // Handle click effects
    document.addEventListener('click', function(e) {
        if (spotlight) {
            // Create ripple effect on click
            spotlight.style.transform = 'translate(-50%, -50%) scale(1.5)';
            spotlight.style.boxShadow = `
                0 0 40px rgba(255, 255, 255, 0.8),
                0 0 80px rgba(255, 255, 255, 0.5),
                0 0 120px rgba(255, 255, 255, 0.3)
            `;

            setTimeout(() => {
                spotlight.style.transform = 'translate(-50%, -50%) scale(1)';
                spotlight.style.boxShadow = `
                    0 0 20px rgba(255, 255, 255, 0.5),
                    0 0 40px rgba(255, 255, 255, 0.3),
                    0 0 60px rgba(255, 255, 255, 0.1)
                `;
            }, 200);
        }
    });
}

function enhanceInteractiveElements() {
    // Enhance cards with spotlight interaction
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.transform = 'translateY(-15px) scale(1.03)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Enhance buttons with glow effect
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.filter = 'brightness(1.2) saturate(1.3)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.filter = 'brightness(1) saturate(1)';
        });
    });

    // Enhance form controls
    const formControls = document.querySelectorAll('.form-control');
    formControls.forEach(control => {
        control.addEventListener('focus', function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.boxShadow = '0 0 30px rgba(255, 255, 255, 0.3)';
        });

        control.addEventListener('blur', function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.boxShadow = 'none';
        });
    });
}

function addPageSpecificEffects() {
    const body = document.body;
    const path = window.location.pathname;

    // Add page-specific effects
    if (path === '/' || path === '/home') {
        body.classList.add('page-home');
        addParticleEffects();
    } else if (path.includes('/admin')) {
        body.classList.add('page-admin');
        addAdminEffects();
    } else if (path.includes('/login') || path.includes('/register')) {
        body.classList.add('page-auth');
        addAuthPageEffects();
    }
}

function addParticleEffects() {
    // Create floating particles for home page
    const particleContainer = document.createElement('div');
    particleContainer.className = 'floating-particles';
    particleContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    `;

    document.body.appendChild(particleContainer);

    // Create particles
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: ${2 + Math.random() * 4}px;
            height: ${2 + Math.random() * 4}px;
            background: rgba(255, 255, 255, ${0.3 + Math.random() * 0.7});
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${6 + Math.random() * 4}s ease-in-out infinite;
            animation-delay: ${Math.random() * 2}s;
        `;

        particleContainer.appendChild(particle);
    }

    // Add particle animation CSS if not exists
    if (!document.querySelector('#particle-animation-styles')) {
        const style = document.createElement('style');
        style.id = 'particle-animation-styles';
        style.textContent = `
            @keyframes float {
                0%, 100% {
                    transform: translateY(0px) translateX(0px) rotate(0deg);
                    opacity: 0.7;
                }
                33% {
                    transform: translateY(-30px) translateX(15px) rotate(120deg);
                    opacity: 1;
                }
                66% {
                    transform: translateY(15px) translateX(-15px) rotate(240deg);
                    opacity: 0.8;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function addAdminEffects() {
    // Add special effects for admin dashboard
    const adminCards = document.querySelectorAll('.admin-card, .card');
    adminCards.forEach(card => {
        card.style.background = 'rgba(255, 255, 255, 0.08)';
        card.style.border = '1px solid rgba(255, 255, 255, 0.15)';
    });

    // Enhanced table styling
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        table.style.background = 'rgba(255, 255, 255, 0.03)';
    });
}

function addAuthPageEffects() {
    // Special effects for login/signup pages
    const authForms = document.querySelectorAll('.login-form, .register-form, form');
    authForms.forEach(form => {
        form.style.background = 'rgba(255, 255, 255, 0.15)';
        form.style.backdropFilter = 'blur(25px)';
        form.style.border = '1px solid rgba(255, 255, 255, 0.3)';
        form.style.borderRadius = '25px';
        form.style.padding = '3rem';
        form.style.boxShadow = `
            0 20px 60px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3)
        `;
    });
}

// Handle window resize
window.addEventListener('resize', function() {
    // Recreate particles on resize
    const particles = document.querySelector('.floating-particles');
    if (particles) {
        particles.remove();
        setTimeout(addParticleEffects, 100);
    }
});

// Performance optimization
let ticking = false;
function optimizedMouseMove(e) {
    if (!ticking) {
        requestAnimationFrame(function() {
            // Mouse move handling here
            ticking = false;
        });
        ticking = true;
    }
}

// Initialize special features on specific pages
document.addEventListener('DOMContentLoaded', function() {
    // Add food glow effects to featured items
    const featuredItems = document.querySelectorAll('.featured-item, .food-card, .menu-item');
    featuredItems.forEach(item => {
        item.classList.add('food-glow');

        item.addEventListener('mouseenter', function() {
            this.style.boxShadow = `
                0 0 40px rgba(255, 255, 255, 0.4),
                0 20px 60px rgba(0, 0, 0, 0.3)
            `;
        });

        item.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 0 25px rgba(230, 74, 25, 0.4)';
        });
    });
});
