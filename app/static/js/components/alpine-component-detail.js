/**
 * Alpine.js Component Detail Data Function
 * Provides reactive data for component detail page
 */
function componentDetail() {
    return {
        activeStatusForm: null,
        lightboxOpen: false,
        lightboxIndex: 0,
        selectedVariant: null,
        currentImageIndex: 0,
        activeTab: 'basic-info',

        // Component data from server (will be populated by template)
        componentImages: [],
        variants: [],

        get currentImages() {
            if (this.selectedVariant === null) {
                return this.componentImages;
            } else {
                const variant = this.variants.find(v => v.id === this.selectedVariant);
                return variant ? variant.images : [];
            }
        },

        get currentVariant() {
            if (this.selectedVariant === null) {
                return { name: 'Component Images' };
            }
            return this.variants.find(v => v.id === this.selectedVariant);
        },

        init() {
            this.currentImageIndex = 0;
            console.log('Component Detail initialized with activeTab:', this.activeTab);

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

            // Auto-refresh variant data for image visibility fix
            this.autoRefreshVariants();
        },

        selectVariant(variantId) {
            this.selectedVariant = variantId;
            this.currentImageIndex = 0;
        },

        toggleStatusForm(formType) {
            this.activeStatusForm = this.activeStatusForm === formType ? null : formType;
        },

        openLightbox(imageIndex) {
            this.lightboxIndex = imageIndex;
            this.lightboxOpen = true;
            document.body.style.overflow = 'hidden';
        },

        closeLightbox() {
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
                this.lightboxIndex = this.lightboxIndex === 0 ? this.currentImages.length - 1 : this.lightboxIndex - 1;
            }
        },

        async duplicateComponent() {
            const componentId = window.location.pathname.split('/').pop();
            const manager = new ComponentDetailManager();
            await manager.duplicateComponent(componentId);
        },

        selectTab(tabName) {
            console.log('Switching to tab:', tabName);
            this.activeTab = tabName;
        },

        // Auto-refresh variants for image visibility fix
        async autoRefreshVariants() {
            const manager = new ComponentDetailManager();
            
            // Try 3 times with increasing delays
            const attempts = [500, 1500, 3000];
            
            for (const delay of attempts) {
                setTimeout(async () => {
                    console.log('Refreshing variant data...');
                    
                    try {
                        const componentId = window.location.pathname.split('/').pop();
                        const response = await fetch(`/api/components/${componentId}/variants`);
                        
                        if (response.ok) {
                            const data = await response.json();
                            
                            // Update variants data
                            this.variants = data.variants || [];
                            this.componentImages = data.component_images || [];
                            
                            console.log('Variant data refreshed successfully');
                        }
                    } catch (error) {
                        console.error('Error refreshing variant data:', error);
                    }
                }, delay);
            }
        }
    }
}

// Make function globally available
window.componentDetail = componentDetail;