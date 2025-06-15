"""Supplier business logic service."""

from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from app.repositories.supplier_repository import SupplierRepository
from app.utils.validators import validate_data, supplier_code_validator, description_validator


class SupplierService:
    """Service for supplier business logic."""
    
    @staticmethod
    def get_all_suppliers(sort_by: str = 'code') -> List[Dict[str, Any]]:
        """Get all suppliers formatted for API/web responses."""
        suppliers = SupplierRepository.get_all(sort_by=sort_by)
        
        suppliers_data = []
        for supplier in suppliers:
            supplier_dict = {
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'address': supplier.address,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
                'component_count': len(supplier.components),
                'components': [
                    {
                        'id': c.id, 
                        'product_number': c.product_number,
                        'description': c.description
                    } for c in supplier.components
                ]
            }
            suppliers_data.append(supplier_dict)
        
        return suppliers_data
    
    @staticmethod
    def get_supplier(supplier_id: int) -> Optional[Dict[str, Any]]:
        """Get a single supplier by ID."""
        supplier = SupplierRepository.get_by_id(supplier_id)
        if not supplier:
            return None
        
        return {
            'id': supplier.id,
            'supplier_code': supplier.supplier_code,
            'address': supplier.address,
            'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
            'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
            'component_count': len(supplier.components),
            'components': [
                {
                    'id': c.id, 
                    'product_number': c.product_number,
                    'description': c.description
                } for c in supplier.components
            ]
        }
    
    @staticmethod
    def create_supplier(form_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a new supplier with validation.
        Returns (success, message, supplier_data) tuple.
        """
        try:
            # Define validation rules
            validation_rules = {
                'supplier_code': supplier_code_validator,
                'address': description_validator
            }
            
            # Validate form data
            validated_data = validate_data(form_data, validation_rules)
            
            # Check if supplier already exists
            if SupplierRepository.exists_by_code(validated_data['supplier_code']):
                return False, f'Supplier with code "{validated_data["supplier_code"]}" already exists.', None
            
            # Create supplier
            supplier, success = SupplierRepository.create(
                supplier_code=validated_data['supplier_code'],
                address=validated_data.get('address')
            )
            
            if success and supplier:
                supplier_data = {
                    'id': supplier.id,
                    'supplier_code': supplier.supplier_code,
                    'address': supplier.address,
                    'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                    'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None
                }
                return True, f'Supplier "{supplier.supplier_code}" created successfully.', supplier_data
            else:
                return False, 'Failed to create supplier.', None
                
        except Exception as e:
            current_app.logger.error(f"Error creating supplier: {str(e)}")
            return False, 'Error creating supplier. Please check your input and try again.', None
    
    @staticmethod
    def update_supplier(supplier_id: int, form_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update a supplier with validation.
        Returns (success, message, supplier_data) tuple.
        """
        try:
            # Check if supplier exists
            existing_supplier = SupplierRepository.get_by_id(supplier_id)
            if not existing_supplier:
                return False, 'Supplier not found.', None
            
            # Define validation rules
            validation_rules = {
                'supplier_code': supplier_code_validator,
                'address': description_validator
            }
            
            # Validate form data
            validated_data = validate_data(form_data, validation_rules)
            
            # Check if supplier code conflicts with existing (excluding current)
            if SupplierRepository.exists_by_code(validated_data['supplier_code'], exclude_id=supplier_id):
                return False, f'Supplier with code "{validated_data["supplier_code"]}" already exists.', None
            
            # Update supplier
            supplier, success = SupplierRepository.update(
                supplier_id=supplier_id,
                supplier_code=validated_data['supplier_code'],
                address=validated_data.get('address')
            )
            
            if success and supplier:
                supplier_data = {
                    'id': supplier.id,
                    'supplier_code': supplier.supplier_code,
                    'address': supplier.address,
                    'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                    'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None
                }
                return True, f'Supplier "{supplier.supplier_code}" updated successfully.', supplier_data
            else:
                return False, 'Failed to update supplier.', None
                
        except Exception as e:
            current_app.logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
            return False, 'Error updating supplier. Please check your input and try again.', None
    
    @staticmethod
    def delete_supplier(supplier_id: int) -> Tuple[bool, str]:
        """
        Delete a supplier.
        Returns (success, message) tuple.
        """
        try:
            success, message = SupplierRepository.delete(supplier_id)
            return success, message
            
        except Exception as e:
            current_app.logger.error(f"Error deleting supplier {supplier_id}: {str(e)}")
            return False, 'Error deleting supplier.'
    
    @staticmethod
    def bulk_delete_suppliers(supplier_ids: List[int]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Delete multiple suppliers.
        Returns (success, message, results) tuple.
        """
        try:
            if not supplier_ids:
                return False, 'No supplier IDs provided.', {}
            
            # Validate that all IDs are integers
            try:
                supplier_ids = [int(id) for id in supplier_ids]
            except (ValueError, TypeError):
                return False, 'All supplier IDs must be valid integers.', {}
            
            # Check if all suppliers exist
            existing_suppliers = SupplierRepository.get_by_ids(supplier_ids)
            if len(existing_suppliers) != len(supplier_ids):
                return False, 'One or more suppliers not found.', {}
            
            # Perform bulk delete
            deleted_count, deleted_suppliers, errors = SupplierRepository.bulk_delete(supplier_ids)
            
            results = {
                'deleted_count': deleted_count,
                'deleted_suppliers': deleted_suppliers,
                'errors': errors
            }
            
            if errors:
                return False, f'Partially completed. Deleted {deleted_count} suppliers with {len(errors)} errors.', results
            else:
                return True, f'Successfully deleted {deleted_count} supplier(s).', results
                
        except Exception as e:
            current_app.logger.error(f"Error in bulk delete: {str(e)}")
            return False, 'Error deleting suppliers.', {}
    
    @staticmethod
    def search_suppliers(query: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search suppliers with pagination.
        Returns search results with pagination info.
        """
        try:
            if not query.strip():
                return {
                    'suppliers': [],
                    'pagination': {
                        'page': 1,
                        'pages': 0,
                        'per_page': per_page,
                        'total': 0,
                        'has_next': False,
                        'has_prev': False
                    }
                }
            
            suppliers, pagination = SupplierRepository.search(query, page, per_page)
            
            # Format supplier data
            suppliers_data = []
            for supplier in suppliers:
                suppliers_data.append({
                    'id': supplier.id,
                    'supplier_code': supplier.supplier_code,
                    'address': supplier.address,
                    'component_count': len(supplier.components),
                    'created_at': supplier.created_at.isoformat() if supplier.created_at else None
                })
            
            return {
                'suppliers': suppliers_data,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error searching suppliers: {str(e)}")
            return {
                'suppliers': [],
                'pagination': {
                    'page': 1,
                    'pages': 0,
                    'per_page': per_page,
                    'total': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    @staticmethod
    def validate_supplier_data(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, str]]:
        """
        Validate supplier form data.
        Returns (is_valid, validated_data, errors) tuple.
        """
        try:
            validation_rules = {
                'supplier_code': supplier_code_validator,
                'address': description_validator
            }
            
            validated_data = validate_data(form_data, validation_rules)
            return True, validated_data, {}
            
        except Exception as e:
            if hasattr(e, 'field') and isinstance(e.field, dict):
                return False, {}, e.field
            else:
                return False, {}, {'general': str(e)}