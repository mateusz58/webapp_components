/* Supplier Management Page JavaScript */

/**
 * Supplier Management Alpine.js Component
 * Handles all supplier CRUD operations, search, filtering, and bulk actions
 */
function supplierManagement() {
    return {
        // UI State
        showAddForm: false,
        searchQuery: '',
        sortBy: 'code',
        selectedSuppliers: [],
        allSelected: false,
        filteredSuppliers: [],
        
        // Form Data
        newSupplier: {
            code: '',
            name: '',
            address: '',
            email: ''
        },
        
        editSupplierData: {
            id: null,
            code: '',
            name: '',
            address: '',
            email: ''
        },
        
        supplierToDelete: null,
        
        // Data - will be populated from server
        suppliers: [],

        /**
         * Initialize component
         */
        init() {
            // Get suppliers data from window object set by template
            this.suppliers = window.suppliersData || [];
            this.filteredSuppliers = this.suppliers.map(s => s.id);
            this.filterSuppliers();
        },

        /**
         * Add new supplier
         */
        async addSupplier() {
            if (!this.newSupplier.code.trim()) {
                AppUtils.showFlashMessage('Supplier code is required', 'error');
                return;
            }

            try {
                const formData = new FormData();
                formData.append('supplier_code', this.newSupplier.code);
                formData.append('address', this.newSupplier.address);
                formData.append('email', this.newSupplier.email);

                const response = await ApiUtils.postForm('/suppliers/new', formData);
                
                if (response) {
                    AppUtils.showFlashMessage('Supplier added successfully', 'success');
                    this.resetForm();
                    this.showAddForm = false;
                    // Reload page to get updated data
                    setTimeout(() => window.location.reload(), 1000);
                }
            } catch (error) {
                console.error('Error adding supplier:', error);
                AppUtils.showFlashMessage('Error adding supplier', 'error');
            }
        },

        /**
         * Reset new supplier form
         */
        resetForm() {
            this.newSupplier = {
                code: '',
                name: '',
                address: '',
                email: ''
            };
        },

        /**
         * Filter suppliers based on search query
         */
        filterSuppliers() {
            if (!this.searchQuery.trim()) {
                this.filteredSuppliers = this.suppliers.map(s => s.id);
                return;
            }

            const query = this.searchQuery.toLowerCase();
            this.filteredSuppliers = this.suppliers
                .filter(supplier => 
                    supplier.supplier_code.toLowerCase().includes(query) ||
                    (supplier.address && supplier.address.toLowerCase().includes(query))
                )
                .map(s => s.id);
        },

        /**
         * Sort suppliers by selected criteria
         */
        sortSuppliers() {
            const url = new URL(window.location);
            url.searchParams.set('sort', this.sortBy);
            window.location.href = url.toString();
        },

        /**
         * Toggle supplier selection for bulk operations
         */
        toggleSupplierSelection(supplierId) {
            const index = this.selectedSuppliers.indexOf(supplierId);
            if (index > -1) {
                this.selectedSuppliers.splice(index, 1);
            } else {
                this.selectedSuppliers.push(supplierId);
            }
            this.updateAllSelectedState();
        },

        /**
         * Toggle select all suppliers
         */
        toggleSelectAll() {
            if (this.allSelected) {
                this.selectedSuppliers = [];
            } else {
                this.selectedSuppliers = [...this.filteredSuppliers];
            }
            this.updateAllSelectedState();
        },

        /**
         * Update the "select all" state based on individual selections
         */
        updateAllSelectedState() {
            this.allSelected = this.selectedSuppliers.length === this.filteredSuppliers.length && this.filteredSuppliers.length > 0;
        },

        /**
         * Clear all selections
         */
        clearSelection() {
            this.selectedSuppliers = [];
            this.allSelected = false;
        },

        /**
         * Open edit supplier modal
         */
        editSupplier(supplierId) {
            const supplier = this.suppliers.find(s => s.id === supplierId);
            if (supplier) {
                this.editSupplierData = {
                    id: supplier.id,
                    code: supplier.supplier_code,
                    name: supplier.name || '',
                    address: supplier.address || '',
                    email: supplier.email || ''
                };
                
                const modalElement = document.getElementById('editSupplierModal');
                if (modalElement && typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                }
            }
        },

        /**
         * Save supplier changes
         */
        async saveSupplier() {
            try {
                const formData = new FormData();
                formData.append('supplier_code', this.editSupplierData.code);
                formData.append('address', this.editSupplierData.address);
                formData.append('email', this.editSupplierData.email);

                const response = await ApiUtils.postForm(`/api/suppliers/${this.editSupplierData.id}`, formData);
                
                if (response) {
                    AppUtils.showFlashMessage('Supplier updated successfully', 'success');
                    
                    // Hide modal
                    const modalElement = document.getElementById('editSupplierModal');
                    if (modalElement && typeof bootstrap !== 'undefined') {
                        const modalInstance = bootstrap.Modal.getInstance(modalElement);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                    }
                    
                    // Reload page to get updated data
                    setTimeout(() => window.location.reload(), 1000);
                }
            } catch (error) {
                console.error('Error updating supplier:', error);
                AppUtils.showFlashMessage('Error updating supplier', 'error');
            }
        },

        /**
         * Open delete confirmation modal
         */
        deleteSupplier(supplierId) {
            const supplier = this.suppliers.find(s => s.id === supplierId);
            if (supplier) {
                this.supplierToDelete = {
                    id: supplier.id,
                    code: supplier.supplier_code,
                    componentCount: supplier.components ? supplier.components.length : 0
                };
                
                const modalElement = document.getElementById('deleteConfirmModal');
                if (modalElement && typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                }
            }
        },

        /**
         * Confirm supplier deletion
         */
        async confirmDelete() {
            if (!this.supplierToDelete) return;

            try {
                await ApiUtils.delete(`/api/suppliers/${this.supplierToDelete.id}`);
                
                AppUtils.showFlashMessage('Supplier deleted successfully', 'success');
                
                // Hide modal
                const modalElement = document.getElementById('deleteConfirmModal');
                if (modalElement && typeof bootstrap !== 'undefined') {
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
                
                // Reload page to get updated data
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                console.error('Error deleting supplier:', error);
                AppUtils.showFlashMessage('Error deleting supplier', 'error');
            }
        },

        /**
         * Navigate to components view filtered by supplier
         */
        viewComponents(supplierId) {
            window.location.href = `/?supplier_id=${supplierId}`;
        },

        /**
         * Export selected suppliers
         */
        bulkExport() {
            if (this.selectedSuppliers.length === 0) {
                AppUtils.showFlashMessage('Please select suppliers to export', 'warning');
                return;
            }
            
            const ids = this.selectedSuppliers.join(',');
            window.open(`/api/suppliers/export?ids=${ids}`, '_blank');
        },

        /**
         * Delete multiple suppliers
         */
        async bulkDelete() {
            if (this.selectedSuppliers.length === 0) {
                AppUtils.showFlashMessage('Please select suppliers to delete', 'warning');
                return;
            }

            const confirmed = confirm(`Are you sure you want to delete ${this.selectedSuppliers.length} supplier(s)?`);
            if (!confirmed) return;

            try {
                await ApiUtils.post('/api/suppliers/bulk-delete', {
                    ids: this.selectedSuppliers
                });
                
                AppUtils.showFlashMessage('Suppliers deleted successfully', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                console.error('Error deleting suppliers:', error);
                AppUtils.showFlashMessage('Error deleting suppliers', 'error');
            }
        },

        /**
         * Export all suppliers
         */
        exportSuppliers() {
            window.open('/api/suppliers/export', '_blank');
        }
    };
}

// Make function available globally for Alpine.js
window.supplierManagement = supplierManagement;