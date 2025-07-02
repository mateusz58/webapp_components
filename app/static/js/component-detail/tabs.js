/**
 * Component Detail Tabs Module
 * Enhanced tab functionality with animations and user interactions
 * Built from scratch following TDD methodology
 */

/**
 * Tabs Management System
 */
window.ComponentDetailTabs = {
    
    alpineComponent: null,
    
    /**
     * Initialize tabs system
     */
    init(alpineComponent) {
        console.log('📑 ComponentDetailTabs: Initializing tabs system');
        
        this.alpineComponent = alpineComponent;
        
        // Set up keyboard navigation
        this.setupKeyboardNavigation();
        
        // Set up URL hash handling
        this.setupUrlHashHandling();
        
        // Set up smooth scrolling
        this.setupSmoothScrolling();
        
        // Set up analytics tracking
        this.setupAnalyticsTracking();
        
        console.log('✅ ComponentDetailTabs: Tabs system initialized');
    },
    
    /**
     * Set up keyboard navigation for tabs
     */
    setupKeyboardNavigation() {
        console.log('⌨️ ComponentDetailTabs: Setting up keyboard navigation');
        
        document.addEventListener('keydown', (e) => {
            // Only handle keyboard navigation when a tab is focused
            if (!e.target.classList.contains('nav-link')) return;
            
            const tabs = document.querySelectorAll('.nav-tabs-modern .nav-link');
            const currentIndex = Array.from(tabs).indexOf(e.target);
            
            let newIndex = currentIndex;
            
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                    break;
                case 'Home':
                    e.preventDefault();
                    newIndex = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    newIndex = tabs.length - 1;
                    break;
                default:
                    return;
            }
            
            // Focus and activate the new tab
            tabs[newIndex].focus();
            tabs[newIndex].click();
        });
    },
    
    /**
     * Set up URL hash handling for direct tab linking
     */
    setupUrlHashHandling() {
        console.log('🔗 ComponentDetailTabs: Setting up URL hash handling');
        
        // Handle initial hash on page load
        window.addEventListener('load', () => {
            this.handleHashChange();
        });
        
        // Handle hash changes
        window.addEventListener('hashchange', () => {
            this.handleHashChange();
        });
        
        // Update hash when tab changes
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                const tabName = this.getTabNameFromButton(e.target);
                if (tabName) {
                    history.replaceState(null, null, `#${tabName}`);
                }
            }
        });
    },
    
    /**
     * Handle hash change events
     */
    handleHashChange() {
        const hash = window.location.hash.substring(1);
        const validTabs = ['basic-info', 'properties', 'keywords', 'variants'];
        
        if (hash && validTabs.includes(hash)) {
            if (this.alpineComponent) {
                this.alpineComponent.selectTab(hash);
                console.log(`📑 ComponentDetailTabs: Switched to tab: ${hash}`);
            }
        }
    },
    
    /**
     * Get tab name from button element
     */
    getTabNameFromButton(button) {
        const clickHandler = button.getAttribute('@click');
        const match = clickHandler && clickHandler.match(/selectTab\('([^']+)'\)/);
        return match ? match[1] : null;
    },
    
    /**
     * Set up smooth scrolling to tabs section
     */
    setupSmoothScrolling() {
        console.log('🔄 ComponentDetailTabs: Setting up smooth scrolling');
        
        // Scroll to tabs when switching from external links
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                const tabsSection = document.querySelector('.info-tabs');
                if (tabsSection) {
                    // Small delay to allow tab switch animation
                    setTimeout(() => {
                        const offsetTop = tabsSection.offsetTop - 20;
                        window.scrollTo({
                            top: offsetTop,
                            behavior: 'smooth'
                        });
                    }, 100);
                }
            }
        });
    },
    
    /**
     * Set up analytics tracking for tab usage
     */
    setupAnalyticsTracking() {
        console.log('📊 ComponentDetailTabs: Setting up analytics tracking');
        
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                const tabName = this.getTabNameFromButton(e.target);
                if (tabName) {
                    this.trackTabEvent('tab_switch', { tabName });
                }
            }
        });
    },
    
    /**
     * Switch to a specific tab programmatically
     */
    switchToTab(tabName) {
        console.log(`📑 ComponentDetailTabs: Switching to tab: ${tabName}`);
        
        if (this.alpineComponent) {
            this.alpineComponent.selectTab(tabName);
            
            // Update URL hash
            history.replaceState(null, null, `#${tabName}`);
            
            // Track the event
            this.trackTabEvent('tab_switch_programmatic', { tabName });
        }
    },
    
    /**
     * Get currently active tab
     */
    getActiveTab() {
        return this.alpineComponent ? this.alpineComponent.activeTab : null;
    },
    
    /**
     * Get tab content statistics
     */
    getTabStats() {
        if (!this.alpineComponent) return null;
        
        // Count items in each tab
        const variants = document.querySelectorAll('#variants .variant-card').length;
        const keywords = document.querySelectorAll('#keywords .keyword-tag').length;
        const properties = document.querySelectorAll('#properties .property-card').length;
        
        return {
            activeTab: this.getActiveTab(),
            variants,
            keywords,
            properties,
            hasBasicInfo: true
        };
    },
    
    /**
     * Highlight tab with specific content
     */
    highlightTab(tabName, duration = 2000) {
        const tabButton = document.querySelector(`[\\@click*="selectTab('${tabName}')"]`);
        if (tabButton) {
            tabButton.classList.add('tab-highlight');
            setTimeout(() => {
                tabButton.classList.remove('tab-highlight');
            }, duration);
        }
    },
    
    /**
     * Add notification badge to tab
     */
    addTabNotification(tabName, count = null) {
        const tabButton = document.querySelector(`[\\@click*="selectTab('${tabName}')"]`);
        if (tabButton) {
            // Remove existing notification
            const existingBadge = tabButton.querySelector('.tab-notification');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            // Add new notification
            const badge = document.createElement('span');
            badge.className = 'tab-notification';
            badge.textContent = count || '!';
            tabButton.appendChild(badge);
            
            console.log(`📑 ComponentDetailTabs: Added notification to ${tabName} tab`);
        }
    },
    
    /**
     * Remove notification badge from tab
     */
    removeTabNotification(tabName) {
        const tabButton = document.querySelector(`[\\@click*="selectTab('${tabName}')"]`);
        if (tabButton) {
            const badge = tabButton.querySelector('.tab-notification');
            if (badge) {
                badge.remove();
                console.log(`📑 ComponentDetailTabs: Removed notification from ${tabName} tab`);
            }
        }
    },
    
    /**
     * Animate tab content on show
     */
    animateTabContent(tabName) {
        const tabPane = document.querySelector(`#${tabName}`);
        if (tabPane) {
            // Add animation class
            tabPane.classList.add('tab-animate-in');
            
            // Remove after animation
            setTimeout(() => {
                tabPane.classList.remove('tab-animate-in');
            }, 300);
        }
    },
    
    /**
     * Update tab counts dynamically
     */
    updateTabCounts() {
        console.log('🔢 ComponentDetailTabs: Updating tab counts');
        
        // Update variants count
        const variantsTab = document.querySelector(`[\\@click*="selectTab('variants')"]`);
        const variantsCount = document.querySelectorAll('#variants .variant-card').length;
        if (variantsTab) {
            const countMatch = variantsTab.textContent.match(/\((\d+)\)/);
            if (countMatch) {
                variantsTab.innerHTML = variantsTab.innerHTML.replace(/\(\d+\)/, `(${variantsCount})`);
            }
        }
        
        // Update keywords count if needed
        const keywordsCount = document.querySelectorAll('#keywords .keyword-tag').length;
        console.log(`📊 ComponentDetailTabs: Variants: ${variantsCount}, Keywords: ${keywordsCount}`);
    },
    
    /**
     * Track tab events for analytics
     */
    trackTabEvent(eventName, data = {}) {
        // Send analytics data if analytics system is available
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track(`Tabs ${eventName}`, {
                componentId: this.alpineComponent?.componentData?.id,
                currentTab: this.getActiveTab(),
                ...data
            });
        }
        
        console.log('📊 ComponentDetailTabs: Event tracked:', eventName, data);
    },
    
    /**
     * Add custom CSS animations
     */
    addCustomAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            .tab-highlight {
                animation: tabHighlight 2s ease-in-out;
            }
            
            @keyframes tabHighlight {
                0%, 100% { background: transparent; }
                50% { background: rgba(59, 130, 246, 0.1); }
            }
            
            .tab-notification {
                position: absolute;
                top: -8px;
                right: -8px;
                background: #ef4444;
                color: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                font-size: 11px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
            }
            
            .tab-animate-in {
                animation: tabSlideIn 0.3s ease-out;
            }
            
            @keyframes tabSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
};

// Initialize custom animations when module loads
document.addEventListener('DOMContentLoaded', () => {
    window.ComponentDetailTabs.addCustomAnimations();
});

console.log('✅ Component Detail Tabs: Module loaded successfully');