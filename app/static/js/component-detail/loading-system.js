/**
 * Component Detail Loading System Module
 * Handles loading states, progress tracking, and user feedback
 * Built from scratch following TDD methodology
 */

/**
 * Advanced Loading System
 */
window.ComponentDetailLoadingSystem = {
    
    alpineComponent: null,
    loadingStartTime: null,
    progressInterval: null,
    loadingStages: [
        { name: 'Initializing', duration: 200 },
        { name: 'Loading component data', duration: 300 },
        { name: 'Fetching images', duration: 1000 },
        { name: 'Optimizing display', duration: 500 }
    ],
    currentStage: 0,
    
    /**
     * Initialize loading system
     */
    init(alpineComponent) {
        console.log('🔄 ComponentDetailLoadingSystem: Initializing loading system');
        
        this.alpineComponent = alpineComponent;
        this.loadingStartTime = Date.now();
        
        // Set up immediate loading indicators
        this.activateImmediateLoading();
        
        // Set up progressive loading feedback
        this.setupProgressiveFeedback();
        
        // Set up loading timeout protection
        this.setupTimeoutProtection();
        
        console.log('✅ ComponentDetailLoadingSystem: Loading system initialized');
    },
    
    /**
     * Activate immediate loading indicators
     */
    activateImmediateLoading() {
        console.log('⚡ ComponentDetailLoadingSystem: Activating immediate loading');
        
        // Add loading class to document for immediate CSS effects
        document.documentElement.classList.add('loading-active');
        document.body.setAttribute('data-loading', 'true');
        
        // Set initial loading message
        if (this.alpineComponent) {
            this.alpineComponent.isLoading = true;
            this.alpineComponent.imagesLoading = true;
            this.alpineComponent.loadingMessage = 'Initializing component...';
            this.alpineComponent.loadingProgress = 0;
        }
        
        // Show loading overlay
        this.showLoadingOverlay();
    },
    
    /**
     * Set up progressive loading feedback
     */
    setupProgressiveFeedback() {
        console.log('📊 ComponentDetailLoadingSystem: Setting up progressive feedback');
        
        this.currentStage = 0;
        this.updateLoadingStage();
        
        // Update progress every 100ms
        this.progressInterval = setInterval(() => {
            this.updateLoadingProgress();
        }, 100);
    },
    
    /**
     * Update current loading stage
     */
    updateLoadingStage() {
        if (this.currentStage >= this.loadingStages.length) return;
        
        const stage = this.loadingStages[this.currentStage];
        console.log(`🔄 ComponentDetailLoadingSystem: Stage ${this.currentStage + 1}: ${stage.name}`);
        
        if (this.alpineComponent) {
            this.alpineComponent.loadingMessage = stage.name;
        }
        
        // Auto-advance to next stage after duration
        setTimeout(() => {
            this.currentStage++;
            if (this.currentStage < this.loadingStages.length) {
                this.updateLoadingStage();
            }
        }, stage.duration);
    },
    
    /**
     * Update loading progress
     */
    updateLoadingProgress() {
        if (!this.alpineComponent || !this.alpineComponent.imagesLoading) return;
        
        const elapsed = Date.now() - this.loadingStartTime;
        const totalEstimatedTime = this.loadingStages.reduce((sum, stage) => sum + stage.duration, 0);
        
        let progress = (elapsed / totalEstimatedTime) * 100;
        
        // Cap progress at 90% until actual completion
        progress = Math.min(progress, 90);
        
        this.alpineComponent.loadingProgress = Math.round(progress);
    },
    
    /**
     * Set up timeout protection
     */
    setupTimeoutProtection() {
        console.log('⏰ ComponentDetailLoadingSystem: Setting up timeout protection');
        
        // Force complete loading after 30 seconds
        setTimeout(() => {
            if (this.alpineComponent?.imagesLoading) {
                console.warn('⚠️ ComponentDetailLoadingSystem: Loading timeout reached, forcing completion');
                this.completeLoading('timeout');
            }
        }, 30000);
    },
    
    /**
     * Show loading overlay
     */
    showLoadingOverlay() {
        // Create loading overlay if it doesn't exist
        let overlay = document.querySelector('.loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-overlay__content">
                    <div class="loading-overlay__spinner">
                        <div class="spinner"></div>
                    </div>
                    <div class="loading-overlay__message">Loading component...</div>
                    <div class="loading-overlay__progress">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        
        overlay.classList.add('active');
    },
    
    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            
            // Remove overlay after animation
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    },
    
    /**
     * Complete loading process
     */
    completeLoading(reason = 'success') {
        console.log(`✅ ComponentDetailLoadingSystem: Completing loading (${reason})`);
        
        const loadingDuration = Date.now() - this.loadingStartTime;
        console.log(`⏱️ ComponentDetailLoadingSystem: Total loading time: ${loadingDuration}ms`);
        
        // Clear progress interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // Update Alpine component state
        if (this.alpineComponent) {
            this.alpineComponent.isLoading = false;
            this.alpineComponent.imagesLoading = false;
            this.alpineComponent.loadingMessage = '';
            this.alpineComponent.loadingProgress = 100;
        }
        
        // Remove loading classes and attributes
        document.documentElement.classList.remove('loading-active');
        document.body.removeAttribute('data-loading');
        
        // Hide loading overlay
        this.hideLoadingOverlay();
        
        // Clean up URL parameters
        this.cleanupUrlParameters();
        
        // Track completion analytics
        this.trackLoadingCompletion(loadingDuration, reason);
    },
    
    /**
     * Update loading message
     */
    updateLoadingMessage(message) {
        console.log(`💬 ComponentDetailLoadingSystem: ${message}`);
        
        if (this.alpineComponent) {
            this.alpineComponent.loadingMessage = message;
        }
        
        // Update overlay message
        const overlayMessage = document.querySelector('.loading-overlay__message');
        if (overlayMessage) {
            overlayMessage.textContent = message;
        }
    },
    
    /**
     * Update loading progress
     */
    setLoadingProgress(progress) {
        if (this.alpineComponent) {
            this.alpineComponent.loadingProgress = Math.round(progress);
        }
        
        // Update overlay progress bar
        const progressBar = document.querySelector('.loading-overlay__progress .progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    },
    
    /**
     * Clean up URL parameters
     */
    cleanupUrlParameters() {
        const url = new URL(window.location);
        if (url.searchParams.has('loading')) {
            // Ensure minimum display time for UX
            const minDisplayTime = 2000; // 2 seconds
            const elapsed = Date.now() - this.loadingStartTime;
            
            if (elapsed < minDisplayTime) {
                const remainingTime = minDisplayTime - elapsed;
                console.log(`🕐 ComponentDetailLoadingSystem: Delaying URL cleanup for ${remainingTime}ms`);
                setTimeout(() => this.cleanupUrlParameters(), remainingTime);
                return;
            }
            
            url.searchParams.delete('loading');
            window.history.replaceState({}, '', url);
            console.log('🧹 ComponentDetailLoadingSystem: Cleaned up loading URL parameter');
        }
    },
    
    /**
     * Handle loading errors
     */
    handleLoadingError(error, context = '') {
        console.error(`❌ ComponentDetailLoadingSystem: Loading error${context ? ` (${context})` : ''}:`, error);
        
        this.updateLoadingMessage('Error loading component. Please refresh to try again.');
        
        // Complete loading with error state after 3 seconds
        setTimeout(() => {
            this.completeLoading('error');
        }, 3000);
        
        // Track error analytics
        this.trackLoadingError(error, context);
    },
    
    /**
     * Retry loading operation
     */
    retryLoading() {
        console.log('🔄 ComponentDetailLoadingSystem: Retrying loading operation');
        
        this.loadingStartTime = Date.now();
        this.currentStage = 0;
        
        if (this.alpineComponent) {
            this.alpineComponent.isLoading = true;
            this.alpineComponent.imagesLoading = true;
            this.alpineComponent.loadingProgress = 0;
        }
        
        this.activateImmediateLoading();
        this.setupProgressiveFeedback();
        
        // Restart auto-refresh if Alpine component has the method
        if (this.alpineComponent && typeof this.alpineComponent.startAutoRefresh === 'function') {
            this.alpineComponent.startAutoRefresh();
        }
    },
    
    /**
     * Get loading statistics
     */
    getLoadingStats() {
        return {
            startTime: this.loadingStartTime,
            currentStage: this.currentStage,
            totalStages: this.loadingStages.length,
            isLoading: this.alpineComponent?.imagesLoading || false,
            progress: this.alpineComponent?.loadingProgress || 0,
            message: this.alpineComponent?.loadingMessage || '',
            elapsedTime: this.loadingStartTime ? Date.now() - this.loadingStartTime : 0
        };
    },
    
    /**
     * Track loading completion analytics
     */
    trackLoadingCompletion(duration, reason) {
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track('Component Loading Completed', {
                duration,
                reason,
                componentId: this.alpineComponent?.componentData?.id,
                totalImages: this.alpineComponent?.totalImages
            });
        }
        
        console.log('📊 ComponentDetailLoadingSystem: Loading completion tracked:', { duration, reason });
    },
    
    /**
     * Track loading error analytics
     */
    trackLoadingError(error, context) {
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track('Component Loading Error', {
                error: error.message || error.toString(),
                context,
                componentId: this.alpineComponent?.componentData?.id,
                elapsed: Date.now() - this.loadingStartTime
            });
        }
        
        console.log('📊 ComponentDetailLoadingSystem: Loading error tracked:', { error, context });
    }
};

/**
 * Loading State Manager for multiple concurrent operations
 */
window.ComponentDetailLoadingStateManager = {
    
    activeOperations: new Set(),
    
    /**
     * Start a loading operation
     */
    startOperation(operationId, message = '') {
        this.activeOperations.add(operationId);
        console.log(`🔄 LoadingStateManager: Started operation ${operationId}`);
        
        if (message && window.ComponentDetailLoadingSystem.alpineComponent) {
            window.ComponentDetailLoadingSystem.updateLoadingMessage(message);
        }
        
        this.updateOverallLoadingState();
    },
    
    /**
     * Complete a loading operation
     */
    completeOperation(operationId) {
        this.activeOperations.delete(operationId);
        console.log(`✅ LoadingStateManager: Completed operation ${operationId}`);
        
        this.updateOverallLoadingState();
    },
    
    /**
     * Update overall loading state based on active operations
     */
    updateOverallLoadingState() {
        const hasActiveOperations = this.activeOperations.size > 0;
        
        if (!hasActiveOperations && window.ComponentDetailLoadingSystem.alpineComponent?.imagesLoading) {
            // All operations complete, finish loading
            window.ComponentDetailLoadingSystem.completeLoading('all_operations_complete');
        }
    },
    
    /**
     * Get active operations
     */
    getActiveOperations() {
        return Array.from(this.activeOperations);
    }
};

console.log('✅ Component Detail Loading System: Module loaded successfully');