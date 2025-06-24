/**
 * Component Detail Page - Picture Visibility Fix
 * 
 * Addresses the variant picture visibility issue by refreshing 
 * variant data via AJAX after initial page load
 */

class ComponentDetailManager {
    constructor() {
        this.componentId = null;
        this.alpineComponent = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    init() {
        // Extract component ID immediately
        const urlParts = window.location.pathname.split('/');
        if (urlParts[1] === 'component' && urlParts[2]) {
            this.componentId = parseInt(urlParts[2]);
            
            // Start refresh process immediately - don't wait for Alpine
            this.startImmediateRefresh();
        }
    }
    
    startImmediateRefresh() {
        // First attempt - refresh data immediately
        setTimeout(() => {
            this.attemptDataRefresh();
        }, 500);
        
        // Second attempt - in case Alpine wasn't ready
        setTimeout(() => {
            this.attemptDataRefresh();
        }, 1500);
        
        // Third attempt - final fallback
        setTimeout(() => {
            this.attemptDataRefresh();
        }, 3000);
    }
    
    attemptDataRefresh() {
        const alpineElement = document.querySelector('[x-data]');
        if (alpineElement && window.Alpine) {
            try {
                this.alpineComponent = Alpine.$data(alpineElement);
                if (this.alpineComponent) {
                    console.log('Refreshing variant data...');
                    this.refreshVariantData();
                }
            } catch (e) {
                console.log('Alpine not ready yet:', e);
            }
        }
    }
    
    checkAndRefreshVariantPictures() {
        if (!this.alpineComponent || !this.componentId) return;
        
        // Wait a bit for initial page load to settle
        setTimeout(() => {
            this.performRefreshCheck();
        }, 1500);
    }
    
    performRefreshCheck() {
        if (!this.alpineComponent) return;
        
        // Check if any variants show they have pictures in chips but Alpine data is empty
        const needsRefresh = this.alpineComponent.variants.some(variant => {
            const hasEmptyImages = variant.images.length === 0;
            const chipShowsPictures = this.variantChipShowsPictures(variant.id);
            
            if (hasEmptyImages && chipShowsPictures) {
                console.log(`Variant ${variant.id} has empty images but chip shows pictures`);
                return true;
            }
            return false;
        });
        
        // Also check if main image is showing but no variant images are available when switching
        const hasMainImageButNoVariantData = this.alpineComponent.componentImages.length > 0 && 
            this.alpineComponent.variants.length > 0 && 
            this.alpineComponent.variants.every(v => v.images.length === 0);
        
        if (needsRefresh || hasMainImageButNoVariantData) {
            console.log('Variant picture data inconsistency detected, refreshing...');
            this.refreshVariantData();
        }
    }
    
    variantChipShowsPictures(variantId) {
        // Check if variant chip shows it has pictures
        const variantChips = document.querySelectorAll('.variant-chip');
        for (const chip of variantChips) {
            const text = chip.textContent;
            // Look for patterns like "Red (1)" or "Green (15)" indicating any number of pictures
            // Match pattern: "Color Name (N)" where N is any number > 0
            const pictureCountMatch = text.match(/\((\d+)\)/);
            if (pictureCountMatch && !text.includes('Component Images')) {
                const count = parseInt(pictureCountMatch[1]);
                if (count > 0) {
                    return true;
                }
            }
        }
        return false;
    }
    
    async refreshVariantData() {
        try {
            const response = await fetch(`/api/components/${this.componentId}/variants`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (response.ok) {
                const variantData = await response.json();
                this.updateAlpineVariantData(variantData);
                console.log('Variant data refreshed successfully');
            } else {
                console.warn('Failed to refresh variant data:', response.status);
                this.handleRefreshFailure();
            }
        } catch (error) {
            console.error('Error refreshing variant data:', error);
            this.handleRefreshFailure();
        }
    }
    
    updateAlpineVariantData(variantData) {
        if (!this.alpineComponent) return;
        
        console.log('Updating Alpine data with fresh variant data:', variantData);
        
        // Update both variants and component images
        this.alpineComponent.variants = variantData.variants || [];
        this.alpineComponent.componentImages = variantData.component_images || [];
        
        // Force immediate re-render by triggering Alpine's reactivity
        this.alpineComponent.$nextTick(() => {
            // Reset selection to trigger image refresh
            const currentVariant = this.alpineComponent.selectedVariant;
            this.alpineComponent.selectedVariant = null;
            this.alpineComponent.currentImageIndex = 0;
            
            this.alpineComponent.$nextTick(() => {
                this.alpineComponent.selectedVariant = currentVariant;
                console.log('Alpine data updated successfully');
            });
        });
    }
    
    handleRefreshFailure() {
        this.retryCount++;
        
        if (this.retryCount < this.maxRetries) {
            console.log(`Retrying variant data refresh (${this.retryCount}/${this.maxRetries})...`);
            setTimeout(() => {
                this.refreshVariantData();
            }, 1000 * this.retryCount); // Exponential backoff
        } else {
            console.warn('Max retries reached for variant data refresh');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on component detail pages
    if (window.location.pathname.includes('/component/') && !window.location.pathname.includes('/edit')) {
        new ComponentDetailManager();
    }
});