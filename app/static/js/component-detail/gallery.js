/**
 * Component Detail Gallery Module
 * Handles image gallery, lightbox, thumbnails, and variant switching
 * Built from scratch following TDD methodology
 */

/**
 * Gallery Management System
 */
window.ComponentDetailGallery = {
    
    alpineComponent: null,
    
    /**
     * Initialize gallery system
     */
    init(alpineComponent) {
        console.log('🖼️ ComponentDetailGallery: Initializing gallery system');
        
        this.alpineComponent = alpineComponent;
        
        // Set up keyboard navigation
        this.setupKeyboardNavigation();
        
        // Set up touch/swipe support
        this.setupTouchSupport();
        
        // Set up image lazy loading
        this.setupLazyLoading();
        
        // Set up image error handling
        this.setupImageErrorHandling();
        
        console.log('✅ ComponentDetailGallery: Gallery system initialized');
    },
    
    /**
     * Set up keyboard navigation for lightbox
     */
    setupKeyboardNavigation() {
        console.log('⌨️ ComponentDetailGallery: Setting up keyboard navigation');
        
        document.addEventListener('keydown', (e) => {
            if (!this.alpineComponent?.lightboxOpen) return;
            
            switch (e.key) {
                case 'Escape':
                    e.preventDefault();
                    this.closeLightbox();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousImage();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextImage();
                    break;
                case ' ': // Spacebar
                    e.preventDefault();
                    this.nextImage();
                    break;
            }
        });
    },
    
    /**
     * Set up touch/swipe support for mobile
     */
    setupTouchSupport() {
        console.log('👆 ComponentDetailGallery: Setting up touch support');
        
        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;
        
        document.addEventListener('touchstart', (e) => {
            if (!this.alpineComponent?.lightboxOpen) return;
            
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!this.alpineComponent?.lightboxOpen) return;
            
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const threshold = 50;
            
            // Only handle horizontal swipes that are greater than vertical movement
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
                if (deltaX > 0) {
                    this.previousImage(); // Swipe right = previous
                } else {
                    this.nextImage(); // Swipe left = next
                }
            }
        });
    },
    
    /**
     * Set up lazy loading for images
     */
    setupLazyLoading() {
        console.log('🔄 ComponentDetailGallery: Setting up lazy loading');
        
        // Use Intersection Observer for lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.dataset.src;
                        
                        if (src) {
                            img.src = src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                            
                            console.log('🖼️ ComponentDetailGallery: Lazy loaded image:', src);
                        }
                    }
                });
            });
            
            // Observe all images with data-src attribute
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    },
    
    /**
     * Set up error handling for failed image loads
     */
    setupImageErrorHandling() {
        console.log('🚨 ComponentDetailGallery: Setting up image error handling');
        
        document.addEventListener('error', (e) => {
            if (e.target.tagName === 'IMG') {
                console.warn('⚠️ ComponentDetailGallery: Image failed to load:', e.target.src);
                this.handleImageError(e.target);
            }
        }, true);
    },
    
    /**
     * Handle image loading errors
     */
    handleImageError(img) {
        // Add error class for styling
        img.classList.add('image-error');
        
        // Set fallback image or placeholder
        if (!img.classList.contains('fallback-attempted')) {
            img.classList.add('fallback-attempted');
            
            // Try to replace with a placeholder
            const placeholder = this.createImagePlaceholder(img.alt || 'Image not available');
            img.parentNode.replaceChild(placeholder, img);
        }
    },
    
    /**
     * Create image placeholder element
     */
    createImagePlaceholder(altText) {
        const placeholder = document.createElement('div');
        placeholder.className = 'image-placeholder';
        placeholder.innerHTML = `
            <div class="image-placeholder__icon">📷</div>
            <div class="image-placeholder__text">${altText}</div>
        `;
        return placeholder;
    },
    
    /**
     * Select variant and update gallery
     */
    selectVariant(variantId) {
        console.log('🎨 ComponentDetailGallery: Selecting variant:', variantId);
        
        if (this.alpineComponent) {
            this.alpineComponent.selectedVariant = variantId;
            this.alpineComponent.currentImageIndex = 0;
            
            // Update gallery display
            this.updateGalleryDisplay();
        }
    },
    
    /**
     * Update gallery display after variant change
     */
    updateGalleryDisplay() {
        console.log('🔄 ComponentDetailGallery: Updating gallery display');
        
        // Trigger lazy loading for new images
        setTimeout(() => {
            this.setupLazyLoading();
        }, 100);
        
        // Update thumbnail active states
        this.updateThumbnailStates();
    },
    
    /**
     * Update thumbnail active states
     */
    updateThumbnailStates() {
        const thumbnails = document.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, index) => {
            if (index === this.alpineComponent?.currentImageIndex) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });
    },
    
    /**
     * Open lightbox at specific index
     */
    openLightbox(imageIndex = 0) {
        console.log('🔍 ComponentDetailGallery: Opening lightbox at index:', imageIndex);
        
        if (this.alpineComponent) {
            this.alpineComponent.lightboxIndex = imageIndex;
            this.alpineComponent.lightboxOpen = true;
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
            document.body.classList.add('lightbox-open');
            
            // Preload adjacent images
            this.preloadAdjacentImages(imageIndex);
            
            // Track analytics
            this.trackGalleryEvent('lightbox_open', { imageIndex });
        }
    },
    
    /**
     * Close lightbox
     */
    closeLightbox() {
        console.log('🔍 ComponentDetailGallery: Closing lightbox');
        
        if (this.alpineComponent) {
            this.alpineComponent.lightboxOpen = false;
            
            // Restore body scroll
            document.body.style.overflow = 'auto';
            document.body.classList.remove('lightbox-open');
            
            // Track analytics
            this.trackGalleryEvent('lightbox_close');
        }
    },
    
    /**
     * Navigate to next image
     */
    nextImage() {
        if (!this.alpineComponent?.currentImages?.length) return;
        
        const currentIndex = this.alpineComponent.lightboxIndex;
        const nextIndex = (currentIndex + 1) % this.alpineComponent.currentImages.length;
        
        console.log('➡️ ComponentDetailGallery: Next image:', nextIndex);
        
        this.alpineComponent.lightboxIndex = nextIndex;
        this.preloadAdjacentImages(nextIndex);
        
        // Track analytics
        this.trackGalleryEvent('next_image', { from: currentIndex, to: nextIndex });
    },
    
    /**
     * Navigate to previous image
     */
    previousImage() {
        if (!this.alpineComponent?.currentImages?.length) return;
        
        const currentIndex = this.alpineComponent.lightboxIndex;
        const prevIndex = currentIndex === 0 ? 
            this.alpineComponent.currentImages.length - 1 : currentIndex - 1;
        
        console.log('⬅️ ComponentDetailGallery: Previous image:', prevIndex);
        
        this.alpineComponent.lightboxIndex = prevIndex;
        this.preloadAdjacentImages(prevIndex);
        
        // Track analytics
        this.trackGalleryEvent('previous_image', { from: currentIndex, to: prevIndex });
    },
    
    /**
     * Preload adjacent images for better performance
     */
    preloadAdjacentImages(currentIndex) {
        if (!this.alpineComponent?.currentImages?.length) return;
        
        const images = this.alpineComponent.currentImages;
        const preloadIndices = [];
        
        // Previous image
        const prevIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
        preloadIndices.push(prevIndex);
        
        // Next image
        const nextIndex = (currentIndex + 1) % images.length;
        preloadIndices.push(nextIndex);
        
        preloadIndices.forEach(index => {
            if (images[index] && images[index].url) {
                const img = new Image();
                img.src = images[index].url;
                console.log('🔄 ComponentDetailGallery: Preloading image:', images[index].url);
            }
        });
    },
    
    /**
     * Get image dimensions for responsive display
     */
    async getImageDimensions(imageUrl) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                resolve({
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    aspectRatio: img.naturalWidth / img.naturalHeight
                });
            };
            img.onerror = () => {
                resolve({ width: 0, height: 0, aspectRatio: 1 });
            };
            img.src = imageUrl;
        });
    },
    
    /**
     * Optimize image display based on viewport
     */
    optimizeImageDisplay() {
        const images = document.querySelectorAll('.gallery-image');
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        images.forEach(async (img) => {
            if (!img.src) return;
            
            const dimensions = await this.getImageDimensions(img.src);
            
            // Set optimal display size
            if (dimensions.aspectRatio > 1) {
                // Landscape image
                img.style.maxWidth = Math.min(viewport.width * 0.9, 1200) + 'px';
                img.style.height = 'auto';
            } else {
                // Portrait image
                img.style.maxHeight = Math.min(viewport.height * 0.8, 800) + 'px';
                img.style.width = 'auto';
            }
        });
    },
    
    /**
     * Track gallery events for analytics
     */
    trackGalleryEvent(eventName, data = {}) {
        // Send analytics data if analytics system is available
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track(`Gallery ${eventName}`, {
                componentId: this.alpineComponent?.componentData?.id,
                selectedVariant: this.alpineComponent?.selectedVariant,
                totalImages: this.alpineComponent?.totalImages,
                ...data
            });
        }
        
        console.log('📊 ComponentDetailGallery: Event tracked:', eventName, data);
    },
    
    /**
     * Get gallery statistics
     */
    getGalleryStats() {
        if (!this.alpineComponent) return null;
        
        return {
            totalImages: this.alpineComponent.totalImages,
            componentImages: this.alpineComponent.componentImages.length,
            variantCount: this.alpineComponent.variants.length,
            selectedVariant: this.alpineComponent.selectedVariant,
            lightboxOpen: this.alpineComponent.lightboxOpen,
            currentImageIndex: this.alpineComponent.lightboxIndex
        };
    }
};

// Initialize gallery on window resize for responsive optimization
window.addEventListener('resize', debounce(() => {
    if (window.ComponentDetailGallery) {
        window.ComponentDetailGallery.optimizeImageDisplay();
    }
}, 250));

// Debounce utility function
function debounce(func, wait) {
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

console.log('✅ Component Detail Gallery: Module loaded successfully');