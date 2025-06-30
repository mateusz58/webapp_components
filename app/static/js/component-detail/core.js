/**
 * Component Detail Core Module
 * Main Alpine.js application factory and core functionality
 * Built from scratch following TDD methodology
 */

/**
 * Main Alpine.js Component Factory
 * This is the core application component that manages all state and functionality
 */
function ComponentDetailApp() {
    console.log('🏭 ComponentDetailApp: Factory function called');
    console.log('📍 Current URL:', window.location.href);
    
    // Initialize loading state based on URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const hasLoadingParam = urlParams.get('loading') === 'true';
    
    console.log('🔍 ComponentDetailApp: Loading parameter check:', {
        hasLoadingParam,
        searchParams: window.location.search
    });
    
    // Set global loading start time for performance tracking
    if (hasLoadingParam && !window.componentDetailLoadStart) {
        window.componentDetailLoadStart = Date.now();
        console.log('⏱️ ComponentDetailApp: Loading start time recorded:', window.componentDetailLoadStart);
    }
    
    return {
        // === CORE STATE ===
        // Loading states
        isLoading: hasLoadingParam,
        imagesLoading: hasLoadingParam,
        loadingMessage: hasLoadingParam ? 'Loading component images...' : '',
        loadingProgress: 0,
        
        // UI states
        activeTab: 'basic-info',
        activeStatusForm: null,
        
        // Gallery states
        lightboxOpen: false,
        lightboxIndex: 0,
        selectedVariant: null,
        currentImageIndex: 0,
        
        // Data states
        componentData: null,
        componentImages: [],
        variants: [],
        
        // === COMPUTED PROPERTIES ===
        get hasImages() {
            return this.componentImages.length > 0 || 
                   this.variants.some(v => v.images && v.images.length > 0);
        },
        
        get currentImages() {
            if (this.selectedVariant === null) {
                return this.componentImages;
            }
            const variant = this.variants.find(v => v.id === this.selectedVariant);
            return variant ? variant.images : [];
        },
        
        get currentVariant() {
            if (this.selectedVariant === null) {
                return { name: 'Component Images' };
            }
            return this.variants.find(v => v.id === this.selectedVariant);
        },
        
        get totalImages() {
            const componentCount = this.componentImages.length;
            const variantCount = this.variants.reduce((sum, v) => sum + (v.images?.length || 0), 0);
            return componentCount + variantCount;
        },
        
        // === INITIALIZATION ===
        init() {
            console.log('🚀 ComponentDetailApp: Initializing application');
            console.log('🔗 URL:', window.location.href);
            console.log('📊 Initial state:', {
                isLoading: this.isLoading,
                imagesLoading: this.imagesLoading,
                hasLoadingParam: hasLoadingParam
            });
            
            // Initialize current image index
            this.currentImageIndex = 0;
            
            // Load server data
            this.loadServerData();
            
            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (this.lightboxOpen) {
                    if (e.key === 'Escape') {
                        this.closeLightbox();
                    } else if (e.key === 'ArrowLeft') {
                        this.previousImage();
                    } else if (e.key === 'ArrowRight') {
                        this.nextImage();
                    }
                }
            });
            
            // Check if we should show loading state
            this.checkForLoadingState();
            
            console.log('✅ ComponentDetailApp: Initialization complete');
        },
        
        // === DATA MANAGEMENT ===
        loadServerData() {
            console.log('📥 ComponentDetailApp: Loading server data');
            
            if (window.componentServerData) {
                // Load component metadata
                this.componentData = window.componentServerData.component;
                
                // Load images
                this.componentImages = window.componentServerData.componentImages || [];
                this.variants = window.componentServerData.variants || [];
                
                console.log('📊 ComponentDetailApp: Server data loaded:', {
                    componentId: this.componentData?.id,
                    componentImages: this.componentImages.length,
                    variants: this.variants.length,
                    totalImages: this.totalImages
                });
                
                // Debug: Log first few images
                console.log('📷 Component images:', this.componentImages);
                console.log('🎨 Variants with images:', this.variants.map(v => ({
                    id: v.id, 
                    name: v.name, 
                    images: v.images?.length || 0
                })));
                console.log('🖼️ Current images (computed):', this.currentImages);
            } else {
                console.warn('⚠️ ComponentDetailApp: No server data available');
            }
        },
        
        // === LOADING SYSTEM ===
        checkForLoadingState() {
            console.log('=== Checking Loading State ===');
            
            // Check URL parameter for fallback loading case
            const urlParams = new URLSearchParams(window.location.search);
            const hasLoadingParam = urlParams.get('loading') === 'true';
            
            // Check if we have images loaded
            const hasImages = this.componentImages.length > 0 || 
                             this.variants.some(v => v.images && v.images.length > 0);
            
            console.log('Loading check results:', { 
                hasLoadingParam, 
                hasImages, 
                componentImages: this.componentImages.length, 
                variants: this.variants.length 
            });
            
            // Only show loading if explicitly requested (fallback case) AND no images
            if (hasLoadingParam && !hasImages) {
                console.log('🔄 URL loading parameter found with no images - starting fallback auto-refresh');
                this.imagesLoading = true;
                this.loadingMessage = 'Loading images...';
                if (!window.componentDetailLoadStart) {
                    window.componentDetailLoadStart = Date.now();
                }
                
                // Shorter, simpler auto-refresh for fallback only
                setTimeout(() => this.startAutoRefresh(), 500);
                return;
            }
            
            // Clean up loading parameter if images are present
            if (hasLoadingParam && hasImages) {
                console.log('🧹 Loading parameter found but images present - cleaning up URL');
                this.cleanupUrlParameters();
            }
            
            console.log('✅ No loading state needed - server verification ensures images are ready');
        },

        // Check if this is likely a newly created component
        isLikelyNewComponent() {
            // Check URL parameter first (most reliable)
            const urlParams = new URLSearchParams(window.location.search);
            const hasLoadingParam = urlParams.get('loading') === 'true';
            
            // Check if we came from the create form
            const referrer = document.referrer;
            const isFromCreateForm = referrer.includes('/component/new') || referrer.includes('/component/create');
            
            // Check if the component was created recently (within last 10 minutes)
            const currentTime = new Date();
            const componentCreatedTime = new Date(window.componentCreatedAt || 0);
            const timeDiff = currentTime - componentCreatedTime;
            const isRecentlyCreated = timeDiff < 10 * 60 * 1000; // 10 minutes
            
            console.log('New component check:', { 
                hasLoadingParam,
                isFromCreateForm, 
                isRecentlyCreated, 
                timeDiff: Math.round(timeDiff / 1000), 
                referrer 
            });
            
            return hasLoadingParam || isFromCreateForm || isRecentlyCreated;
        },

        initializeLoadingSystem() {
            console.log('🔄 ComponentDetailApp: Initializing loading system');
            
            // Check if we should show loading state
            if (this.shouldShowLoading()) {
                console.log('🔄 ComponentDetailApp: Starting auto-refresh process');
                setTimeout(() => this.startAutoRefresh(), 200);
            } else {
                console.log('✅ ComponentDetailApp: No loading needed - images already available');
                this.completeLoading();
            }
        },
        
        shouldShowLoading() {
            const urlParams = new URLSearchParams(window.location.search);
            const hasLoadingParam = urlParams.get('loading') === 'true';
            
            // Always show loading if URL parameter is present (redirect case)
            if (hasLoadingParam) {
                console.log('🔄 ComponentDetailApp: Loading required - URL parameter present');
                return true;
            }
            
            // Show loading if no images are available
            if (!this.hasImages) {
                console.log('🔄 ComponentDetailApp: Loading required - no images available');
                return true;
            }
            
            return false;
        },
        
        async startAutoRefresh() {
            console.log('🔄 ComponentDetailApp: Starting fallback auto-refresh for image loading');
            
            const componentId = this.componentData?.id || window.location.pathname.split('/').pop();
            let attempts = 0;
            const maxAttempts = 3; // Reduced attempts since server should have verified
            
            while (attempts < maxAttempts && this.imagesLoading) {
                attempts++;
                this.loadingMessage = `Loading images... (${attempts}/${maxAttempts})`;
                this.loadingProgress = (attempts / maxAttempts) * 100;
                
                console.log(`🔄 ComponentDetailApp: Refresh attempt ${attempts}/${maxAttempts}`);
                
                try {
                    const response = await fetch(`/api/components/${componentId}/variants`, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'Cache-Control': 'no-cache'
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('📥 ComponentDetailApp: API response received:', data);
                        
                        // Update data
                        this.variants = data.variants || [];
                        this.componentImages = data.component_images || [];
                        
                        // Check if we have images now
                        if (this.hasImages) {
                            // For redirect case, also verify images are actually accessible
                            const urlParams = new URLSearchParams(window.location.search);
                            const isRedirectCase = urlParams.get('loading') === 'true';
                            
                            if (isRedirectCase && attempts === 1) {
                                // On first attempt for redirect case, test if images are actually loading
                                console.log('🔍 Redirect case: Testing if images are actually accessible...');
                                
                                const imageAccessible = await this.testImageAccessibility();
                                
                                if (!imageAccessible) {
                                    console.log('⚠️ Images not yet accessible, will retry...');
                                    // Continue to next attempt
                                } else {
                                    console.log('✅ ComponentDetailApp: Images loaded and accessible');
                                    this.completeLoading();
                                    break;
                                }
                            } else {
                                console.log('✅ ComponentDetailApp: Images loaded successfully');
                                this.completeLoading();
                                break;
                            }
                        } else if (attempts >= 3) {
                            // After 3 attempts, stop trying even if no images
                            console.log('⚠️ No images found after 3 attempts - stopping refresh');
                            this.completeLoading();
                            break;
                        }
                    } else {
                        console.warn(`⚠️ ComponentDetailApp: API request failed with status ${response.status}`);
                    }
                } catch (error) {
                    console.error('❌ ComponentDetailApp: Error during auto-refresh:', error);
                }
                
                // Wait before next attempt (exponential backoff)
                if (attempts < maxAttempts) {
                    const delay = attempts === 1 ? 500 : attempts * 1000;
                    console.log(`⏱️ ComponentDetailApp: Waiting ${delay}ms before next attempt`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
            
            // Complete loading even if no images found
            if (attempts >= maxAttempts) {
                console.warn('⚠️ ComponentDetailApp: Max refresh attempts reached');
                this.completeLoading();
            }
        },
        
        completeLoading() {
            console.log('✅ ComponentDetailApp: Completing loading process');
            console.log('📷 Current state before completion:');
            console.log('   - componentImages:', this.componentImages.length);
            console.log('   - variants:', this.variants.length);
            console.log('   - currentImages:', this.currentImages.length);
            console.log('   - selectedVariant:', this.selectedVariant);
            console.log('   - hasImages:', this.hasImages);
            
            this.isLoading = false;
            this.imagesLoading = false;
            this.loadingMessage = '';
            this.loadingProgress = 100;
            
            // Force Alpine.js to re-evaluate reactive data
            this.$nextTick(() => {
                console.log('📷 State after completion and nextTick:');
                console.log('   - imagesLoading:', this.imagesLoading);
                console.log('   - currentImages.length:', this.currentImages.length);
                console.log('   - First image URL:', this.currentImages[0]?.url);
            });
            
            // Clean up URL parameter
            this.cleanupUrlParameters();
            
            // Remove loading class from document
            document.documentElement.classList.remove('loading-active');
            document.body.removeAttribute('data-initial-loading');
            
            // Track loading time
            if (window.componentDetailLoadStart) {
                const loadTime = Date.now() - window.componentDetailLoadStart;
                console.log(`⏱️ ComponentDetailApp: Total loading time: ${loadTime}ms`);
            }
        },
        
        cleanupUrlParameters() {
            const url = new URL(window.location);
            if (url.searchParams.has('loading')) {
                // Ensure loading indicator is visible for at least 2 seconds for UX
                const loadStart = window.componentDetailLoadStart || Date.now();
                const elapsed = Date.now() - loadStart;
                const minDisplayTime = 2000;
                
                if (elapsed < minDisplayTime) {
                    const remainingTime = minDisplayTime - elapsed;
                    console.log(`🕐 ComponentDetailApp: Delaying URL cleanup for ${remainingTime}ms`);
                    setTimeout(() => this.cleanupUrlParameters(), remainingTime);
                    return;
                }
                
                url.searchParams.delete('loading');
                window.history.replaceState({}, '', url);
                console.log('🧹 ComponentDetailApp: Cleaned up loading URL parameter');
            }
        },

        // Test if images are actually accessible (for redirect case)
        async testImageAccessibility() {
            try {
                // Get the first image URL to test
                let testUrl = null;
                
                if (this.componentImages.length > 0) {
                    testUrl = this.componentImages[0].url;
                } else if (this.variants.length > 0 && this.variants[0].images.length > 0) {
                    testUrl = this.variants[0].images[0].url;
                }
                
                if (!testUrl) {
                    console.log('🔍 No image URL to test');
                    return true; // No images to test
                }
                
                console.log(`🔍 Testing image accessibility: ${testUrl}`);
                
                // Try to fetch the image with a short timeout
                const response = await fetch(testUrl, {
                    method: 'HEAD', // Just check if accessible, don't download
                    signal: AbortSignal.timeout(3000) // 3 second timeout
                });
                
                const accessible = response.ok;
                console.log(`🔍 Image accessibility test result: ${accessible} (status: ${response.status})`);
                
                return accessible;
                
            } catch (error) {
                console.log(`🔍 Image accessibility test failed: ${error.message}`);
                return false; // Not accessible yet
            }
        },
        
        // === GALLERY FUNCTIONALITY ===
        initializeGallery() {
            console.log('🖼️ ComponentDetailApp: Initializing gallery');
            
            // Initialize gallery module if available
            if (window.ComponentDetailGallery && typeof window.ComponentDetailGallery.init === 'function') {
                window.ComponentDetailGallery.init(this);
            }
        },
        
        selectVariant(variantId) {
            console.log('🎨 ComponentDetailApp: Selecting variant:', variantId);
            this.selectedVariant = variantId;
            this.currentImageIndex = 0;
        },
        
        openLightbox(imageIndex) {
            console.log('🔍 ComponentDetailApp: Opening lightbox at index:', imageIndex);
            this.lightboxIndex = imageIndex;
            this.lightboxOpen = true;
            document.body.style.overflow = 'hidden';
        },
        
        closeLightbox() {
            console.log('🔍 ComponentDetailApp: Closing lightbox');
            this.lightboxOpen = false;
            document.body.style.overflow = 'auto';
        },
        
        nextImage() {
            if (this.currentImages.length > 0) {
                this.lightboxIndex = (this.lightboxIndex + 1) % this.currentImages.length;
            }
        },
        
        previousImage() {
            if (this.currentImages.length > 0) {
                this.lightboxIndex = this.lightboxIndex === 0 ? 
                    this.currentImages.length - 1 : this.lightboxIndex - 1;
            }
        },
        
        // === TAB FUNCTIONALITY ===
        selectTab(tabName) {
            console.log('📑 ComponentDetailApp: Switching to tab:', tabName);
            this.activeTab = tabName;
        },
        
        // === STATUS FORM FUNCTIONALITY ===
        toggleStatusForm(formType) {
            console.log('📝 ComponentDetailApp: Toggling status form:', formType);
            this.activeStatusForm = this.activeStatusForm === formType ? null : formType;
        },
        
        // === AUTO-REFRESH FUNCTIONALITY (ORIGINAL COMPATIBILITY) ===
        async autoRefreshVariants() {
            console.log('🔄 ComponentDetailApp: autoRefreshVariants() called - delegating to startAutoRefresh()');
            return await this.startAutoRefresh();
        },

        // === COMPONENT ACTIONS ===
        async duplicateComponent() {
            const componentId = this.componentData?.id || window.location.pathname.split('/').pop();
            
            console.log('📋 ComponentDetailApp: Duplicating component:', componentId);
            
            try {
                const response = await fetch(`/api/components/${componentId}/duplicate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.new_component_id) {
                        console.log('✅ ComponentDetailApp: Component duplicated successfully');
                        window.location.href = `/component/${data.new_component_id}`;
                    } else {
                        throw new Error(data.message || 'Unknown error');
                    }
                } else {
                    throw new Error('Request failed');
                }
            } catch (error) {
                console.error('❌ ComponentDetailApp: Error duplicating component:', error);
                alert('Failed to duplicate component. Please try again.');
            }
        }
    };
}

// Make the component factory globally available
window.ComponentDetailApp = ComponentDetailApp;

console.log('✅ Component Detail Core: Module loaded successfully');
console.log('🔧 ComponentDetailApp function available:', typeof ComponentDetailApp);

// Debug: Test immediate function call
console.log('🧪 Testing ComponentDetailApp factory...');
try {
    const testApp = ComponentDetailApp();
    console.log('✅ ComponentDetailApp factory works:', typeof testApp, Object.keys(testApp).slice(0, 5));
} catch (error) {
    console.error('❌ ComponentDetailApp factory failed:', error);
}