/**
 * Advanced UI Animations and Micro-interactions
 * QVM Panel - Enhanced User Experience
 */

class AnimationController {
    constructor() {
        this.init();
        this.setupIntersectionObserver();
        this.setupRippleEffects();
        this.setupLoadingAnimations();
        this.setupMicroInteractions();
    }

    init() {
        // Add loading animation to body
        document.body.classList.add('animations-ready');
        
        // Animate elements on page load
        this.animateOnLoad();
        
        // Setup smooth scroll behavior
        this.setupSmoothScroll();
    }

    animateOnLoad() {
        // Animate sidebar
        const sidebar = document.querySelector('.sidebar, .admin-sidebar');
        if (sidebar) {
            sidebar.style.animation = 'slideInLeft 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }

        // Animate header
        const header = document.querySelector('.header, .admin-header');
        if (header) {
            header.style.animation = 'slideInRight 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }

        // Animate cards with stagger
        const cards = document.querySelectorAll('.card, .stat-card');
        cards.forEach((card, index) => {
            card.style.animation = `fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.1}s both`;
        });

        // Animate navigation items
        const navItems = document.querySelectorAll('.nav-item, .nav-link');
        navItems.forEach((item, index) => {
            item.style.animation = `fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) ${0.3 + index * 0.05}s both`;
        });
    }

    setupIntersectionObserver() {
        // Animate elements when they come into view
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe all cards and stat cards
        document.querySelectorAll('.card, .stat-card').forEach(el => {
            observer.observe(el);
        });
    }

    setupRippleEffects() {
        // Add ripple effect to buttons
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.btn');
            if (button && !button.classList.contains('no-ripple')) {
                this.createRipple(e, button);
            }
        });
    }

    createRipple(event, button) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.animation = 'ripple 0.6s ease-out';
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    setupLoadingAnimations() {
        // Add loading states to forms and buttons
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) {
                    this.setButtonLoading(submitBtn, true);
                }
            });
        });

        // Enhanced loading states for async operations
        this.setupAsyncLoading();
    }

    setupAsyncLoading() {
        // Skip async loading setup to avoid interfering with normal page functionality
        // The global loading interceptor was causing the stuck "Processing..." screen
        return;
        
        // Original code (disabled):
        // const originalFetch = window.fetch;
        // window.fetch = async (...args) => {
        //     this.showGlobalLoading();
        //     try {
        //         const response = await originalFetch(...args);
        //         return response;
        //     } finally {
        //         setTimeout(() => this.hideGlobalLoading(), 300);
        //     }
        // };
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            const originalText = button.innerHTML;
            button.dataset.originalText = originalText;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    }

    showGlobalLoading() {
        const loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.innerHTML = `
            <div class="loader-backdrop">
                <div class="loader-content">
                    <div class="loader-spinner"></div>
                    <div class="loader-text">Processing...</div>
                </div>
            </div>
        `;
        document.body.appendChild(loader);
    }

    hideGlobalLoading() {
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 300);
        }
    }

    setupMicroInteractions() {
        // Enhanced hover effects for interactive elements
        this.setupEnhancedHovers();
        this.setupFocusAnimations();
        this.setupTransitionEffects();
    }

    setupEnhancedHovers() {
        // Add subtle hover animations to interactive elements
        const hoverElements = document.querySelectorAll('.btn, .card, .stat-card, .nav-item, .nav-link');
        
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            });
        });
    }

    setupFocusAnimations() {
        // Enhanced focus animations for form elements
        const formElements = document.querySelectorAll('input, textarea, select');
        
        formElements.forEach(element => {
            element.addEventListener('focus', () => {
                element.parentElement.classList.add('focused');
            });
            
            element.addEventListener('blur', () => {
                element.parentElement.classList.remove('focused');
            });
        });
    }

    setupTransitionEffects() {
        // Smooth page transitions
        this.setupPageTransitions();
        this.setupModalAnimations();
    }

    setupPageTransitions() {
        // Add fade transition to internal links
        const internalLinks = document.querySelectorAll('a[href^="/"], a[href^="./"]');
        
        internalLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if (!e.ctrlKey && !e.metaKey && !link.target) {
                    e.preventDefault();
                    this.fadeOutPage(() => {
                        window.location.href = link.href;
                    });
                }
            });
        });
    }

    fadeOutPage(callback) {
        document.body.style.transition = 'opacity 0.3s ease-out';
        document.body.style.opacity = '0';
        setTimeout(callback, 300);
    }

    setupModalAnimations() {
        // Enhanced modal animations
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            modal.addEventListener('show', () => {
                modal.style.display = 'block';
                setTimeout(() => {
                    modal.classList.add('show');
                }, 10);
            });
            
            modal.addEventListener('hide', () => {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 300);
            });
        });
    }

    setupSmoothScroll() {
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Utility methods for custom animations
    animateElement(element, animation, duration = 600, delay = 0) {
        element.style.animation = `${animation} ${duration}ms cubic-bezier(0.4, 0, 0.2, 1) ${delay}ms both`;
    }

    addParticleEffect(container, count = 20) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 4 + 1}px;
                height: ${Math.random() * 4 + 1}px;
                background: rgba(79, 154, 245, ${Math.random() * 0.5 + 0.3});
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: particleFloat ${Math.random() * 10 + 15}s linear infinite;
                animation-delay: ${Math.random() * 5}s;
            `;
            container.appendChild(particle);
        }
    }

    // Performance optimization
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Additional CSS for animations
const animationStyles = `
<style>
/* Ripple Effect */
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple 0.6s ease-out;
    pointer-events: none;
}

@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

/* Loading States */
.loading {
    position: relative;
    pointer-events: none;
}

#global-loader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 9999;
    transition: opacity 0.3s ease;
}

.loader-backdrop {
    position: absolute;
    inset: 0;
    background: rgba(10, 12, 16, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
}

.loader-content {
    text-align: center;
    color: #e1e9f0;
}

.loader-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(79, 154, 245, 0.2);
    border-top: 3px solid #4f9af5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Focus States */
.focused {
    transform: translateY(-2px);
}

/* Animate In Class */
.animate-in {
    animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
}

/* Enhanced Hover Effects */
.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

/* Page Transitions */
body {
    transition: opacity 0.3s ease;
}

/* Modal Animations */
.modal {
    opacity: 0;
    transform: scale(0.9);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal.show {
    opacity: 1;
    transform: scale(1);
}
</style>
`;

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Inject animation styles
    document.head.insertAdjacentHTML('beforeend', animationStyles);
    
    // Initialize animation controller
    window.animationController = new AnimationController();
    
    // Add animations-ready class to body
    document.body.classList.add('animations-ready');
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationController;
}
