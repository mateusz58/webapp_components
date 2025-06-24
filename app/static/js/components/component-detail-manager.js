/**
 * Component Detail Manager
 * Handles all functionality for the component detail page
 */
class ComponentDetailManager {
    constructor() {
        this.activeStatusForm = null;
        this.lightboxOpen = false;
        this.lightboxIndex = 0;
        this.selectedVariant = null;
        this.currentImageIndex = 0;
        this.activeTab = 'basic-info';
        
        // Data will be populated by the template
        this.componentImages = [];
        this.variants = [];
        
        this.init();
    }

    init() {
        this.currentImageIndex = 0;
        console.log('Component Detail initialized with activeTab:', this.activeTab);
        this.setupKeyboardNavigation();
    }

    setupKeyboardNavigation() {
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
    }

    get currentImages() {
        if (this.selectedVariant === null) {
            return this.componentImages;
        } else {
            const variant = this.variants.find(v => v.id === this.selectedVariant);
            return variant ? variant.images : [];
        }
    }

    get currentVariant() {
        if (this.selectedVariant === null) {
            return { name: 'Component Images' };
        }
        return this.variants.find(v => v.id === this.selectedVariant);
    }

    selectVariant(variantId) {
        this.selectedVariant = variantId;
        this.currentImageIndex = 0;
    }

    toggleStatusForm(formType) {
        this.activeStatusForm = this.activeStatusForm === formType ? null : formType;
    }

    openLightbox(imageIndex) {
        this.lightboxIndex = imageIndex;
        this.lightboxOpen = true;
        document.body.style.overflow = 'hidden';
    }

    closeLightbox() {
        this.lightboxOpen = false;
        document.body.style.overflow = 'auto';
    }

    nextImage() {
        if (this.currentImages.length > 0) {
            this.lightboxIndex = (this.lightboxIndex + 1) % this.currentImages.length;
        }
    }

    previousImage() {
        if (this.currentImages.length > 0) {
            this.lightboxIndex = this.lightboxIndex === 0 ? this.currentImages.length - 1 : this.lightboxIndex - 1;
        }
    }

    selectTab(tabName) {
        console.log('Switching to tab:', tabName);
        this.activeTab = tabName;
    }

    async duplicateComponent(componentId) {
        if (confirm('Create a duplicate of this component?')) {
            try {
                const response = await fetch(`/api/components/${componentId}/duplicate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrf_token]')?.value
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = `/component/${data.new_id}`;
                } else {
                    alert('Error creating duplicate: ' + data.error);
                }
            } catch (error) {
                console.error('Error duplicating component:', error);
                alert('Error creating duplicate component');
            }
        }
    }

    // Method to refresh variant data via AJAX (for the image visibility fix)
    async refreshVariantData() {
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
                return true;
            } else {
                console.error('Failed to refresh variant data:', response.statusText);
                return false;
            }
        } catch (error) {
            console.error('Error refreshing variant data:', error);
            return false;
        }
    }
}

// Export for global access
window.ComponentDetailManager = ComponentDetailManager;