/**
 * Component Variants Management Module
 * Handles all variant-related functionality including:
 * - Adding new variants
 * - Removing variants
 * - Color selection and custom colors
 * - Picture management for variants
 * - SKU generation
 */

class VariantManager {
    constructor() {
        this.variantCount = 0;
        this.uploadedImages = [];
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        // Initialize variant count from existing variants
        const existingVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        this.variantCount = existingVariants.length;
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('VariantManager initialized with', this.variantCount, 'existing variants');
    }
    
    setupEventListeners() {
        // Add variant button
        const addVariantBtn = document.getElementById('add_variant_btn');
        if (addVariantBtn) {
            addVariantBtn.addEventListener('click', () => this.addNewVariant());
        }
        
        // Set up drag and drop handlers for existing variants
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('dragleave', this.handleDragLeave.bind(this));
    }
    
    addNewVariant() {
        console.log('Adding new variant...');
        
        const emptyState = document.getElementById('empty_variants');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        this.variantCount++;
        const variantId = `new_${this.variantCount}`;
        const container = document.getElementById('variants_container');
        
        if (!container) {
            console.error('Variants container not found');
            return;
        }
        
        const variantCard = this.createVariantCard(variantId);
        container.appendChild(variantCard);
        
        // Update submit button state if function exists
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
        
        console.log(`Created new variant: ${variantId}`);
    }
    
    createVariantCard(variantId) {
        const variantCard = document.createElement('div');
        variantCard.className = 'variant-card';
        variantCard.dataset.variantId = variantId;
        
        variantCard.innerHTML = `
            <div class="variant-header">
                <h4 class="variant-title">New Variant - No SKU</h4>
                <div class="variant-actions">
                    <button type="button" class="btn-icon btn-icon-outline" onclick="variantManager.toggleVariantPictures('${variantId}')" title="Manage Pictures">
                        <svg style="width: 16px; height: 16px;" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                            <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                        </svg>
                    </button>
                    <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removeVariant('${variantId}')" title="Remove Variant">×</button>
                </div>
            </div>
            
            <div class="variant-form">
                <div class="form-grid form-grid-cols-2">
                    <div class="form-group">
                        <label class="form-label required">Color</label>
                        <select name="variant_color_${variantId}" id="color_select_${variantId}" class="form-select" required onchange="variantManager.handleColorSelection('${variantId}')">
                            ${this.getAvailableColorOptions()}
                        </select>
                        <div id="custom_color_input_${variantId}" style="display: none;" class="mt-2">
                            <input type="text" 
                                   name="variant_custom_color_${variantId}" 
                                   id="custom_color_${variantId}"
                                   class="form-input" 
                                   placeholder="Enter new color name..."
                                   onchange="variantManager.updateVariantSKU('${variantId}')">
                            <small class="form-help">This will create a new color in the system</small>
                        </div>
                        <div class="form-help">Select a color for this variant</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Variant SKU</label>
                        <input 
                            type="text" 
                            name="variant_sku_${variantId}" 
                            id="variant_sku_${variantId}"
                            class="form-input"
                            readonly
                            style="background: var(--gray-50);"
                            placeholder="SKU will be generated">
                        <div class="form-help">
                            <span id="sku_help_${variantId}">SKU will be generated after color selection</span>
                        </div>
                    </div>
                </div>
                
                <!-- Picture Miniatures -->
                <div class="form-group">
                    <div class="pictures-section-header">
                        <label class="form-label">Pictures (0)</label>
                        <button type="button" class="btn btn-outline btn-sm" onclick="variantManager.addVariantPicture('${variantId}')">
                            <svg style="width: 14px; height: 14px;" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                            </svg>
                            Add Pictures
                        </button>
                    </div>
                    
                    <div class="variant-pictures-miniatures" id="miniatures_${variantId}">
                        <div class="no-pictures" onclick="variantManager.addVariantPicture('${variantId}')">
                            <svg width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                                <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                            </svg>
                            <p>Click to add pictures</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Collapsible Pictures Section -->
            <div class="variant-pictures" id="pictures_section_${variantId}" style="display: none;">
                <div class="pictures-header">
                    <h5>Manage Pictures</h5>
                    <button type="button" class="btn btn-outline btn-sm" onclick="variantManager.toggleVariantPictures('${variantId}')">
                        <svg style="width: 14px; height: 14px;" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
                        </svg>
                        Close
                    </button>
                </div>
                
                <div class="image-upload-area">
                    <div class="upload-drop-zone" 
                         ondrop="variantManager.handleVariantDrop(event, '${variantId}')" 
                         ondragover="variantManager.handleDragOver(event)" 
                         ondragleave="variantManager.handleDragLeave(event)"
                         onclick="document.getElementById('variant_images_${variantId}').click()">
                        <svg class="upload-icon" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                            <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
                        </svg>
                        <p><strong>Click to upload</strong> or drag and drop</p>
                        <p class="upload-formats">PNG, JPG, JPEG, WEBP up to 16MB</p>
                    </div>
                    <input 
                        type="file" 
                        id="variant_images_${variantId}" 
                        name="variant_images_${variantId}[]" 
                        multiple 
                        accept="image/*" 
                        style="display: none;"
                        onchange="variantManager.handleVariantImages('${variantId}', this.files)">
                </div>

                <div class="variant-pictures-grid" id="pictures_grid_${variantId}">
                    <!-- Pictures will be added here -->
                </div>
            </div>
        `;
        
        return variantCard;
    }
    
    getAvailableColorOptions() {
        // Get all colors that are already taken by existing variants
        const takenColors = new Set();
        const existingVariants = document.querySelectorAll('[data-variant-id]');
        
        existingVariants.forEach(variant => {
            const colorSelect = variant.querySelector('[name*="variant_color_"]');
            if (colorSelect && colorSelect.value && colorSelect.value !== 'custom') {
                takenColors.add(colorSelect.value);
            }
        });
        
        // Build options HTML - will be populated from template data
        let optionsHtml = '<option value="">Select a color...</option>';
        
        // Get colors from global template data if available
        if (window.availableColors) {
            window.availableColors.forEach(color => {
                const isTaken = takenColors.has(color.id.toString());
                if (isTaken) {
                    optionsHtml += `<option value="${color.id}" disabled style="color: #999; background-color: #f5f5f5;">${color.name} (Already used)</option>`;
                } else {
                    optionsHtml += `<option value="${color.id}">${color.name}</option>`;
                }
            });
        }
        
        optionsHtml += '<option value="custom">+ Add New Color</option>';
        
        return optionsHtml;
    }
    
    removeVariant(variantId) {
        const variantCard = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (!variantCard) return;
        
        if (confirm('Are you sure you want to remove this variant?')) {
            variantCard.remove();
            
            // Show empty state if no variants left
            const remainingVariants = document.querySelectorAll('[data-variant-id]');
            if (remainingVariants.length === 0) {
                const emptyState = document.getElementById('empty_variants');
                if (emptyState) {
                    emptyState.style.display = 'block';
                }
            }
            
            // Update submit button state if function exists
            if (typeof updateSubmitButtonState === 'function') {
                updateSubmitButtonState();
            }
            
            console.log(`Removed variant: ${variantId}`);
        }
    }
    
    toggleVariantPictures(variantId) {
        const picturesSection = document.getElementById(`pictures_section_${variantId}`);
        if (picturesSection) {
            const isVisible = picturesSection.style.display !== 'none';
            picturesSection.style.display = isVisible ? 'none' : 'block';
        }
    }
    
    handleColorSelection(variantId) {
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customColorInput = document.getElementById(`custom_color_input_${variantId}`);
        
        if (!colorSelect) return;
        
        if (colorSelect.value === 'custom') {
            customColorInput.style.display = 'block';
            customColorInput.querySelector('input').focus();
        } else {
            customColorInput.style.display = 'none';
        }
        
        this.updateVariantSKU(variantId);
        this.updateVariantTitle(variantId);
        
        // Check for duplicate colors
        if (colorSelect.value && colorSelect.value !== 'custom') {
            if (this.isDuplicateColor(variantId, colorSelect.value)) {
                alert('This color is already used by another variant. Please select a different color.');
                colorSelect.value = '';
                return;
            }
        }
    }
    
    isDuplicateColor(currentVariantId, colorId) {
        const variants = document.querySelectorAll('[data-variant-id]');
        for (let variant of variants) {
            if (variant.dataset.variantId === currentVariantId) continue;
            
            const colorSelect = variant.querySelector('[name*="variant_color_"]');
            if (colorSelect && colorSelect.value === colorId) {
                return true;
            }
        }
        return false;
    }
    
    updateVariantSKU(variantId) {
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customColorInput = document.getElementById(`custom_color_${variantId}`);
        const skuInput = document.getElementById(`variant_sku_${variantId}`);
        const skuHelp = document.getElementById(`sku_help_${variantId}`);
        
        if (!colorSelect || !skuInput) return;
        
        let colorName = '';
        if (colorSelect.value === 'custom' && customColorInput) {
            colorName = customColorInput.value || 'custom';
        } else if (colorSelect.value) {
            colorName = colorSelect.selectedOptions[0]?.textContent || 'unknown';
        }
        
        if (colorName) {
            // Get product number for SKU generation
            const productNumber = document.getElementById('product_number')?.value || 'PRODUCT';
            const supplierCode = document.getElementById('supplier_id')?.selectedOptions[0]?.textContent || '';
            
            // Generate preview SKU
            const normalizedProduct = productNumber.toLowerCase().replace(/\s+/g, '_');
            const normalizedColor = colorName.toLowerCase().replace(/\s+/g, '_');
            
            let previewSKU;
            if (supplierCode && supplierCode !== 'Select supplier...') {
                previewSKU = `${supplierCode}_${normalizedProduct}_${normalizedColor}`;
            } else {
                previewSKU = `${normalizedProduct}_${normalizedColor}`;
            }
            
            skuInput.value = previewSKU;
            skuHelp.textContent = 'Preview SKU (will be finalized when saved)';
        } else {
            skuInput.value = '';
            skuHelp.textContent = 'SKU will be generated after color selection';
        }
    }
    
    updateVariantTitle(variantId) {
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customColorInput = document.getElementById(`custom_color_${variantId}`);
        const titleElement = document.querySelector(`[data-variant-id="${variantId}"] .variant-title`);
        
        if (!titleElement) return;
        
        let colorName = 'New Variant';
        if (colorSelect?.value === 'custom' && customColorInput?.value) {
            colorName = customColorInput.value;
        } else if (colorSelect?.value) {
            colorName = colorSelect.selectedOptions[0]?.textContent || 'Unknown Color';
        }
        
        const skuInput = document.getElementById(`variant_sku_${variantId}`);
        const sku = skuInput?.value || 'No SKU';
        
        titleElement.textContent = `${colorName} - ${sku}`;
    }
    
    addVariantPicture(variantId) {
        const fileInput = document.getElementById(`variant_images_${variantId}`);
        if (fileInput) {
            fileInput.click();
        }
    }
    
    handleVariantImages(variantId, files) {
        console.log(`Processing ${files.length} images for variant ${variantId}`);
        
        // Store files for form submission
        if (!this.variantFiles) {
            this.variantFiles = new Map();
        }
        
        // Get or create file list for this variant
        if (!this.variantFiles.has(variantId)) {
            this.variantFiles.set(variantId, []);
        }
        
        Array.from(files).forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                // Add file to submission list
                this.variantFiles.get(variantId).push(file);
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    const imageId = `new_${Date.now()}_${index}`;
                    const imageData = {
                        id: imageId,
                        file: file,
                        name: file.name,
                        url: e.target.result,
                        variantId: variantId,
                        isNew: true
                    };
                    
                    this.addVariantPictureToGrid(variantId, imageData);
                    this.updateVariantMiniatures(variantId);
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Update the form to include these files
        this.updateFormFiles();
    }
    
    addVariantPictureToGrid(variantId, picture) {
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        const pictureDiv = document.createElement('div');
        pictureDiv.className = 'picture-item';
        pictureDiv.dataset.pictureId = picture.id;
        
        pictureDiv.innerHTML = `
            <img src="${picture.url}" alt="${picture.name}" onclick="variantManager.previewPicture('${picture.url}', '${picture.name}', '${picture.id}')">
            <div class="picture-overlay">
                <button type="button" class="btn-icon btn-icon-primary" onclick="variantManager.setPrimaryVariantPicture('${variantId}', '${picture.id}')">★</button>
                <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removeVariantPicture('${variantId}', '${picture.id}')">×</button>
            </div>
            <div class="picture-info">
                <input type="text" 
                       name="picture_alt_${picture.id}" 
                       value="${picture.alt_text || ''}" 
                       placeholder="Alt text..." 
                       class="picture-alt-input">
                <small>New image</small>
            </div>
            ${picture.isNew ? `<input type="hidden" name="new_variant_images_${variantId}[]" value="${picture.id}">` : ''}
        `;
        
        grid.appendChild(pictureDiv);
    }
    
    updateVariantMiniatures(variantId) {
        const miniatures = document.getElementById(`miniatures_${variantId}`);
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        
        if (!miniatures || !grid) return;
        
        const pictures = grid.querySelectorAll('.picture-item');
        const pictureCount = pictures.length;
        
        // Update picture count in header
        const label = document.querySelector(`[data-variant-id="${variantId}"] .pictures-section-header .form-label`);
        if (label) {
            label.textContent = `Pictures (${pictureCount})`;
        }
        
        if (pictureCount === 0) {
            miniatures.innerHTML = `
                <div class="no-pictures" onclick="variantManager.addVariantPicture('${variantId}')">
                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                        <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                    </svg>
                    <p>Click to add pictures</p>
                </div>
            `;
        } else {
            const firstFew = Array.from(pictures).slice(0, 4);
            const miniatureHTML = firstFew.map(pic => {
                const img = pic.querySelector('img');
                const isPrimary = pic.querySelector('.primary-badge');
                return `
                    <div class="miniature-item ${isPrimary ? 'primary' : ''}" onclick="variantManager.toggleVariantPictures('${variantId}')">
                        <img src="${img.src}" alt="Miniature">
                        ${isPrimary ? '<span class="mini-primary">★</span>' : ''}
                    </div>
                `;
            }).join('');
            
            miniatures.innerHTML = miniatureHTML + (pictureCount > 4 ? `<div class="more-pictures">+${pictureCount - 4}</div>` : '');
        }
    }
    
    removeVariantPicture(variantId, pictureId) {
        const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
        if (pictureItem && confirm('Remove this picture?')) {
            pictureItem.remove();
            this.updateVariantMiniatures(variantId);
            
            // Also remove from stored files if it's a new upload
            if (this.variantFiles && this.variantFiles.has(variantId)) {
                const files = this.variantFiles.get(variantId);
                // Find and remove the file by matching some identifier
                // For now, we'll just update the form
                this.updateFormFiles();
            }
            
            // Update submit button state if function exists
            if (typeof updateSubmitButtonState === 'function') {
                updateSubmitButtonState();
            }
        }
    }
    
    updateFormFiles() {
        // Update hidden file inputs for form submission
        if (!this.variantFiles) return;
        
        this.variantFiles.forEach((files, variantId) => {
            const fileInput = document.getElementById(`variant_images_${variantId}`);
            if (fileInput && files.length > 0) {
                // Create a new DataTransfer object to set files
                const dt = new DataTransfer();
                files.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            }
        });
    }
    
    setPrimaryVariantPicture(variantId, pictureId) {
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        // Remove primary status from all pictures
        grid.querySelectorAll('.primary-badge').forEach(badge => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn-icon btn-icon-primary';
            btn.onclick = () => this.setPrimaryVariantPicture(variantId, badge.closest('.picture-item').dataset.pictureId);
            btn.innerHTML = '★';
            badge.parentNode.replaceChild(btn, badge);
        });
        
        // Set new primary
        const newPrimary = grid.querySelector(`[data-picture-id="${pictureId}"] .btn-icon-primary`);
        if (newPrimary) {
            const badge = document.createElement('span');
            badge.className = 'primary-badge';
            badge.textContent = 'Primary';
            newPrimary.parentNode.replaceChild(badge, newPrimary);
        }
        
        this.updateVariantMiniatures(variantId);
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }
    
    handleVariantDrop(e, variantId) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        const files = e.dataTransfer.files;
        this.handleVariantImages(variantId, files);
    }
    
    previewPicture(imageUrl, imageName, pictureId) {
        // Delegate to global preview function if it exists
        if (typeof window.previewPicture === 'function') {
            window.previewPicture(imageUrl, imageName, pictureId);
        } else {
            // Simple fallback
            window.open(imageUrl, '_blank');
        }
    }
    
    validateVariantBeforeSubmit(variantId) {
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customColorInput = document.getElementById(`custom_color_${variantId}`);
        const picturesGrid = document.getElementById(`pictures_grid_${variantId}`);
        
        // Check if color is selected
        if (!colorSelect?.value) {
            alert(`Please select a color for the variant.`);
            return false;
        }
        
        // Check custom color name if custom is selected
        if (colorSelect.value === 'custom' && (!customColorInput?.value || !customColorInput.value.trim())) {
            alert(`Please enter a name for the custom color.`);
            customColorInput?.focus();
            return false;
        }
        
        // Check if at least one picture is added
        const pictures = picturesGrid?.querySelectorAll('.picture-item') || [];
        if (pictures.length === 0) {
            alert(`Please add at least one picture for the variant.`);
            return false;
        }
        
        return true;
    }
}

// Initialize variant manager when DOM is ready
let variantManager = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        variantManager = new VariantManager();
    });
} else {
    variantManager = new VariantManager();
}

// Export for global access
window.variantManager = variantManager;