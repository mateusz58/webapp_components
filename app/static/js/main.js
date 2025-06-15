/* Main JavaScript Entry Point */

/**
 * Main application JavaScript file
 * Loads all utility modules and initializes global functionality
 */

// This file serves as the main entry point for JavaScript functionality
// It loads all the required utility modules and sets up global functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Variant image preview on hover
    enableVariantImagePreview();
    
    // Keyword expansion functionality
    enableKeywordExpansion();
    
    console.log('Main JavaScript initialized');
});

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    if (window.AppUtils) {
        AppUtils.showFlashMessage('An unexpected error occurred', 'error');
    }
});

// Global error handler for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
});

// Export app version for debugging
window.APP_INFO = {
    name: 'Component Management System',
    version: '1.0.0',
    environment: 'development'
};

// Variant image preview on hover
window.enableVariantImagePreview = function enableVariantImagePreview() {
    // Helper function to validate image URL
    function isValidImageUrl(url) {
        if (!url || url === 'null' || url === 'undefined' || url.trim() === '') {
            return false;
        }
        // Check if URL is properly formatted
        try {
            new URL(url, window.location.origin);
            return true;
        } catch {
            return false;
        }
    }

    // Helper function to handle image load errors
    function handleImageError(mainImg, originalSrc, errorMessage = 'Variant image not available') {
        console.warn(errorMessage);
        // Restore original image immediately
        if (originalSrc) {
            mainImg.src = originalSrc;
        }
        // Show a subtle indicator that variant image is not available
        mainImg.style.opacity = '0.7';
        setTimeout(() => {
            mainImg.style.opacity = '1';
        }, 300);
    }
    
    // Helper function to show no-image placeholder
    function showNoImagePlaceholder(mainImg, variantName) {
        // Create SVG placeholder as data URL
        const placeholderSvg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="140" viewBox="0 0 200 140">
                <rect width="200" height="140" fill="#f8f9fa" stroke="#e9ecef" stroke-width="2"/>
                <g transform="translate(100, 50)">
                    <circle cx="0" cy="0" r="15" fill="#dee2e6"/>
                    <path d="M-8 -5 L8 -5 L8 5 L-8 5 Z" fill="#6c757d"/>
                    <circle cx="-3" cy="-2" r="2" fill="#adb5bd"/>
                </g>
                <text x="100" y="85" text-anchor="middle" fill="#6c757d" font-family="Arial, sans-serif" font-size="12">
                    No image available
                </text>
                <text x="100" y="100" text-anchor="middle" fill="#adb5bd" font-family="Arial, sans-serif" font-size="10">
                    ${variantName}
                </text>
            </svg>
        `;
        
        const encodedSvg = 'data:image/svg+xml;base64,' + btoa(placeholderSvg);
        mainImg.src = encodedSvg;
        mainImg.style.transition = 'opacity 0.3s ease';
        mainImg.style.opacity = '1';
    }

    // Use a more universal approach that works with dynamic content
    document.addEventListener('mouseenter', function(e) {
        if (e.target.matches('.variant-color-dot[data-has-image="true"]')) {
            const dot = e.target;
            const card = dot.closest('.component-card');
            if (!card) return;
            
            // Find the main image in both grid and list views
            const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
            if (!mainImg) return;
            
            const bgImgMatch = dot.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/);
            if (!bgImgMatch || !bgImgMatch[1]) {
                console.warn('No valid background image URL found');
                return;
            }
            
            const variantImgUrl = bgImgMatch[1];
            
            // Validate the image URL
            if (!isValidImageUrl(variantImgUrl)) {
                console.warn('Invalid variant image URL:', variantImgUrl);
                return;
            }
            
            // Store original src if not already stored
            if (!mainImg.dataset.originalSrc) {
                mainImg.dataset.originalSrc = mainImg.src;
            }
            
            // Create a new image to test if the variant image loads
            const testImg = new Image();
            
            testImg.onload = function() {
                // Image loaded successfully, now change the main image
                mainImg.src = variantImgUrl;
                mainImg.style.transition = 'opacity 0.3s ease';
                
                // Clear any error state
                mainImg.style.opacity = '1';
            };
            
            testImg.onerror = function() {
                // Image failed to load, handle error gracefully
                handleImageError(mainImg, mainImg.dataset.originalSrc, `Failed to load variant image: ${variantImgUrl}`);
            };
            
            // Start loading the test image
            testImg.src = variantImgUrl;
        }
        // Handle variants without images - show placeholder
        else if (e.target.matches('.variant-color-dot[data-has-image="false"]')) {
            const dot = e.target;
            const card = dot.closest('.component-card');
            if (!card) return;
            
            // Find the main image in both grid and list views
            const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
            if (!mainImg) return;
            
            // Store original src if not already stored
            if (!mainImg.dataset.originalSrc) {
                mainImg.dataset.originalSrc = mainImg.src;
            }
            
            // Create a no-image placeholder
            showNoImagePlaceholder(mainImg, dot.dataset.variantName || 'Variant');
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        if (e.target.matches('.variant-color-dot[data-has-image="true"]') || e.target.matches('.variant-color-dot[data-has-image="false"]')) {
            const dot = e.target;
            const card = dot.closest('.component-card');
            if (!card) return;
            
            // Find the main image in both grid and list views
            const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
            if (!mainImg || !mainImg.dataset.originalSrc) return;
            
            try {
                // Restore original image with error handling
                mainImg.src = mainImg.dataset.originalSrc;
                
                // Clear any opacity effects
                mainImg.style.opacity = '1';
                
                // Add error handler for original image too
                mainImg.onerror = function() {
                    console.warn('Original image failed to load, using fallback');
                    // Don't let the main image disappear completely
                    this.style.display = 'block';
                    this.style.opacity = '0.5';
                };
            } catch (error) {
                console.error('Error restoring original image:', error);
                // Ensure image remains visible even if there's an error
                mainImg.style.display = 'block';
                mainImg.style.opacity = '1';
            }
        }
    }, true);
    
    // Also handle initial load for existing cards
    document.querySelectorAll('.component-card').forEach(card => {
        const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
        if (!mainImg) return;
        
        // Add error handling to main images
        mainImg.onerror = function() {
            console.warn('Main component image failed to load');
            // Create a placeholder div instead of broken image
            const placeholder = document.createElement('div');
            placeholder.className = 'd-flex align-items-center justify-content-center bg-light';
            placeholder.style.height = this.style.height || '140px';
            placeholder.innerHTML = '<i data-lucide="image" style="width: 32px; height: 32px; color: #9ca3af;"></i>';
            
            // Replace the broken image with placeholder
            this.parentNode.replaceChild(placeholder, this);
            
            // Reinitialize icons for the new placeholder
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        };
        
        const variantDots = card.querySelectorAll('.variant-color-dot');
        variantDots.forEach(dot => {
            // Check if this variant has a valid image
            if (dot.dataset.hasImage === 'true') {
                // Add cursor pointer style for variants with images
                dot.style.cursor = 'pointer';
                dot.title = dot.dataset.variantName || 'Variant preview';
                
                // Validate variant image URL on initialization
                const bgImgMatch = dot.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/);
                if (bgImgMatch && bgImgMatch[1]) {
                    const variantImgUrl = bgImgMatch[1];
                    if (!isValidImageUrl(variantImgUrl)) {
                        // Mark invalid variant dots
                        dot.style.opacity = '0.5';
                        dot.title = 'Variant image not available';
                        dot.style.cursor = 'not-allowed';
                        // Remove the data-has-image attribute to prevent hover
                        dot.dataset.hasImage = 'false';
                    }
                }
            } else {
                // For variants without images, set appropriate styling but allow hover to show placeholder
                dot.style.cursor = 'pointer';
                dot.title = dot.dataset.variantName || 'Color variant (hover to see placeholder)';
            }
        });
    });
};

// Keyword expansion functionality
window.enableKeywordExpansion = function enableKeywordExpansion() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('.keyword-expand-trigger')) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            const componentId = e.target.dataset.componentId;
            const keywordsContainer = e.target.parentElement;
            const allKeywordsContainer = document.getElementById(`all-keywords-${componentId}`);
            
            if (!allKeywordsContainer) {
                console.warn('All keywords container not found for component:', componentId);
                return;
            }
            
            // Store original content if not already stored
            if (!keywordsContainer.dataset.originalContent) {
                keywordsContainer.dataset.originalContent = keywordsContainer.innerHTML;
            }
            
            // Expand: show all keywords
            keywordsContainer.innerHTML = allKeywordsContainer.innerHTML + 
                `<span class="keyword-tag keyword-collapse-trigger" 
                       data-component-id="${componentId}"
                       style="cursor: pointer; background-color: #ef4444; color: white; margin-left: 0.25rem; font-size: 0.75rem;">
                    <i data-lucide="chevron-up" style="width: 10px; height: 10px; display: inline-block; margin-right: 2px;"></i>
                    Collapse
                </span>`;
            
            // Reinitialize Lucide icons for the new collapse button
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
                
        } else if (e.target.matches('.keyword-collapse-trigger')) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Collapse: restore original view
            const keywordsContainer = e.target.parentElement;
            
            if (keywordsContainer.dataset.originalContent) {
                keywordsContainer.innerHTML = keywordsContainer.dataset.originalContent;
                
                // Reinitialize Lucide icons for the restored content
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
    }, true); // Use capture phase to ensure our handler runs first
};