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
        if (window.APP_INFO && window.APP_INFO.environment === 'development') {
            console.log('[DEBUG] Setting placeholder for:', variantName, mainImg);
        }
        // Create a more visually appealing SVG placeholder
        const placeholderSvg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="140" viewBox="0 0 200 140">
                <defs>
                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#f8f9fa;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#e9ecef;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="200" height="140" fill="url(#grad1)" stroke="#dee2e6" stroke-width="2"/>
                <g transform="translate(100, 45)">
                    <!-- Camera icon -->
                    <rect x="-12" y="-8" width="24" height="16" rx="2" fill="#adb5bd" opacity="0.3"/>
                    <circle cx="0" cy="-2" r="3" fill="#adb5bd" opacity="0.5"/>
                    <rect x="-8" y="2" width="16" height="10" rx="1" fill="#adb5bd" opacity="0.3"/>
                    <circle cx="0" cy="7" r="2" fill="#adb5bd" opacity="0.4"/>
                </g>
                <text x="100" y="85" text-anchor="middle" fill="#6c757d" font-family="Arial, sans-serif" font-size="12" font-weight="500">
                    No Image Available
                </text>
                <text x="100" y="100" text-anchor="middle" fill="#adb5bd" font-family="Arial, sans-serif" font-size="10">
                    ${variantName}
                </text>
                <text x="100" y="115" text-anchor="middle" fill="#ced4da" font-family="Arial, sans-serif" font-size="8">
                    Hover to preview
                </text>
            </svg>
        `;
        
        const encodedSvg = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(placeholderSvg)));
        mainImg.src = encodedSvg;
        mainImg.style.transition = 'opacity 0.3s ease';
        mainImg.style.opacity = '1';
        
        // Add a subtle border to indicate it's a placeholder
        mainImg.style.border = '2px dashed #dee2e6';
        mainImg.style.borderRadius = '8px';
    }

    // Use a more universal approach that works with dynamic content
    document.addEventListener('mouseenter', function(e) {
        if (window.APP_INFO && window.APP_INFO.environment === 'development') {
            console.log('[DEBUG] mouseenter event:', e.target);
        }
        if (e.target.matches('.variant-color-dot[data-has-image="true"]')) {
            const dot = e.target;
            const card = dot.closest('.component-card');
            if (!card) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] No card found for dot:', dot);
                }
                return;
            }
            const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
            if (!mainImg) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] No mainImg found in card:', card);
                }
                return;
            }
            const bgImgMatch = dot.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/);
            if (!bgImgMatch || !bgImgMatch[1]) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] No valid background image URL found for dot:', dot);
                }
                return;
            }
            const variantImgUrl = bgImgMatch[1];
            if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                console.log('[DEBUG] Variant image URL:', variantImgUrl);
            }
            if (!isValidImageUrl(variantImgUrl)) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] Invalid variant image URL:', variantImgUrl);
                }
                return;
            }
            if (!mainImg.dataset.originalSrc) {
                mainImg.dataset.originalSrc = mainImg.src;
            }
            if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                console.log('[DEBUG] Setting mainImg.src to variantImgUrl:', variantImgUrl);
            }
            const testImg = new Image();
            testImg.onload = function() {
                mainImg.src = variantImgUrl;
                mainImg.style.transition = 'opacity 0.3s ease';
                mainImg.style.opacity = '1';
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.log('[DEBUG] Variant image loaded successfully:', variantImgUrl);
                }
            };
            testImg.onerror = function() {
                // Show the placeholder if the image fails to load (404, etc)
                showNoImagePlaceholder(mainImg, dot.dataset.variantName || 'Variant');
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.error('[DEBUG] Failed to load variant image (404 or error):', variantImgUrl, 'Showing placeholder.');
                }
            };
            testImg.src = variantImgUrl;
        }
        else if (e.target.matches('.variant-color-dot[data-has-image="false"]')) {
            const dot = e.target;
            const card = dot.closest('.component-card');
            if (!card) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] No card found for dot:', dot);
                }
                return;
            }
            const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
            if (!mainImg) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.warn('[DEBUG] No mainImg found in card:', card);
                }
                return;
            }
            if (!mainImg.dataset.originalSrc) {
                mainImg.dataset.originalSrc = mainImg.src;
            }
            if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                console.log('[DEBUG] No image variant hovered:', dot, 'Main image:', mainImg);
            }
            try {
                showNoImagePlaceholder(mainImg, dot.dataset.variantName || 'Variant');
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.log('[DEBUG] Called showNoImagePlaceholder for:', dot.dataset.variantName || 'Variant');
                }
            } catch (err) {
                if (window.APP_INFO && window.APP_INFO.environment === 'development') {
                    console.error('[DEBUG] Error in showNoImagePlaceholder:', err);
                }
            }
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
                
                // Clear any opacity effects and placeholder styling
                mainImg.style.opacity = '1';
                mainImg.style.border = '';
                mainImg.style.borderRadius = '';
                
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
                mainImg.style.border = '';
                mainImg.style.borderRadius = '';
            }
        }
    }, true);
    
    // Also handle initial load for existing cards
    document.querySelectorAll('.component-card').forEach(card => {
        const mainImg = card.querySelector('.card-img-top') || card.querySelector('.component-image');
        if (!mainImg) return;
        
        // Skip adding onerror handler if template already has one
        if (!mainImg.hasAttribute('onerror')) {
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
        }
        
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