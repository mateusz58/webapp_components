/**
 * Brand Information Management Module
 * Handles all brand-related functionality including:
 * - Brand selection and creation
 * - Subbrand selection and creation
 * - Brand validation
 * - Multiple brand management
 */

class BrandManager {
    constructor() {
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
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize state based on current selections
        this.initializeState();
        
        console.log('BrandManager initialized');
    }
    
    setupEventListeners() {
        // Brand selection handler
        const brandSelect = document.getElementById('brand_id');
        if (brandSelect) {
            brandSelect.addEventListener('change', () => this.handleBrandSelection());
        }
        
        // Subbrand selection handler
        const subbrandSelect = document.getElementById('subbrand_id');
        if (subbrandSelect) {
            subbrandSelect.addEventListener('change', () => this.handleSubbrandSelection());
        }
        
        // Subbrand name validation
        const subbrandNameInput = document.getElementById('new_subbrand_name');
        if (subbrandNameInput) {
            subbrandNameInput.addEventListener('change', () => this.validateSubbrandName());
            subbrandNameInput.addEventListener('input', () => this.validateSubbrandName());
        }
        
        // Brand name validation
        const brandNameInput = document.getElementById('new_brand_name');
        if (brandNameInput) {
            brandNameInput.addEventListener('change', () => this.validateBrandName());
            brandNameInput.addEventListener('input', () => this.validateBrandName());
        }
    }
    
    initializeState() {
        // Check if brand is already selected and show subbrand options if needed
        const brandSelect = document.getElementById('brand_id');
        if (brandSelect && brandSelect.value && brandSelect.value !== 'new') {
            this.loadSubbrands(brandSelect.value);
        }
        
        // Handle initial state if 'new' brand is selected
        if (brandSelect && brandSelect.value === 'new') {
            this.showNewBrandInput();
        }
    }
    
    handleBrandSelection() {
        const brandSelect = document.getElementById('brand_id');
        const subbrandGroup = document.getElementById('subbrand_group');
        const newBrandInput = document.getElementById('new_brand_input');
        const newSubbrandInput = document.getElementById('new_subbrand_input');
        
        if (!brandSelect) return;
        
        const selectedValue = brandSelect.value;
        
        // Hide all conditional inputs first
        if (subbrandGroup) subbrandGroup.style.display = 'none';
        if (newBrandInput) newBrandInput.style.display = 'none';
        if (newSubbrandInput) newSubbrandInput.style.display = 'none';
        
        // Clear any previous errors
        this.clearErrors();
        
        if (selectedValue === 'new') {
            // Show new brand input
            this.showNewBrandInput();
        } else if (selectedValue) {
            // Load subbrands for selected brand
            this.loadSubbrands(selectedValue);
            if (subbrandGroup) {
                subbrandGroup.style.display = 'block';
            }
        }
        
        console.log(`Brand selection changed to: ${selectedValue}`);
    }
    
    handleSubbrandSelection() {
        const subbrandSelect = document.getElementById('subbrand_id');
        const newSubbrandInput = document.getElementById('new_subbrand_input');
        
        if (!subbrandSelect) return;
        
        const selectedValue = subbrandSelect.value;
        
        if (selectedValue === 'new') {
            // Show new subbrand input
            this.showNewSubbrandInput();
        } else {
            // Hide new subbrand input
            if (newSubbrandInput) {
                newSubbrandInput.style.display = 'none';
            }
        }
        
        console.log(`Subbrand selection changed to: ${selectedValue}`);
    }
    
    showNewBrandInput() {
        const newBrandInput = document.getElementById('new_brand_input');
        const brandNameInput = document.getElementById('new_brand_name');
        
        if (newBrandInput) {
            newBrandInput.style.display = 'block';
            if (brandNameInput) {
                brandNameInput.focus();
            }
        }
    }
    
    showNewSubbrandInput() {
        const newSubbrandInput = document.getElementById('new_subbrand_input');
        const subbrandNameInput = document.getElementById('new_subbrand_name');
        
        if (newSubbrandInput) {
            newSubbrandInput.style.display = 'block';
            if (subbrandNameInput) {
                subbrandNameInput.focus();
            }
        }
    }
    
    async loadSubbrands(brandId) {
        const subbrandSelect = document.getElementById('subbrand_id');
        if (!subbrandSelect || !brandId) return;
        
        try {
            // Show loading state
            subbrandSelect.disabled = true;
            subbrandSelect.innerHTML = '<option value="">Loading subbrands...</option>';
            
            // Fetch subbrands for the selected brand
            const response = await fetch(`/api/brands/${brandId}/subbrands`);
            
            if (!response.ok) {
                throw new Error('Failed to load subbrands');
            }
            
            const subbrands = await response.json();
            
            // Rebuild subbrand options
            subbrandSelect.innerHTML = `
                <option value="">Select a subbrand...</option>
                ${subbrands.map(subbrand => 
                    `<option value="${subbrand.id}">${subbrand.name}</option>`
                ).join('')}
                <option value="new">+ Create New Subbrand</option>
            `;
            
            subbrandSelect.disabled = false;
            
        } catch (error) {
            console.error('Error loading subbrands:', error);
            
            // Fallback options
            subbrandSelect.innerHTML = `
                <option value="">Select a subbrand...</option>
                <option value="new">+ Create New Subbrand</option>
            `;
            subbrandSelect.disabled = false;
            
            // Show error message
            this.showError('subbrand', 'Failed to load subbrands. You can still create a new one.');
        }
    }
    
    validateBrandName() {
        const brandNameInput = document.getElementById('new_brand_name');
        if (!brandNameInput) return true;
        
        const value = brandNameInput.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        if (!value) {
            errorMessage = 'Brand name is required when creating a new brand';
            isValid = false;
        } else if (value.length < 2) {
            errorMessage = 'Brand name must be at least 2 characters';
            isValid = false;
        } else if (value.length > 100) {
            errorMessage = 'Brand name must be less than 100 characters';
            isValid = false;
        }
        
        if (isValid) {
            this.clearError('new_brand');
        } else {
            this.showError('new_brand', errorMessage);
        }
        
        return isValid;
    }
    
    validateSubbrandName() {
        const subbrandNameInput = document.getElementById('new_subbrand_name');
        if (!subbrandNameInput) return true;
        
        const value = subbrandNameInput.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        if (!value) {
            errorMessage = 'Subbrand name is required when creating a new subbrand';
            isValid = false;
        } else if (value.length < 2) {
            errorMessage = 'Subbrand name must be at least 2 characters';
            isValid = false;
        } else if (value.length > 100) {
            errorMessage = 'Subbrand name must be less than 100 characters';
            isValid = false;
        }
        
        if (isValid) {
            this.clearError('new_subbrand');
        } else {
            this.showError('new_subbrand', errorMessage);
        }
        
        return isValid;
    }
    
    removeBrand(brandId) {
        const brandTag = document.querySelector(`[onclick="removeBrand(${brandId})"]`)?.closest('.brand-tag');
        if (brandTag && confirm('Remove this brand association?')) {
            brandTag.remove();
            
            // Update form state or trigger change detection
            if (typeof updateSubmitButtonState === 'function') {
                updateSubmitButtonState();
            }
            
            console.log(`Removed brand: ${brandId}`);
        }
    }
    
    showError(fieldPrefix, message) {
        const errorElement = document.getElementById(`${fieldPrefix}_error`);
        const inputElement = document.getElementById(`${fieldPrefix}_name`) || document.getElementById(`${fieldPrefix}_id`);
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
        
        if (inputElement) {
            inputElement.classList.add('error');
        }
    }
    
    clearError(fieldPrefix) {
        const errorElement = document.getElementById(`${fieldPrefix}_error`);
        const inputElement = document.getElementById(`${fieldPrefix}_name`) || document.getElementById(`${fieldPrefix}_id`);
        
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
        
        if (inputElement) {
            inputElement.classList.remove('error');
        }
    }
    
    clearErrors() {
        ['brand', 'new_brand', 'subbrand', 'new_subbrand'].forEach(prefix => {
            this.clearError(prefix);
        });
    }
    
    validateBeforeSubmit() {
        const brandSelect = document.getElementById('brand_id');
        let isValid = true;
        
        if (brandSelect) {
            const brandValue = brandSelect.value;
            
            if (brandValue === 'new') {
                // Validate new brand name
                if (!this.validateBrandName()) {
                    isValid = false;
                }
            }
            
            // Check subbrand if applicable
            const subbrandSelect = document.getElementById('subbrand_id');
            if (subbrandSelect && subbrandSelect.style.display !== 'none' && subbrandSelect.value === 'new') {
                if (!this.validateSubbrandName()) {
                    isValid = false;
                }
            }
        }
        
        return isValid;
    }
}

// Global functions for template compatibility
function handleBrandSelection() {
    if (window.brandManager) {
        window.brandManager.handleBrandSelection();
    }
}

function handleSubbrandSelection() {
    if (window.brandManager) {
        window.brandManager.handleSubbrandSelection();
    }
}

function validateSubbrandName() {
    if (window.brandManager) {
        return window.brandManager.validateSubbrandName();
    }
    return true;
}

function removeBrand(brandId) {
    if (window.brandManager) {
        window.brandManager.removeBrand(brandId);
    }
}

// Initialize brand manager when DOM is ready
let brandManager = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        brandManager = new BrandManager();
    });
} else {
    brandManager = new BrandManager();
}

// Export for global access
window.brandManager = brandManager;