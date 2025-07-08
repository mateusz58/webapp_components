/**
 * Component Variants Management Module
 * Handles all variant-related functionality using API endpoints:
 * - Adding new variants via API
 * - Removing variants via API
 * - Color selection and custom colors
 * - Picture management for variants via API
 * - SKU generation via database triggers
 * - Proper error handling and user feedback
 */

class VariantManager {
    constructor() {
        this.variantCount = 0;
        this.pendingVariants = new Map(); // Store new variants before creation
        this.stagedChanges = new Map(); // Store staged picture changes for existing variants
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
        
        // Get component ID for API calls
        this.componentId = window.componentId || null;
        
        // Setup CSRF token for API calls
        this.csrfToken = document.querySelector('[name="csrf_token"]')?.value;
        
        // In edit mode, load full component data via API to populate pictures
        if (window.isEditMode && this.componentId) {
            this.loadComponentEditData();
        }
        
        console.log('🔧 VariantManager initialized with', this.variantCount, 'existing variants', 'Component ID:', this.componentId);
        console.log('🔧 CSRF Token:', this.csrfToken ? 'Present' : 'Missing');
        console.log('🔧 Add variant button:', document.getElementById('add_variant_btn') ? 'Found' : 'Not found');
    }
    
    setupEventListeners() {
        // Add variant button
        const addVariantBtn = document.getElementById('add_variant_btn');
        if (addVariantBtn) {
            addVariantBtn.addEventListener('click', () => this.addNewVariant());
        }
        
        // Set up drag and drop handlers for existing variants
        this.setupDragAndDrop();
        
        // Monitor component-level field changes that affect SKUs and picture names
        this.setupComponentFieldMonitoring();
    }
    
    setupDragAndDrop() {
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('dragleave', this.handleDragLeave.bind(this));
    }
    
    setupComponentFieldMonitoring() {
        console.log('🔧 DEBUG: Setting up component field monitoring for SKU and picture name updates');
        
        // Monitor product number changes
        const productNumberInput = document.getElementById('product_number') || document.querySelector('input[name="product_number"]');
        if (productNumberInput) {
            console.log('🔧 DEBUG: Product number input found, adding listener');
            productNumberInput.addEventListener('input', (event) => {
                const oldValue = event.target.defaultValue || '';
                const newValue = event.target.value || '';
                console.log(`🔧 DEBUG: Product number changed from "${oldValue}" to "${newValue}"`);
                console.log('🔧 DEBUG: Triggering SKU and picture name updates for all variants');
                this.updateAllVariantSKUs();
                this.updateAllVariantPictureNames('product_number');
            });
        } else {
            console.warn('🔧 DEBUG: Product number input not found');
        }
        
        // Monitor supplier changes
        const supplierSelect = document.getElementById('supplier_id') || document.querySelector('select[name="supplier_id"]');
        if (supplierSelect) {
            console.log('🔧 DEBUG: Supplier select found, adding listener');
            supplierSelect.addEventListener('change', (event) => {
                const oldValue = event.target.defaultValue || '';
                const newValue = event.target.value || '';
                const selectedOption = event.target.selectedOptions[0];
                const supplierText = selectedOption ? selectedOption.textContent : 'None';
                console.log(`🔧 DEBUG: Supplier changed from "${oldValue}" to "${newValue}" (${supplierText})`);
                console.log('🔧 DEBUG: Triggering SKU and picture name updates for all variants');
                this.updateAllVariantSKUs();
                this.updateAllVariantPictureNames('supplier');
            });
        } else {
            console.warn('🔧 DEBUG: Supplier select not found');
        }
        
        console.log('🔧 DEBUG: Component field monitoring setup complete');
    }
    
    addNewVariant() {
        console.log('🔥 addNewVariant() called - User clicked Add Variant button');
        
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
        
        // Store as pending variant
        this.pendingVariants.set(variantId, {
            isNew: true,
            colorId: null,
            customColorName: null,
            pictures: []
        });
        
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
                                   onchange="variantManager.updateCustomColorName('${variantId}')"
                                   oninput="variantManager.updateCustomColorName('${variantId}')"
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
    
    async removeVariant(variantId) {
        const variantCard = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (!variantCard) return;
        
        if (!confirm('Are you sure you want to remove this variant?')) {
            return;
        }
        
        try {
            // Check if it's a new variant (not yet saved) or existing variant
            if (variantId.startsWith('new_')) {
                // Remove from pending variants
                this.pendingVariants.delete(variantId);
                variantCard.remove();
                this.showSuccessMessage('Variant removed (will be saved on form submission)');
            } else {
                // For existing variants, just mark for deletion instead of immediate API call
                this.stageVariantForDeletion(variantId);
                variantCard.style.opacity = '0.5';
                variantCard.style.filter = 'grayscale(100%)';
                
                // Add undo button to variant header
                const variantHeader = variantCard.querySelector('.variant-header');
                if (variantHeader && !variantHeader.querySelector('.undo-deletion')) {
                    const undoBtn = document.createElement('button');
                    undoBtn.type = 'button';
                    undoBtn.className = 'btn btn-sm btn-warning undo-deletion';
                    undoBtn.innerHTML = '↶ Undo Deletion';
                    undoBtn.onclick = () => this.undoVariantDeletion(variantId);
                    variantHeader.appendChild(undoBtn);
                }
                
                this.showSuccessMessage('Variant marked for deletion (will be saved on form submission)');
            }
            
            // Show empty state if no variants left
            const remainingVariants = document.querySelectorAll('[data-variant-id]:not([style*="display: none"])');
            if (remainingVariants.length === 0) {
                const emptyState = document.getElementById('empty_variants');
                if (emptyState) {
                    emptyState.style.display = 'block';
                }
            }
            
            // Update submit button state
            if (typeof updateSubmitButtonState === 'function') {
                updateSubmitButtonState();
            }
            
            console.log(`Staged variant for deletion: ${variantId}`);
            
        } catch (error) {
            console.error('Error staging variant for removal:', error);
            this.showErrorMessage(`Failed to stage variant for removal: ${error.message}`);
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
        
        // Update pending variant data
        if (variantId.startsWith('new_')) {
            if (!this.pendingVariants.has(variantId)) {
                this.pendingVariants.set(variantId, {
                    isNew: true,
                    colorId: null,
                    customColorName: null,
                    pictures: []
                });
            }
            
            const variant = this.pendingVariants.get(variantId);
            if (colorSelect.value === 'custom') {
                variant.colorId = null;
                // Get custom color name when available
                const customInput = customColorInput.querySelector('input');
                variant.customColorName = customInput ? customInput.value : '';
            } else {
                variant.colorId = parseInt(colorSelect.value) || null;
                variant.customColorName = null;
            }
        }
        
        this.updateVariantSKU(variantId);
        this.updateVariantTitle(variantId);
        this.updateVariantValidationStatus(variantId);
        this.updateOverallValidationStatus();
        
        // Update picture names for color change
        this.updatePictureNamesForVariantChange(variantId, 'color');
        
        // Update submit button state if function exists
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
        
        // Check for duplicate colors
        if (colorSelect.value && colorSelect.value !== 'custom') {
            if (this.isDuplicateColor(variantId, colorSelect.value)) {
                alert('This color is already used by another variant. Please select a different color.');
                colorSelect.value = '';
                return;
            }
        }
    }
    
    updateCustomColorName(variantId) {
        // Update pending variant data when custom color name changes
        if (variantId.startsWith('new_') && this.pendingVariants.has(variantId)) {
            const variant = this.pendingVariants.get(variantId);
            const customInput = document.getElementById(`custom_color_${variantId}`);
            if (customInput) {
                variant.customColorName = customInput.value.trim();
            }
        }
        
        // Update SKU and validation
        this.updateVariantSKU(variantId);
        this.updateVariantTitle(variantId);
        this.updateVariantValidationStatus(variantId);
        this.updateOverallValidationStatus();
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
            // Get clean color name from the option text
            const selectedOption = colorSelect.selectedOptions[0];
            if (selectedOption) {
                colorName = selectedOption.textContent.trim();
                // Clean up any extra formatting from the color name
                colorName = colorName.replace(/\s*\(.*\)/, '').trim(); // Remove "(Current)" or similar
            }
        }
        
        if (colorName) {
            // Get product number for SKU generation
            const productNumber = document.getElementById('product_number')?.value || 'PRODUCT';
            
            // Get supplier code properly - first try to get from data attribute, then from API call if needed
            let supplierCode = '';
            const supplierSelect = document.getElementById('supplier_id');
            if (supplierSelect && supplierSelect.value) {
                // Look for the supplier code in the option's data attribute or text
                const selectedOption = supplierSelect.selectedOptions[0];
                if (selectedOption) {
                    // Try to extract supplier code from the option text (format: "CODE - Name" or just "CODE")
                    const optionText = selectedOption.textContent.trim();
                    if (optionText && optionText !== 'Select supplier...') {
                        // Extract code part before any " - " separator
                        supplierCode = optionText.split(' - ')[0].trim();
                    }
                }
            }
            
            // Generate preview SKU with proper formatting
            const normalizedProduct = productNumber.toLowerCase().replace(/\s+/g, '_');
            const normalizedColor = colorName.toLowerCase().replace(/\s+/g, '_');
            const normalizedSupplier = supplierCode.toUpperCase().replace(/\s+/g, '');
            
            let previewSKU;
            if (normalizedSupplier && normalizedSupplier !== 'SELECT') {
                previewSKU = `${normalizedSupplier}_${normalizedProduct}_${normalizedColor}`.replace(/_+/g, '_');
            } else {
                previewSKU = `${normalizedProduct}_${normalizedColor}`;
            }
            
            skuInput.value = previewSKU;
            skuHelp.textContent = 'Preview SKU (will be finalized when saved)';
            
            console.log('🔧 Generated SKU:', previewSKU, 'from supplier:', normalizedSupplier, 'product:', normalizedProduct, 'color:', normalizedColor);
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
    
    async handleVariantImages(variantId, files) {
        if (files.length === 0) return;
        
        // Show immediate feedback
        this.showSuccessMessage(`Adding ${files.length} images...`);
        
        // Handle images based on variant type
        if (variantId.startsWith('new_')) {
            this.handleNewVariantImages(variantId, files);
        } else {
            this.handleExistingVariantImages(variantId, files);
        }
    }
    
    addPictureToGrid(variantId, picture) {
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) {
            console.error(`Pictures grid not found: pictures_grid_${variantId}`);
            return;
        }
        
        // Calculate max allowed order based on total pictures for this variant
        const allPictures = this.getAllVariantPictures(variantId);
        const maxOrder = allPictures.length;
        
        const pictureDiv = document.createElement('div');
        pictureDiv.className = 'picture-item';
        if (picture.isPending) {
            pictureDiv.classList.add('pending-upload');
        }
        if (picture.isStaged) {
            pictureDiv.classList.add('staged-picture');
        }
        pictureDiv.dataset.pictureId = picture.id;
        
        let overlayContent = '';
        if (picture.isPending) {
            overlayContent = `
                <span class="staged-badge">Pending</span>
                <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${picture.id}')">×</button>
            `;
        } else if (picture.is_primary) {
            overlayContent = `
                <span class="primary-badge">Primary</span>
                <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${picture.id}')">×</button>
            `;
        } else {
            overlayContent = `
                <button type="button" class="btn-icon btn-icon-primary" onclick="variantManager.setPrimaryPicture('${variantId}', '${picture.id}')">★</button>
                <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${picture.id}')">×</button>
            `;
        }
        
        pictureDiv.innerHTML = `
            <img src="${picture.url}" alt="${picture.alt_text || picture.name}" onclick="variantManager.previewPicture('${picture.url}', '${picture.name}', '${picture.id}')">
            <div class="picture-overlay">
                ${overlayContent}
            </div>
            <div class="picture-info">
                <div class="picture-name">${picture.picture_name || picture.name || 'New Picture'}</div>
                <div class="picture-inputs">
                    <input type="text" 
                           name="picture_alt_${picture.id}" 
                           value="${picture.alt_text || ''}" 
                           placeholder="Alt text..." 
                           class="picture-alt-input">
                    <input type="number" 
                           name="picture_order_${picture.id}" 
                           value="${picture.picture_order || 1}" 
                           min="1" 
                           max="${maxOrder}"
                           placeholder="Order..." 
                           class="picture-order-input"
                           onchange="variantManager.updatePictureOrder('${variantId}', '${picture.id}', this.value)"
                           title="Order range: 1 to ${maxOrder}">
                </div>
            </div>
        `;
        
        grid.appendChild(pictureDiv);
    }
    
    updatePictureOrder(variantId, pictureId, newOrder) {
        const targetOrder = parseInt(newOrder);
        
        // Get all pictures for this variant (existing, staged, and pending)
        const allPictures = this.getAllVariantPictures(variantId);
        
        // Validate order value
        const maxAllowedOrder = allPictures.length;
        if (isNaN(targetOrder) || targetOrder < 1) {
            this.showErrorMessage('Order must be a positive number starting from 1');
            
            // Reset the input to the current order
            const orderInput = document.querySelector(`[data-picture-id="${pictureId}"] .picture-order-input`);
            if (orderInput) {
                const currentPicture = allPictures.find(p => p.id === pictureId);
                orderInput.value = currentPicture ? currentPicture.order : 1;
            }
            return;
        }
        
        if (targetOrder > maxAllowedOrder) {
            this.showErrorMessage(`Order cannot be higher than ${maxAllowedOrder} (total number of pictures for this variant)`);
            
            // Reset the input to the current order
            const orderInput = document.querySelector(`[data-picture-id="${pictureId}"] .picture-order-input`);
            if (orderInput) {
                const currentPicture = allPictures.find(p => p.id === pictureId);
                orderInput.value = currentPicture ? currentPicture.order : 1;
            }
            return;
        }
        
        // Check for conflicts and resolve them
        const conflictResolution = this.resolveOrderConflicts(allPictures, pictureId, targetOrder);
        
        // Apply the resolved orders
        this.applyOrderChanges(variantId, conflictResolution);
        
        // Update picture names based on new orders
        const nameChanges = this.updatePictureNamesAfterOrderChange(variantId, conflictResolution.changes);
        
        // Update the UI inputs to reflect the resolved orders
        this.updateOrderInputsDisplay(variantId, conflictResolution);
        
        // Show appropriate feedback message
        if (conflictResolution.hasConflicts) {
            this.showSuccessMessage(`Order updated to ${conflictResolution.finalOrder}. Other pictures automatically reordered to prevent conflicts.`);
        } else {
            this.showSuccessMessage('Picture order updated (will be saved on form submission)');
        }
        
        // Mark component as having pending changes
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
    }
    
    getAllVariantPictures(variantId) {
        const pictures = [];
        
        // Get existing pictures from the grid
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (grid) {
            const pictureElements = grid.querySelectorAll('.picture-item:not(.marked-for-deletion)');
            pictureElements.forEach(element => {
                const pictureId = element.dataset.pictureId;
                const orderInput = element.querySelector('.picture-order-input');
                const currentOrder = orderInput ? parseInt(orderInput.value) || 1 : 1;
                
                pictures.push({
                    id: pictureId,
                    order: currentOrder,
                    element: element,
                    isExisting: !pictureId.startsWith('new_') && !pictureId.startsWith('staged_')
                });
            });
        }
        
        return pictures;
    }
    
    resolveOrderConflicts(allPictures, changingPictureId, newOrder) {
        const result = {
            changes: new Map(),
            hasConflicts: false,
            finalOrder: newOrder
        };
        
        // Find the picture being changed
        const changingPicture = allPictures.find(p => p.id === changingPictureId);
        if (!changingPicture) return result;
        
        // Check if the new order conflicts with existing pictures
        const conflictingPicture = allPictures.find(p => p.id !== changingPictureId && p.order === newOrder);
        
        if (conflictingPicture) {
            result.hasConflicts = true;
            
            // Strategy: Shift conflicting pictures up by 1
            const picturesToShift = allPictures
                .filter(p => p.id !== changingPictureId && p.order >= newOrder)
                .sort((a, b) => b.order - a.order); // Sort descending to avoid cascading conflicts
            
            // Shift each conflicting picture up by 1
            picturesToShift.forEach(picture => {
                const newShiftedOrder = picture.order + 1;
                result.changes.set(picture.id, newShiftedOrder);
            });
        }
        
        // Set the new order for the changing picture
        result.changes.set(changingPictureId, newOrder);
        
        return result;
    }
    
    applyOrderChanges(variantId, conflictResolution) {
        conflictResolution.changes.forEach((newOrder, pictureId) => {
            // Update in staged changes
            if (this.stagedChanges.has(variantId)) {
                const staged = this.stagedChanges.get(variantId);
                const stagedPicture = staged.picturesToAdd.find(p => p.id === pictureId);
                if (stagedPicture) {
                    stagedPicture.picture_order = newOrder;
                }
            }
            
            // Update in pending variants
            if (this.pendingVariants.has(variantId)) {
                const variant = this.pendingVariants.get(variantId);
                const pendingPicture = variant.pictures.find(p => p.id === pictureId);
                if (pendingPicture) {
                    pendingPicture.picture_order = newOrder;
                }
            }
            
            // For existing pictures, we'll track the changes for form submission
            // This will be handled by the form submission process
        });
    }
    
    updateOrderInputMaxValues(variantId) {
        const allPictures = this.getAllVariantPictures(variantId);
        const maxOrder = allPictures.length;
        
        // Update all order inputs for this variant
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (grid) {
            const orderInputs = grid.querySelectorAll('.picture-order-input');
            orderInputs.forEach(input => {
                input.setAttribute('max', maxOrder);
                input.setAttribute('title', `Order range: 1 to ${maxOrder}`);
            });
        }
    }
    
    updateOrderInputsDisplay(variantId, conflictResolution) {
        conflictResolution.changes.forEach((newOrder, pictureId) => {
            const grid = document.getElementById(`pictures_grid_${variantId}`);
            if (grid) {
                const pictureElement = grid.querySelector(`[data-picture-id="${pictureId}"]`);
                if (pictureElement) {
                    const orderInput = pictureElement.querySelector('.picture-order-input');
                    if (orderInput) {
                        orderInput.value = newOrder;
                        
                        // Add visual feedback for changed orders
                        if (conflictResolution.hasConflicts && pictureId !== Array.from(conflictResolution.changes.keys())[0]) {
                            orderInput.style.backgroundColor = '#fff3cd'; // Light yellow
                            orderInput.style.borderColor = '#ffc107'; // Warning color
                            
                            // Remove highlight after 2 seconds
                            setTimeout(() => {
                                orderInput.style.backgroundColor = '';
                                orderInput.style.borderColor = '';
                            }, 2000);
                        }
                    }
                }
            }
        });
    }
    
    getNextAvailableOrder(variantId) {
        const allPictures = this.getAllVariantPictures(variantId);
        if (allPictures.length === 0) return 1;
        
        const maxOrder = Math.max(...allPictures.map(p => p.order));
        return maxOrder + 1;
    }
    
    generatePictureName(variantId, pictureOrder) {
        // Get variant information to generate picture name
        const variantElement = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (!variantElement) return null;
        
        // Get color name
        const colorSelect = variantElement.querySelector(`[name*="variant_color_"]`);
        const customColorInput = variantElement.querySelector(`[name*="variant_custom_color_"]`);
        
        let colorName = '';
        if (colorSelect && colorSelect.value) {
            const selectedOption = colorSelect.querySelector(`option[value="${colorSelect.value}"]`);
            if (selectedOption && selectedOption.textContent) {
                colorName = selectedOption.textContent.trim().toLowerCase();
                // Remove "(Current)" suffix if present
                colorName = colorName.replace(/\s*\(current\)$/i, '');
            }
        } else if (customColorInput && customColorInput.value.trim()) {
            colorName = customColorInput.value.trim().toLowerCase();
        }
        
        if (!colorName) return null;
        
        // Get current component product number from form
        const productNumberInput = document.getElementById('product_number');
        let productNumber = productNumberInput ? productNumberInput.value.trim() : 'component';
        
        // Get supplier code from form
        let supplierCode = '';
        const supplierSelect = document.getElementById('supplier_id');
        if (supplierSelect && supplierSelect.value) {
            const selectedOption = supplierSelect.selectedOptions[0];
            if (selectedOption) {
                const optionText = selectedOption.textContent.trim();
                if (optionText && optionText !== 'Select supplier...') {
                    supplierCode = optionText.split(' - ')[0].trim();
                }
            }
        }
        
        // Normalize strings: replace spaces with underscores, make lowercase
        colorName = colorName.replace(/\s+/g, '_').toLowerCase();
        productNumber = productNumber.replace(/\s+/g, '_').toLowerCase();
        const normalizedSupplier = supplierCode.replace(/\s+/g, '').toLowerCase();
        
        // Generate picture name following the same pattern as SKU but lowercase
        if (normalizedSupplier) {
            return `${normalizedSupplier}_${productNumber}_${colorName}_${pictureOrder}`;
        } else {
            return `${productNumber}_${colorName}_${pictureOrder}`;
        }
    }
    
    updatePictureNamesAfterOrderChange(variantId, orderChanges) {
        // Track picture name changes for WebDAV file renaming
        const nameChanges = new Map(); // oldName -> newName
        
        console.log('🔧 Processing order changes for variant', variantId, orderChanges);
        
        orderChanges.forEach((newOrder, pictureId) => {
            const newPictureName = this.generatePictureName(variantId, newOrder);
            if (!newPictureName) return;
            
            console.log('🔧 Picture', pictureId, 'new order:', newOrder, 'new name:', newPictureName);
            
            // For existing pictures (real database pictures), we need to get the current name
            if (!pictureId.startsWith('new_') && !pictureId.startsWith('staged_')) {
                // Get current picture name from DOM element
                const grid = document.getElementById(`pictures_grid_${variantId}`);
                if (grid) {
                    const pictureElement = grid.querySelector(`[data-picture-id="${pictureId}"]`);
                    if (pictureElement) {
                        const nameElement = pictureElement.querySelector('.picture-name');
                        if (nameElement) {
                            const currentDisplayedName = nameElement.textContent.trim();
                            console.log('🔧 Current displayed name:', currentDisplayedName, 'New name:', newPictureName);
                            
                            // Only add to rename map if names are actually different
                            if (currentDisplayedName && currentDisplayedName !== newPictureName) {
                                nameChanges.set(currentDisplayedName, newPictureName);
                                console.log('🔧 Added rename mapping:', currentDisplayedName, '→', newPictureName);
                            }
                            
                            // Update the display
                            nameElement.textContent = newPictureName;
                        }
                    }
                }
            }
            
            // Update staged pictures
            if (this.stagedChanges.has(variantId)) {
                const staged = this.stagedChanges.get(variantId);
                const stagedPicture = staged.picturesToAdd.find(p => p.id === pictureId);
                if (stagedPicture) {
                    const oldName = stagedPicture.picture_name || stagedPicture.name;
                    stagedPicture.picture_name = newPictureName;
                    stagedPicture.name = newPictureName;
                    if (oldName && oldName !== newPictureName) {
                        nameChanges.set(oldName, newPictureName);
                        console.log('🔧 Staged picture rename:', oldName, '→', newPictureName);
                    }
                }
            }
            
            // Update pending variants
            if (this.pendingVariants.has(variantId)) {
                const variant = this.pendingVariants.get(variantId);
                const pendingPicture = variant.pictures.find(p => p.id === pictureId);
                if (pendingPicture) {
                    const oldName = pendingPicture.picture_name || pendingPicture.name;
                    pendingPicture.picture_name = newPictureName;
                    pendingPicture.name = newPictureName;
                    if (oldName && oldName !== newPictureName) {
                        nameChanges.set(oldName, newPictureName);
                        console.log('🔧 Pending picture rename:', oldName, '→', newPictureName);
                    }
                }
            }
        });
        
        // Store file rename operations for form submission
        if (nameChanges.size > 0) {
            if (!this.stagedChanges.has(variantId)) {
                this.stagedChanges.set(variantId, {
                    variantToDelete: false,
                    picturesToAdd: [],
                    picturesToDelete: []
                });
            }
            
            const staged = this.stagedChanges.get(variantId);
            if (!staged.pictureRenames) {
                staged.pictureRenames = new Map();
            }
            
            // Merge rename operations
            nameChanges.forEach((newName, oldName) => {
                staged.pictureRenames.set(oldName, newName);
            });
        }
        
        return nameChanges;
    }
    
    updatePictureNamesForVariantChange(variantId, changeType) {
        /**
         * Update picture names when variant properties change (color, supplier, product number)
         * This handles the comprehensive picture renaming scenarios you mentioned
         */
        console.log(`🔧 Updating picture names for variant ${variantId} due to ${changeType} change`);
        
        // Get all pictures for this variant
        const allPictures = this.getAllVariantPictures(variantId);
        if (allPictures.length === 0) {
            console.log('🔧 No pictures found for this variant');
            return;
        }
        
        const nameChanges = new Map(); // oldName -> newName
        
        // Process each picture
        allPictures.forEach(picture => {
            const currentOrder = picture.order;
            const newPictureName = this.generatePictureName(variantId, currentOrder);
            
            if (!newPictureName) {
                console.log(`🔧 Could not generate new name for picture ${picture.id}`);
                return;
            }
            
            // Get current name - for existing pictures, get from DOM or database
            let currentName = null;
            
            if (!picture.id.startsWith('new_') && !picture.id.startsWith('staged_')) {
                // Existing picture - get current name from DOM
                const grid = document.getElementById(`pictures_grid_${variantId}`);
                if (grid) {
                    const pictureElement = grid.querySelector(`[data-picture-id="${picture.id}"]`);
                    if (pictureElement) {
                        const nameElement = pictureElement.querySelector('.picture-name');
                        if (nameElement) {
                            currentName = nameElement.textContent.trim();
                        }
                    }
                }
            } else {
                // Staged or pending picture
                if (this.stagedChanges.has(variantId)) {
                    const staged = this.stagedChanges.get(variantId);
                    const stagedPicture = staged.picturesToAdd.find(p => p.id === picture.id);
                    if (stagedPicture) {
                        currentName = stagedPicture.picture_name || stagedPicture.name;
                    }
                }
                
                if (!currentName && this.pendingVariants.has(variantId)) {
                    const variant = this.pendingVariants.get(variantId);
                    const pendingPicture = variant.pictures.find(p => p.id === picture.id);
                    if (pendingPicture) {
                        currentName = pendingPicture.picture_name || pendingPicture.name;
                    }
                }
            }
            
            if (currentName && currentName !== newPictureName) {
                console.log(`🔧 Picture ${picture.id}: ${currentName} → ${newPictureName}`);
                nameChanges.set(currentName, newPictureName);
                
                // Update the displayed name
                const grid = document.getElementById(`pictures_grid_${variantId}`);
                if (grid) {
                    const pictureElement = grid.querySelector(`[data-picture-id="${picture.id}"]`);
                    if (pictureElement) {
                        const nameElement = pictureElement.querySelector('.picture-name');
                        if (nameElement) {
                            nameElement.textContent = newPictureName;
                        }
                    }
                }
                
                // Update staged/pending data
                if (picture.id.startsWith('staged_') && this.stagedChanges.has(variantId)) {
                    const staged = this.stagedChanges.get(variantId);
                    const stagedPicture = staged.picturesToAdd.find(p => p.id === picture.id);
                    if (stagedPicture) {
                        stagedPicture.picture_name = newPictureName;
                        stagedPicture.name = newPictureName;
                    }
                }
                
                if (picture.id.startsWith('new_') && this.pendingVariants.has(variantId)) {
                    const variant = this.pendingVariants.get(variantId);
                    const pendingPicture = variant.pictures.find(p => p.id === picture.id);
                    if (pendingPicture) {
                        pendingPicture.picture_name = newPictureName;
                        pendingPicture.name = newPictureName;
                    }
                }
            }
        });
        
        // Store rename operations for form submission if there are any changes
        if (nameChanges.size > 0) {
            if (!this.stagedChanges.has(variantId)) {
                this.stagedChanges.set(variantId, {
                    variantToDelete: false,
                    picturesToAdd: [],
                    picturesToDelete: []
                });
            }
            
            const staged = this.stagedChanges.get(variantId);
            if (!staged.pictureRenames) {
                staged.pictureRenames = new Map();
            }
            
            // Merge rename operations
            nameChanges.forEach((newName, oldName) => {
                staged.pictureRenames.set(oldName, newName);
            });
            
            console.log(`🔧 Added ${nameChanges.size} picture rename operations for ${changeType} change`);
            
            // Update max values for order inputs since names changed
            this.updateOrderInputMaxValues(variantId);
            
            // Show user feedback
            this.showSuccessMessage(`Picture names updated for ${changeType} change (will be saved on form submission)`);
        }
    }
    
    // Function to update SKUs for all variants when component-level fields change
    updateAllVariantSKUs() {
        console.log('🔧 DEBUG: Starting updateAllVariantSKUs() - updating SKUs for all variants');
        
        // Update existing variants
        const allVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        console.log(`🔧 DEBUG: Found ${allVariants.length} existing variants to update`);
        
        allVariants.forEach((variantElement, index) => {
            const variantId = variantElement.dataset.variantId;
            if (variantId) {
                console.log(`🔧 DEBUG: Updating SKU for existing variant ${index + 1}/${allVariants.length}: ${variantId}`);
                this.updateVariantSKU(variantId);
            } else {
                console.warn(`🔧 DEBUG: Variant element missing ID at index ${index}`);
            }
        });
        
        // Update pending variants
        console.log(`🔧 DEBUG: Found ${this.pendingVariants.size} pending variants to update`);
        this.pendingVariants.forEach((variant, variantId) => {
            console.log(`🔧 DEBUG: Updating SKU for pending variant: ${variantId}`);
            this.updateVariantSKU(variantId);
        });
        
        console.log('🔧 DEBUG: Completed updateAllVariantSKUs()');
    }
    
    // Function to call when component-level changes affect all variants
    updateAllVariantPictureNames(changeType) {
        console.log(`🔧 DEBUG: Starting updateAllVariantPictureNames() with changeType: ${changeType}`);
        
        // Update pictures for all existing variants
        const allVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        console.log(`🔧 DEBUG: Found ${allVariants.length} existing variants for picture name updates`);
        
        allVariants.forEach((variantElement, index) => {
            const variantId = variantElement.dataset.variantId;
            if (variantId) {
                console.log(`🔧 DEBUG: Updating pictures for existing variant ${index + 1}/${allVariants.length}: ${variantId}`);
                this.updatePictureNamesForVariantChange(variantId, changeType);
            } else {
                console.warn(`🔧 DEBUG: Variant element missing ID at index ${index}`);
            }
        });
        
        // Update pictures for all pending variants
        console.log(`🔧 DEBUG: Found ${this.pendingVariants.size} pending variants for picture updates`);
        this.pendingVariants.forEach((variant, variantId) => {
            console.log(`🔧 DEBUG: Updating pictures for pending variant: ${variantId}`);
            this.updatePictureNamesForVariantChange(variantId, changeType);
        });
        
        // Update pictures for all staged variants
        console.log(`🔧 DEBUG: Found ${this.stagedChanges.size} staged variants for picture updates`);
        this.stagedChanges.forEach((changes, variantId) => {
            console.log(`🔧 DEBUG: Updating pictures for staged variant: ${variantId}`);
            this.updatePictureNamesForVariantChange(variantId, changeType);
        });
        
        console.log(`🔧 DEBUG: Completed updateAllVariantPictureNames() for changeType: ${changeType}`);
    }
    
    getPictureOrderChanges() {
        // Collect all picture order changes for form submission
        const orderChanges = {};
        const renames = {};
        
        // Get all picture order inputs from all variants
        const allPictureInputs = document.querySelectorAll('.picture-order-input');
        allPictureInputs.forEach(input => {
            const pictureId = input.name.split('picture_order_')[1];
            if (pictureId) {
                orderChanges[`picture_order_${pictureId}`] = input.value;
            }
        });
        
        // Collect rename operations from staged changes
        this.stagedChanges.forEach((changes, variantId) => {
            if (changes.pictureRenames) {
                changes.pictureRenames.forEach((newName, oldName) => {
                    renames[oldName] = newName;
                });
            }
        });
        
        console.log('🔧 Picture order changes collected:');
        console.log('🔧 Order changes:', orderChanges);
        console.log('🔧 Rename mapping:', renames);
        
        return {
            orders: orderChanges,
            renames: renames
        };
    }
    
    updateVariantMiniatures(variantId) {
        const miniatures = document.getElementById(`miniatures_${variantId}`);
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        
        if (!miniatures) return;
        
        // Get all pictures from the grid (includes staged, pending, and existing)
        const pictures = grid ? Array.from(grid.querySelectorAll('.picture-item:not(.marked-for-deletion)')) : [];
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
            const firstFew = pictures.slice(0, 4);
            const miniatureHTML = firstFew.map(pic => {
                const img = pic.querySelector('img');
                const isPrimary = pic.querySelector('.primary-badge');
                const isPending = pic.classList.contains('pending-upload') || pic.classList.contains('staged-picture');
                
                return `
                    <div class="miniature-item ${isPrimary ? 'primary' : ''} ${isPending ? 'pending' : ''}" onclick="variantManager.toggleVariantPictures('${variantId}')">
                        <img src="${img.src}" alt="Miniature">
                        ${isPrimary ? '<span class="mini-primary">★</span>' : ''}
                        ${isPending ? '<span class="mini-pending">•</span>' : ''}
                    </div>
                `;
            }).join('');
            
            miniatures.innerHTML = miniatureHTML + (pictureCount > 4 ? `<div class="more-pictures">+${pictureCount - 4}</div>` : '');
        }
    }
    
    removePicture(variantId, pictureId) {
        if (!confirm('Remove this picture?')) {
            return;
        }
        
        try {
            // Find and remove from DOM
            const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
            if (pictureItem) {
                pictureItem.remove();
            }
            
            // Remove from appropriate data structure
            if (pictureId.toString().startsWith('new_') && this.pendingVariants.has(variantId)) {
                // Remove from pending variants (new variants)
                const variant = this.pendingVariants.get(variantId);
                variant.pictures = variant.pictures.filter(p => p.id !== pictureId);
            } else if (pictureId.toString().startsWith('staged_') && this.stagedChanges.has(variantId)) {
                // Remove from staged changes (existing variants, new files)
                const staged = this.stagedChanges.get(variantId);
                staged.picturesToAdd = staged.picturesToAdd.filter(p => p.id !== pictureId);
            } else {
                // Mark existing picture for deletion
                this.stagePictureForDeletion(variantId, pictureId);
            }
            
            // Update UI
            this.updateVariantMiniatures(variantId);
            this.updateVariantValidationStatus(variantId);
            this.updateOrderInputMaxValues(variantId);
            this.updateOverallValidationStatus();
            
            if (typeof updateSubmitButtonState === 'function') {
                updateSubmitButtonState();
            }
            
            this.showSuccessMessage('Picture removed (will be saved on form submission)');
            
        } catch (error) {
            console.error('Error removing picture:', error);
            this.showErrorMessage(`Failed to remove picture: ${error.message}`);
        }
    }
    
    removeStagedPicture(variantId, pictureId) {
        // Remove from staged changes
        if (this.stagedChanges.has(variantId)) {
            const staged = this.stagedChanges.get(variantId);
            staged.picturesToAdd = staged.picturesToAdd.filter(p => p.id !== pictureId);
        }
        
        // Remove from UI
        const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
        if (pictureItem) {
            pictureItem.remove();
        }
        
        this.updateVariantMiniatures(variantId);
        this.updateVariantValidationStatus(variantId);
        this.updateOrderInputMaxValues(variantId);
        this.updateOverallValidationStatus();
        
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
    }
    
    stagePictureForDeletion(variantId, pictureId) {
        // Initialize staged changes if not exists
        if (!this.stagedChanges.has(variantId)) {
            this.stagedChanges.set(variantId, {
                variantToDelete: false,
                picturesToAdd: [],
                picturesToDelete: []
            });
        }
        
        const staged = this.stagedChanges.get(variantId);
        
        // Add to deletion list if not already there
        if (!staged.picturesToDelete.includes(pictureId)) {
            staged.picturesToDelete.push(pictureId);
        }
        
        // Mark the picture as "to be deleted" in the UI
        const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
        if (pictureItem) {
            pictureItem.classList.add('marked-for-deletion');
            pictureItem.style.opacity = '0.5';
            pictureItem.style.filter = 'grayscale(100%)';
            
            // Update the overlay to show deletion status
            const overlay = pictureItem.querySelector('.picture-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <span class="deletion-badge">Will be deleted</span>
                    <button type="button" class="btn-icon btn-icon-secondary" onclick="variantManager.undoPictureDeletion('${variantId}', '${pictureId}')" title="Undo deletion">↶</button>
                `;
            }
        }
    }
    
    undoPictureDeletion(variantId, pictureId) {
        if (this.stagedChanges.has(variantId)) {
            const staged = this.stagedChanges.get(variantId);
            staged.picturesToDelete = staged.picturesToDelete.filter(id => id !== pictureId);
        }
        
        const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
        if (pictureItem) {
            pictureItem.classList.remove('marked-for-deletion');
            pictureItem.style.opacity = '';
            pictureItem.style.filter = '';
            
            // Restore original overlay
            const overlay = pictureItem.querySelector('.picture-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <button type="button" class="btn-icon btn-icon-primary" onclick="variantManager.setPrimaryPicture('${variantId}', '${pictureId}')">★</button>
                    <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${pictureId}')">×</button>
                `;
            }
        }
        
        this.updateVariantMiniatures(variantId);
        this.updateVariantValidationStatus(variantId);
        this.updateOverallValidationStatus();
        
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
        
        this.showSuccessMessage('Picture deletion cancelled');
    }
    
    setPrimaryPicture(variantId, pictureId) {
        // For now, just update locally - actual primary setting will be done on form submission
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        // Remove primary status from all pictures
        grid.querySelectorAll('.primary-badge').forEach(badge => {
            const pictureItem = badge.closest('.picture-item');
            const pictureItemId = pictureItem.dataset.pictureId;
            const overlay = pictureItem.querySelector('.picture-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <button type="button" class="btn-icon btn-icon-primary" onclick="variantManager.setPrimaryPicture('${variantId}', '${pictureItemId}')">★</button>
                    <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${pictureItemId}')">×</button>
                `;
            }
        });
        
        // Set new primary
        const newPrimary = grid.querySelector(`[data-picture-id="${pictureId}"]`);
        if (newPrimary) {
            const overlay = newPrimary.querySelector('.picture-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <span class="primary-badge">Primary</span>
                    <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removePicture('${variantId}', '${pictureId}')">×</button>
                `;
            }
        }
        
        this.updateVariantMiniatures(variantId);
        this.showSuccessMessage('Primary picture set (will be saved on form submission)');
    }
    
    async setPrimaryVariantPicture(variantId, pictureId) {
        try {
            // Check if it's a new picture or existing picture
            if (pictureId.toString().startsWith('new_')) {
                // Handle new variant pictures locally
                this.setPrimaryVariantPictureLocally(variantId, pictureId);
            } else {
                // Set primary via API for existing pictures
                const response = await fetch(`/api/variant/${variantId}/pictures/${pictureId}/primary`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.setPrimaryVariantPictureLocally(variantId, pictureId);
                    this.showSuccessMessage('Primary picture updated');
                } else {
                    throw new Error(result.error || 'Failed to set primary picture');
                }
            }
            
        } catch (error) {
            console.error('Error setting primary picture:', error);
            this.showErrorMessage(`Failed to set primary picture: ${error.message}`);
        }
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
    
    updateVariantValidationStatus(variantId) {
        const variantCard = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (!variantCard) return;
        
        const colorSelect = variantCard.querySelector(`[name*="variant_color_"]`);
        const customColorInput = variantCard.querySelector(`[name*="variant_custom_color_"]`);
        const existingPictures = variantCard.querySelectorAll('.picture-item:not(.marked-for-deletion)').length;
        
        // Check if variant has color
        const hasColor = (colorSelect && colorSelect.value) || 
                        (customColorInput && customColorInput.value.trim());
        
        // Check if variant has pictures
        const hasPictures = existingPictures > 0;
        
        // Update visual indicators
        const variantTitle = variantCard.querySelector('.variant-title');
        const picturesHeader = variantCard.querySelector('.pictures-section-header .form-label');
        
        // Color validation indicator
        if (hasColor) {
            colorSelect?.classList.remove('error');
        } else {
            colorSelect?.classList.add('error');
        }
        
        // Pictures validation indicator
        if (hasPictures) {
            picturesHeader?.classList.remove('error');
        } else if (hasColor) { // Only show picture error if color is selected
            picturesHeader?.classList.add('error');
        }
        
        // Overall variant status
        const isValid = hasColor && hasPictures;
        if (variantTitle) {
            if (isValid) {
                variantTitle.style.color = '';
                variantCard.style.borderLeft = '3px solid #28a745';
            } else if (hasColor || hasPictures) {
                variantTitle.style.color = '#ffc107';
                variantCard.style.borderLeft = '3px solid #ffc107';
            } else {
                variantTitle.style.color = '#dc3545';
                variantCard.style.borderLeft = '3px solid #dc3545';
            }
        }
    }
    
    updateOverallValidationStatus() {
        const allVariants = document.querySelectorAll('[data-variant-id]:not([style*="display: none"]):not([style*="opacity: 0.5"])');
        const submitBtn = document.getElementById('submitBtn');
        
        let hasValidVariants = false;
        let allVariantsValid = true;
        
        allVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name*="variant_color_"]`);
            const customColorInput = variantCard.querySelector(`[name*="variant_custom_color_"]`);
            const existingPictures = variantCard.querySelectorAll('.picture-item:not(.marked-for-deletion)').length;
            
            const hasColor = (colorSelect && colorSelect.value) || 
                            (customColorInput && customColorInput.value.trim());
            const hasPictures = existingPictures > 0;
            
            if (hasColor && hasPictures) {
                hasValidVariants = true;
            } else if (hasColor || hasPictures) {
                allVariantsValid = false;
            }
        });
        
        // Update submit button state
        if (submitBtn) {
            if (hasValidVariants && allVariantsValid) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-warning');
                submitBtn.classList.add('btn-primary');
            } else if (hasValidVariants) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-primary');
                submitBtn.classList.add('btn-warning');
                submitBtn.title = 'Some variants are incomplete';
            } else {
                submitBtn.disabled = true;
                submitBtn.classList.remove('btn-primary', 'btn-warning');
                submitBtn.title = 'At least one complete variant is required';
            }
        }
    }
    
    // New API-based helper methods
    
    handleNewVariantImages(variantId, files) {
        // Store files for new variants until they are created
        if (!this.pendingVariants.has(variantId)) {
            this.pendingVariants.set(variantId, {
                isNew: true,
                colorId: null,
                customColorName: null,
                pictures: []
            });
        }
        
        const variant = this.pendingVariants.get(variantId);
        
        Array.from(files).forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const imageId = `new_${Date.now()}_${index}`;
                    const nextOrder = this.getNextAvailableOrder(variantId);
                    const imageData = {
                        id: imageId,
                        file: file,
                        name: file.name,
                        url: e.target.result,
                        variantId: variantId,
                        isNew: true,
                        isPending: true,
                        picture_order: nextOrder
                    };
                    
                    variant.pictures.push(imageData);
                    this.addPictureToGrid(variantId, imageData);
                    this.updateVariantMiniatures(variantId);
                    this.updateVariantValidationStatus(variantId);
                    this.updateOrderInputMaxValues(variantId);
                    this.updateOverallValidationStatus();
                    
                    if (typeof updateSubmitButtonState === 'function') {
                        updateSubmitButtonState();
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    handleExistingVariantImages(variantId, files) {
        // Initialize staged changes for this variant if not exists
        if (!this.stagedChanges.has(variantId)) {
            this.stagedChanges.set(variantId, {
                variantToDelete: false,
                picturesToAdd: [],
                picturesToDelete: []
            });
        }
        
        const staged = this.stagedChanges.get(variantId);
        
        Array.from(files).forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const tempId = `staged_${variantId}_${Date.now()}_${index}`;
                    const nextOrder = this.getNextAvailableOrder(variantId);
                    const imageData = {
                        id: tempId,
                        name: file.name,
                        url: e.target.result, // Data URL for preview
                        file: file, // Actual file for later upload
                        isStaged: true,
                        isPending: true,
                        variantId: variantId,
                        picture_order: nextOrder
                    };
                    
                    // Add to staged changes
                    staged.picturesToAdd.push(imageData);
                    
                    // Add to grid for preview
                    this.addPictureToGrid(variantId, imageData);
                    
                    // Update UI
                    this.updateVariantMiniatures(variantId);
                    this.updateVariantValidationStatus(variantId);
                    this.updateOrderInputMaxValues(variantId);
                    this.updateOverallValidationStatus();
                    
                    if (typeof updateSubmitButtonState === 'function') {
                        updateSubmitButtonState();
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    addStagedPictureToGrid(variantId, picture) {
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        const pictureDiv = document.createElement('div');
        pictureDiv.className = 'picture-item staged-picture';
        pictureDiv.dataset.pictureId = picture.id;
        
        pictureDiv.innerHTML = `
            <img src="${picture.url}" alt="${picture.name}" onclick="variantManager.previewPicture('${picture.url}', '${picture.name}', '${picture.id}')">
            <div class="picture-overlay">
                <span class="staged-badge">Staged</span>
                <button type="button" class="btn-icon btn-icon-danger" onclick="variantManager.removeStagedPicture('${variantId}', '${picture.id}')">×</button>
            </div>
            <div class="picture-info">
                <input type="text" 
                       name="staged_picture_alt_${picture.id}" 
                       value="" 
                       placeholder="Alt text..." 
                       class="picture-alt-input">
                <small>Staged for upload</small>
            </div>
        `;
        
        grid.appendChild(pictureDiv);
    }
    
    async uploadVariantImagesViaAPI(variantId, files) {
        try {
            this.showLoading(document.getElementById(`pictures_section_${variantId}`), 'Uploading images...');
            
            const formData = new FormData();
            Array.from(files).forEach(file => {
                if (file.type.startsWith('image/')) {
                    formData.append('images', file);
                }
            });
            
            const response = await fetch(`/api/variant/${variantId}/pictures`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Add new pictures to the grid
                result.pictures.forEach(picture => {
                    this.addVariantPictureToGrid(variantId, picture);
                });
                
                this.updateVariantMiniatures(variantId);
                this.updateVariantValidationStatus(variantId);
                this.updateOverallValidationStatus();
                
                this.showSuccessMessage(`Added ${result.pictures.length} pictures`);
            } else {
                throw new Error(result.error || 'Failed to upload images');
            }
            
        } catch (error) {
            console.error('Error uploading images:', error);
            this.showErrorMessage(`Failed to upload images: ${error.message}`);
        } finally {
            this.hideLoading(document.getElementById(`pictures_section_${variantId}`));
        }
    }
    
    async createVariantViaAPI(variantId) {
        // Create a new variant via API when component is saved
        if (!this.pendingVariants.has(variantId) || !this.componentId) {
            return null;
        }
        
        const pendingVariant = this.pendingVariants.get(variantId);
        
        try {
            const response = await fetch('/api/variant/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    component_id: this.componentId,
                    color_id: pendingVariant.colorId,
                    custom_color_name: pendingVariant.customColorName
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const newVariantId = result.variant.id;
                
                // Upload pictures if any
                if (pendingVariant.pictures.length > 0) {
                    const formData = new FormData();
                    pendingVariant.pictures.forEach(pic => {
                        formData.append('images', pic.file);
                    });
                    
                    await fetch(`/api/variant/${newVariantId}/pictures`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': this.csrfToken
                        },
                        body: formData
                    });
                }
                
                return result.variant;
            } else {
                throw new Error(result.error || 'Failed to create variant');
            }
            
        } catch (error) {
            console.error('Error creating variant:', error);
            throw error;
        }
    }
    
    // UI Helper methods
    
    showLoading(element, message) {
        if (!element) return;
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-overlay';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-message">${message}</div>
        `;
        
        element.style.position = 'relative';
        element.appendChild(loadingDiv);
    }
    
    hideLoading(element) {
        if (!element) return;
        
        const loading = element.querySelector('.loading-overlay');
        if (loading) {
            loading.remove();
        }
    }
    
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // Create or update message display
        let messageContainer = document.getElementById('variant-messages');
        if (!messageContainer) {
            messageContainer = document.createElement('div');
            messageContainer.id = 'variant-messages';
            messageContainer.className = 'message-container';
            document.body.appendChild(messageContainer);
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        
        messageContainer.appendChild(messageDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    
    async deleteExistingPicture(variantId, pictureId) {
        const response = await fetch(`/api/variant/${variantId}/pictures/${pictureId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to delete picture');
        }
    }
    
    async uploadStagedPictures(variantId, pictures) {
        const formData = new FormData();
        pictures.forEach(picture => {
            formData.append('images', picture.file);
        });
        
        const response = await fetch(`/api/variant/${variantId}/pictures`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken
            },
            body: formData
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to upload pictures');
        }
    }
    
    // Get summary of all changes for form submission
    getChangesSummary() {
        let summary = {
            newVariants: this.pendingVariants.size,
            variantChanges: 0,
            pictureAdditions: 0,
            pictureDeletions: 0,
            variantDeletions: 0
        };
        
        // Count staged changes
        for (let [variantId, changes] of this.stagedChanges) {
            if (changes.variantToDelete) {
                summary.variantDeletions++;
            } else {
                if (changes.picturesToAdd.length > 0 || changes.picturesToDelete.length > 0) {
                    summary.variantChanges++;
                }
                summary.pictureAdditions += changes.picturesToAdd.length;
                summary.pictureDeletions += changes.picturesToDelete.length;
            }
        }
        
        // Count new variant pictures
        for (let [variantId, variant] of this.pendingVariants) {
            summary.pictureAdditions += variant.pictures.length;
        }
        
        return summary;
    }
    
    // API method to create a variant (called by form handler)
    async createVariantViaAPI(variantId) {
        if (!this.pendingVariants.has(variantId) || !this.componentId) {
            throw new Error('Invalid variant or missing component ID');
        }
        
        const pendingVariant = this.pendingVariants.get(variantId);
        
        try {
            console.log(`Creating variant ${variantId} for component ${this.componentId}`);
            
            // Create the variant first
            const response = await fetch('/api/variant/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    component_id: this.componentId,
                    color_id: pendingVariant.colorId,
                    custom_color_name: pendingVariant.customColorName
                })
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to create variant');
            }
            
            const newVariantId = result.variant.id;
            console.log(`Variant created with ID: ${newVariantId}`);
            
            // Upload pictures if any
            if (pendingVariant.pictures.length > 0) {
                console.log(`Uploading ${pendingVariant.pictures.length} pictures for variant ${newVariantId}`);
                
                const formData = new FormData();
                pendingVariant.pictures.forEach(pic => {
                    formData.append('images', pic.file);
                });
                
                const pictureResponse = await fetch(`/api/variant/${newVariantId}/pictures`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.csrfToken
                    },
                    body: formData
                });
                
                const pictureResult = await pictureResponse.json();
                
                if (!pictureResult.success) {
                    console.warn(`Variant created but picture upload failed: ${pictureResult.error}`);
                    // Don't throw error - variant was created successfully
                } else {
                    console.log(`Uploaded ${pictureResult.pictures.length} pictures for variant ${newVariantId}`);
                }
            }
            
            return result.variant;
            
        } catch (error) {
            console.error(`Error creating variant ${variantId}:`, error);
            throw error;
        }
    }
    
    // Get all pending and staged changes for processing
    getAllChanges() {
        return {
            pendingVariants: this.pendingVariants,
            stagedChanges: this.stagedChanges
        };
    }
    
    // Process all staged changes for existing components (edit mode)
    async processStagedChanges() {
        const promises = [];
        
        for (let [variantId, changes] of this.stagedChanges) {
            // Process variant deletions first
            if (changes.variantToDelete) {
                promises.push(this.deleteVariantViaAPI(variantId));
                continue;
            }
            
            // Process picture deletions
            for (let pictureId of changes.picturesToDelete) {
                promises.push(this.deleteExistingPicture(variantId, pictureId));
            }
            
            // Process picture additions
            if (changes.picturesToAdd.length > 0) {
                promises.push(this.uploadStagedPictures(variantId, changes.picturesToAdd));
            }
        }
        
        if (promises.length > 0) {
            try {
                await Promise.all(promises);
                this.showSuccessMessage('All changes processed successfully');
                
                // Clear staged changes
                this.stagedChanges.clear();
                
                return true;
            } catch (error) {
                this.showErrorMessage(`Failed to process some changes: ${error.message}`);
                return false;
            }
        }
        
        return true; // No changes to process
    }
    
    async deleteVariantViaAPI(variantId) {
        const response = await fetch(`/api/variant/${variantId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to delete variant');
        }
    }
    
    async deleteExistingPicture(variantId, pictureId) {
        const response = await fetch(`/api/variant/${variantId}/pictures/${pictureId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to delete picture');
        }
    }
    
    async uploadStagedPictures(variantId, pictures) {
        const formData = new FormData();
        pictures.forEach(picture => {
            formData.append('images', picture.file);
        });
        
        const response = await fetch(`/api/variant/${variantId}/pictures`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken
            },
            body: formData
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to upload pictures');
        }
    }
    
    // Clear all changes (called after successful form submission)
    clearAllChanges() {
        this.pendingVariants.clear();
        this.stagedChanges.clear();
    }
    
    // Update form files for new component submission (legacy support)
    updateFormFiles() {
        // This method exists for compatibility with form handler
        // In our new approach, files are handled via API, not form submission
        console.log('updateFormFiles called - using API approach instead');
    }
    
    async loadComponentEditData() {
        try {
            console.log('Loading component edit data via API...');
            
            const response = await fetch(`/api/components/${this.componentId}/edit-data`, {
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Failed to load component data`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.populateVariantsWithPictures(result.component.variants);
                console.log('Component edit data loaded successfully');
            } else {
                throw new Error(result.error || 'Failed to load component data');
            }
            
        } catch (error) {
            console.error('Error loading component edit data:', error);
            this.showErrorMessage(`Failed to load component data: ${error.message}`);
        }
    }
    
    populateVariantsWithPictures(variants) {
        variants.forEach(variantData => {
            const variantCard = document.querySelector(`[data-variant-id="${variantData.id}"]`);
            if (!variantCard) return;
            
            // Get the pictures grid for this variant
            const picturesGrid = variantCard.querySelector(`#pictures_grid_${variantData.id}`);
            
            if (picturesGrid && variantData.pictures.length > 0) {
                // Clear existing content
                picturesGrid.innerHTML = '';
                
                // Add each picture
                variantData.pictures.forEach(picture => {
                    this.addPictureToGrid(variantData.id, {
                        id: picture.id,
                        picture_name: picture.picture_name,
                        url: picture.url,
                        alt_text: picture.alt_text,
                        is_primary: picture.is_primary,
                        picture_order: picture.picture_order,
                        isPending: false,
                        isStaged: false
                    });
                });
                
                // Update miniatures and max values
                this.updateVariantMiniatures(variantData.id);
                this.updateOrderInputMaxValues(variantData.id);
            }
        });
        
        // Update validation status after loading
        this.updateOverallValidationStatus();
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
    }
    
    stageVariantForDeletion(variantId) {
        // Initialize staged changes if not exists
        if (!this.stagedChanges.has(variantId)) {
            this.stagedChanges.set(variantId, {
                variantToDelete: true,
                picturesToAdd: [],
                picturesToDelete: []
            });
        } else {
            this.stagedChanges.get(variantId).variantToDelete = true;
        }
    }
    
    undoVariantDeletion(variantId) {
        // Remove deletion staging
        if (this.stagedChanges.has(variantId)) {
            this.stagedChanges.get(variantId).variantToDelete = false;
        }
        
        // Restore variant appearance
        const variantCard = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (variantCard) {
            variantCard.style.opacity = '';
            variantCard.style.filter = '';
            
            // Remove undo button
            const undoBtn = variantCard.querySelector('.undo-deletion');
            if (undoBtn) {
                undoBtn.remove();
            }
        }
        
        this.showSuccessMessage('Variant deletion cancelled');
    }
}

// Initialize variant manager when DOM is ready
let variantManager = null;

function initializeVariantManager() {
    variantManager = new VariantManager();
    window.variantManager = variantManager;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeVariantManager);
} else {
    initializeVariantManager();
}

// Global function to get variant manager changes for form submission
window.getVariantManagerChanges = function() {
    return variantManager ? variantManager.getAllChanges() : null;
};

// Global function to clear variant manager changes after form submission
window.clearVariantManagerChanges = function() {
    if (variantManager) {
        variantManager.clearAllChanges();
    }
};

// Global function for form handler to process staged changes (edit mode)
window.processVariantManagerChanges = function() {
    if (variantManager && typeof variantManager.processStagedChanges === 'function') {
        return variantManager.processStagedChanges();
    }
    return Promise.resolve(true);
};

// Global function to get changes summary for display
window.getVariantChangesSummary = function() {
    return variantManager ? variantManager.getChangesSummary() : null;
};

// Global function to check if there are pending variants (for form validation)
window.hasPendingVariants = function() {
    return variantManager ? variantManager.pendingVariants.size > 0 : false;
};