"""Supplier repository for database operations."""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import or_, func
from app import db
from app.models import Supplier, Component
from app.utils.database import get_or_create, safe_commit, safe_delete


class SupplierRepository:
    """Repository for supplier database operations."""
    
    @staticmethod
    def get_all(sort_by: str = 'code') -> List[Supplier]:
        """Get all suppliers with optional sorting."""
        query = Supplier.query
        
        if sort_by == 'name':
            query = query.order_by(Supplier.supplier_code)
        elif sort_by == 'components':
            # Sort by component count
            query = query.outerjoin(Component).group_by(Supplier.id).order_by(
                func.count(Component.id).desc()
            )
        elif sort_by == 'created':
            query = query.order_by(Supplier.created_at.desc())
        else:  # default to code
            query = query.order_by(Supplier.supplier_code)
        
        return query.all()
    
    @staticmethod
    def get_by_id(supplier_id: int) -> Optional[Supplier]:
        """Get supplier by ID."""
        return Supplier.query.get(supplier_id)
    
    @staticmethod
    def get_by_code(supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code."""
        return Supplier.query.filter_by(supplier_code=supplier_code).first()
    
    @staticmethod
    def search(query: str, page: int = 1, per_page: int = 20) -> tuple:
        """
        Search suppliers by code or address.
        Returns (suppliers, pagination) tuple.
        """
        search_query = Supplier.query.filter(
            or_(
                Supplier.supplier_code.ilike(f'%{query}%'),
                Supplier.address.ilike(f'%{query}%')
            )
        ).order_by(Supplier.supplier_code)
        
        pagination = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return pagination.items, pagination
    
    @staticmethod
    def create(supplier_code: str, address: str = None) -> Tuple[Optional[Supplier], bool]:
        """
        Create a new supplier.
        Returns (supplier, success) tuple.
        """
        try:
            # Check if supplier already exists
            existing = SupplierRepository.get_by_code(supplier_code)
            if existing:
                return None, False
            
            supplier = Supplier(
                supplier_code=supplier_code,
                address=address
            )
            
            db.session.add(supplier)
            
            if safe_commit():
                return supplier, True
            else:
                return None, False
                
        except Exception:
            db.session.rollback()
            return None, False
    
    @staticmethod
    def update(supplier_id: int, **kwargs) -> Tuple[Optional[Supplier], bool]:
        """
        Update a supplier.
        Returns (supplier, success) tuple.
        """
        try:
            supplier = SupplierRepository.get_by_id(supplier_id)
            if not supplier:
                return None, False
            
            # Check for supplier code conflicts if updating code
            if 'supplier_code' in kwargs:
                existing = Supplier.query.filter(
                    Supplier.supplier_code == kwargs['supplier_code'],
                    Supplier.id != supplier_id
                ).first()
                if existing:
                    return None, False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            
            if safe_commit():
                return supplier, True
            else:
                return None, False
                
        except Exception:
            db.session.rollback()
            return None, False
    
    @staticmethod
    def delete(supplier_id: int) -> Tuple[bool, str]:
        """
        Delete a supplier.
        Returns (success, message) tuple.
        """
        try:
            supplier = SupplierRepository.get_by_id(supplier_id)
            if not supplier:
                return False, "Supplier not found"
            
            # Check for associated components
            component_count = Component.query.filter_by(supplier_id=supplier_id).count()
            if component_count > 0:
                return False, f"Supplier has {component_count} associated component(s)"
            
            supplier_code = supplier.supplier_code
            
            if safe_delete(supplier):
                return True, f'Supplier "{supplier_code}" deleted successfully'
            else:
                return False, "Failed to delete supplier"
                
        except Exception:
            return False, "Error deleting supplier"
    
    @staticmethod
    def bulk_delete(supplier_ids: List[int]) -> Tuple[int, List[str], List[str]]:
        """
        Delete multiple suppliers.
        Returns (deleted_count, deleted_suppliers, errors) tuple.
        """
        deleted_count = 0
        deleted_suppliers = []
        errors = []
        
        for supplier_id in supplier_ids:
            success, message = SupplierRepository.delete(supplier_id)
            if success:
                deleted_count += 1
                # Extract supplier code from success message
                if '"' in message:
                    supplier_code = message.split('"')[1]
                    deleted_suppliers.append(supplier_code)
            else:
                errors.append(f"Supplier ID {supplier_id}: {message}")
        
        return deleted_count, deleted_suppliers, errors
    
    @staticmethod
    def get_with_component_count() -> List[Dict[str, Any]]:
        """Get all suppliers with their component counts."""
        suppliers_with_counts = db.session.query(
            Supplier,
            func.count(Component.id).label('component_count')
        ).outerjoin(Component).group_by(Supplier.id).order_by(Supplier.supplier_code).all()
        
        result = []
        for supplier, component_count in suppliers_with_counts:
            result.append({
                'supplier': supplier,
                'component_count': component_count
            })
        
        return result
    
    @staticmethod
    def get_by_ids(supplier_ids: List[int]) -> List[Supplier]:
        """Get suppliers by list of IDs."""
        return Supplier.query.filter(Supplier.id.in_(supplier_ids)).all()
    
    @staticmethod
    def exists_by_code(supplier_code: str, exclude_id: int = None) -> bool:
        """Check if supplier code exists, optionally excluding a specific ID."""
        query = Supplier.query.filter_by(supplier_code=supplier_code)
        
        if exclude_id:
            query = query.filter(Supplier.id != exclude_id)
        
        return query.first() is not None
    
    @staticmethod
    def get_or_create_by_code(supplier_code: str, address: str = None) -> Tuple[Supplier, bool]:
        """
        Get or create supplier by code.
        Returns (supplier, created) tuple.
        """
        return get_or_create(
            Supplier,
            supplier_code=supplier_code,
            defaults={'address': address} if address else {}
        )