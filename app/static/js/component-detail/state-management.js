/**
 * Component Detail State Management Module
 * Handles reactive state, data persistence, and state synchronization
 * Built from scratch following TDD methodology
 */

/**
 * State Management Utilities
 */
window.ComponentDetailState = {
    
    /**
     * Initialize state management system
     */
    init() {
        console.log('🏪 ComponentDetailState: Initializing state management');
        
        // Set up state persistence
        this.setupStatePersistence();
        
        // Set up cross-tab communication
        this.setupCrossTabSync();
        
        console.log('✅ ComponentDetailState: State management initialized');
    },
    
    /**
     * Set up state persistence to localStorage
     */
    setupStatePersistence() {
        console.log('💾 ComponentDetailState: Setting up state persistence');
        
        // Save state on page unload
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
        
        // Restore state on page load
        this.restoreState();
    },
    
    /**
     * Set up cross-tab communication
     */
    setupCrossTabSync() {
        console.log('🔄 ComponentDetailState: Setting up cross-tab synchronization');
        
        // Listen for storage changes from other tabs
        window.addEventListener('storage', (event) => {
            if (event.key === 'componentDetailState') {
                console.log('🔄 ComponentDetailState: State updated from another tab');
                this.handleExternalStateChange(event.newValue);
            }
        });
    },
    
    /**
     * Save current state to localStorage
     */
    saveState() {
        try {
            const component = this.getAlpineComponent();
            if (!component) return;
            
            const state = {
                activeTab: component.activeTab,
                selectedVariant: component.selectedVariant,
                timestamp: Date.now(),
                componentId: component.componentData?.id
            };
            
            localStorage.setItem('componentDetailState', JSON.stringify(state));
            console.log('💾 ComponentDetailState: State saved to localStorage');
        } catch (error) {
            console.error('❌ ComponentDetailState: Error saving state:', error);
        }
    },
    
    /**
     * Restore state from localStorage
     */
    restoreState() {
        try {
            const savedState = localStorage.getItem('componentDetailState');
            if (!savedState) return;
            
            const state = JSON.parse(savedState);
            const component = this.getAlpineComponent();
            
            if (!component || !state) return;
            
            // Only restore if it's for the same component and recent (< 1 hour)
            const isRecent = Date.now() - state.timestamp < 3600000; // 1 hour
            const isSameComponent = state.componentId === component.componentData?.id;
            
            if (isRecent && isSameComponent) {
                console.log('🔄 ComponentDetailState: Restoring state from localStorage');
                
                if (state.activeTab) {
                    component.activeTab = state.activeTab;
                }
                
                if (state.selectedVariant !== undefined) {
                    component.selectedVariant = state.selectedVariant;
                }
            } else {
                // Clear old state
                localStorage.removeItem('componentDetailState');
            }
        } catch (error) {
            console.error('❌ ComponentDetailState: Error restoring state:', error);
            localStorage.removeItem('componentDetailState');
        }
    },
    
    /**
     * Handle state changes from other tabs
     */
    handleExternalStateChange(newStateJson) {
        try {
            const newState = JSON.parse(newStateJson);
            const component = this.getAlpineComponent();
            
            if (!component || !newState) return;
            
            // Only sync if it's for the same component
            if (newState.componentId === component.componentData?.id) {
                console.log('🔄 ComponentDetailState: Syncing state from another tab');
                
                if (newState.activeTab && newState.activeTab !== component.activeTab) {
                    component.activeTab = newState.activeTab;
                }
                
                if (newState.selectedVariant !== component.selectedVariant) {
                    component.selectedVariant = newState.selectedVariant;
                }
            }
        } catch (error) {
            console.error('❌ ComponentDetailState: Error handling external state change:', error);
        }
    },
    
    /**
     * Get the Alpine.js component instance
     */
    getAlpineComponent() {
        const element = document.querySelector('[x-data*="componentDetailApp"]');
        return element?._x_dataStack?.[0] || element?.__x?.$data;
    },
    
    /**
     * Create state snapshot for debugging
     */
    createSnapshot() {
        const component = this.getAlpineComponent();
        if (!component) return null;
        
        return {
            timestamp: Date.now(),
            url: window.location.href,
            state: {
                isLoading: component.isLoading,
                imagesLoading: component.imagesLoading,
                activeTab: component.activeTab,
                selectedVariant: component.selectedVariant,
                lightboxOpen: component.lightboxOpen,
                hasImages: component.hasImages,
                totalImages: component.totalImages
            },
            data: {
                componentImagesCount: component.componentImages.length,
                variantsCount: component.variants.length
            }
        };
    },
    
    /**
     * Log current state for debugging
     */
    logCurrentState() {
        const snapshot = this.createSnapshot();
        if (snapshot) {
            console.log('📊 ComponentDetailState: Current state snapshot:', snapshot);
        }
    }
};

/**
 * State Validation Utilities
 */
window.ComponentDetailStateValidator = {
    
    /**
     * Validate component state integrity
     */
    validateState(component) {
        const issues = [];
        
        // Check required properties
        if (component.componentData === null || component.componentData === undefined) {
            issues.push('componentData is null or undefined');
        }
        
        if (!Array.isArray(component.componentImages)) {
            issues.push('componentImages is not an array');
        }
        
        if (!Array.isArray(component.variants)) {
            issues.push('variants is not an array');
        }
        
        // Check selected variant validity
        if (component.selectedVariant !== null) {
            const variant = component.variants.find(v => v.id === component.selectedVariant);
            if (!variant) {
                issues.push(`selectedVariant ${component.selectedVariant} not found in variants`);
            }
        }
        
        // Check lightbox index bounds
        if (component.lightboxOpen && component.currentImages.length > 0) {
            if (component.lightboxIndex < 0 || component.lightboxIndex >= component.currentImages.length) {
                issues.push(`lightboxIndex ${component.lightboxIndex} out of bounds`);
            }
        }
        
        if (issues.length > 0) {
            console.warn('⚠️ ComponentDetailStateValidator: State validation issues found:', issues);
            return false;
        }
        
        return true;
    },
    
    /**
     * Auto-fix common state issues
     */
    autoFixState(component) {
        let fixed = false;
        
        // Fix out-of-bounds lightbox index
        if (component.lightboxOpen && component.currentImages.length > 0) {
            if (component.lightboxIndex < 0) {
                component.lightboxIndex = 0;
                fixed = true;
            } else if (component.lightboxIndex >= component.currentImages.length) {
                component.lightboxIndex = component.currentImages.length - 1;
                fixed = true;
            }
        }
        
        // Fix invalid selected variant
        if (component.selectedVariant !== null) {
            const variant = component.variants.find(v => v.id === component.selectedVariant);
            if (!variant) {
                component.selectedVariant = null;
                fixed = true;
            }
        }
        
        // Initialize missing arrays
        if (!Array.isArray(component.componentImages)) {
            component.componentImages = [];
            fixed = true;
        }
        
        if (!Array.isArray(component.variants)) {
            component.variants = [];
            fixed = true;
        }
        
        if (fixed) {
            console.log('🔧 ComponentDetailStateValidator: Auto-fixed state issues');
        }
        
        return fixed;
    }
};

/**
 * Performance monitoring for state changes
 */
window.ComponentDetailPerformance = {
    
    startTime: null,
    metrics: {},
    
    /**
     * Start performance tracking
     */
    start(operation) {
        this.startTime = performance.now();
        this.metrics[operation] = { start: this.startTime };
        console.log(`⏱️ ComponentDetailPerformance: Started tracking ${operation}`);
    },
    
    /**
     * End performance tracking
     */
    end(operation) {
        if (!this.metrics[operation]) return;
        
        const endTime = performance.now();
        const duration = endTime - this.metrics[operation].start;
        this.metrics[operation].duration = duration;
        
        console.log(`⏱️ ComponentDetailPerformance: ${operation} took ${duration.toFixed(2)}ms`);
        
        // Warn about slow operations
        if (duration > 100) {
            console.warn(`🐌 ComponentDetailPerformance: Slow operation detected: ${operation} (${duration.toFixed(2)}ms)`);
        }
        
        return duration;
    },
    
    /**
     * Get performance report
     */
    getReport() {
        return {
            metrics: this.metrics,
            totalOperations: Object.keys(this.metrics).length,
            averageDuration: Object.values(this.metrics)
                .filter(m => m.duration)
                .reduce((sum, m, _, arr) => sum + m.duration / arr.length, 0)
        };
    }
};

// Initialize state management when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏪 ComponentDetailState: DOM ready, initializing state management');
    
    // Wait for Alpine.js to be ready
    document.addEventListener('alpine:init', function() {
        ComponentDetailState.init();
    });
});

console.log('✅ Component Detail State Management: Module loaded successfully');