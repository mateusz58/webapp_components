"""Supplier API routes."""

import os
import tempfile
from flask import Blueprint, request, jsonify, current_app, send_file
from app import db
from app.models import Supplier, Component
from app.utils.response import ApiResponse
from app.utils.validators import validate_data, supplier_code_validator, description_validator
from app.utils.database import safe_commit, safe_delete, safe_bulk_delete
from app.services.csv_service import CSVProcessingService

supplier_api_bp = Blueprint('supplier_api', __name__, url_prefix='/api/suppliers')


@supplier_api_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update a supplier via API."""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    try:
        # Get form data (handles both JSON and form-data)
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = {
                'supplier_code': request.form.get('supplier_code', '').strip(),
                'address': request.form.get('address', '').strip()
            }
        
        # Define validation rules
        validation_rules = {
            'supplier_code': supplier_code_validator,
            'address': description_validator
        }
        
        # Validate data
        validated_data = validate_data(form_data, validation_rules)
        
        # Check if supplier code already exists (excluding current supplier)
        existing = Supplier.query.filter(
            Supplier.supplier_code == validated_data['supplier_code'],
            Supplier.id != supplier_id
        ).first()
        
        if existing:
            return ApiResponse.validation_error({
                'supplier_code': f'Supplier with code "{validated_data["supplier_code"]}" already exists.'
            })
        
        # Update supplier
        supplier.supplier_code = validated_data['supplier_code']
        supplier.address = validated_data['address'] if validated_data['address'] else None
        
        if safe_commit():
            return ApiResponse.success(
                data={
                    'id': supplier.id,
                    'supplier_code': supplier.supplier_code,
                    'address': supplier.address,
                    'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None
                },
                message=f'Supplier "{supplier.supplier_code}" updated successfully.'
            )
        else:
            return ApiResponse.server_error('Failed to update supplier.')
            
    except Exception as e:
        current_app.logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
        return ApiResponse.server_error('Error updating supplier.')


@supplier_api_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier via API."""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    try:
        # Check if supplier has associated components
        component_count = Component.query.filter_by(supplier_id=supplier_id).count()
        
        if component_count > 0:
            return ApiResponse.error(
                message=f'Cannot delete supplier because it has {component_count} associated component(s).',
                status_code=409
            )
        
        # Safe to delete
        supplier_code = supplier.supplier_code
        
        if safe_delete(supplier):
            return ApiResponse.success(
                message=f'Supplier "{supplier_code}" deleted successfully.'
            )
        else:
            return ApiResponse.server_error('Failed to delete supplier.')
            
    except Exception as e:
        current_app.logger.error(f"Error deleting supplier {supplier_id}: {str(e)}")
        return ApiResponse.server_error('Error deleting supplier.')


@supplier_api_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete_suppliers():
    """Delete multiple suppliers via API."""
    try:
        data = request.get_json()
        supplier_ids = data.get('ids', [])
        
        if not supplier_ids:
            return ApiResponse.validation_error({'ids': 'Supplier IDs are required.'})
        
        # Validate that all IDs are integers
        try:
            supplier_ids = [int(id) for id in supplier_ids]
        except (ValueError, TypeError):
            return ApiResponse.validation_error({'ids': 'All supplier IDs must be valid integers.'})
        
        # Get suppliers and check for associated components
        suppliers = Supplier.query.filter(Supplier.id.in_(supplier_ids)).all()
        
        if len(suppliers) != len(supplier_ids):
            return ApiResponse.not_found('One or more suppliers not found.')
        
        # Check for components
        suppliers_with_components = []
        for supplier in suppliers:
            component_count = Component.query.filter_by(supplier_id=supplier.id).count()
            if component_count > 0:
                suppliers_with_components.append({
                    'supplier_code': supplier.supplier_code,
                    'component_count': component_count
                })
        
        if suppliers_with_components:
            return ApiResponse.error(
                message='Cannot delete suppliers with associated components.',
                errors={'suppliers_with_components': suppliers_with_components},
                status_code=409
            )
        
        # Safe to delete all
        deleted_count = 0
        deleted_suppliers = []
        
        for supplier in suppliers:
            if safe_delete(supplier):
                deleted_count += 1
                deleted_suppliers.append(supplier.supplier_code)
        
        return ApiResponse.success(
            data={
                'deleted_count': deleted_count,
                'deleted_suppliers': deleted_suppliers
            },
            message=f'Successfully deleted {deleted_count} supplier(s).'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in bulk delete: {str(e)}")
        return ApiResponse.server_error('Error deleting suppliers.')


@supplier_api_bp.route('/export', methods=['GET'])
def export_suppliers():
    """Export suppliers to CSV file."""
    try:
        # Get optional supplier IDs from query params
        supplier_ids = request.args.getlist('ids')
        
        # Build query
        query = Supplier.query
        if supplier_ids:
            try:
                supplier_ids = [int(id) for id in supplier_ids]
                query = query.filter(Supplier.id.in_(supplier_ids))
            except (ValueError, TypeError):
                return ApiResponse.validation_error({'ids': 'Invalid supplier IDs.'})
        
        suppliers = query.all()
        
        if not suppliers:
            return ApiResponse.not_found('No suppliers found to export.')
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        
        try:
            # Write CSV data
            import csv
            with open(temp_file.name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Write header
                writer.writerow([
                    'supplier_code', 'address', 'component_count', 
                    'created_at', 'updated_at'
                ])
                
                # Write data
                for supplier in suppliers:
                    writer.writerow([
                        supplier.supplier_code,
                        supplier.address or '',
                        len(supplier.components),
                        supplier.created_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.created_at else '',
                        supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.updated_at else ''
                    ])
            
            # Generate filename
            filename = f"suppliers_export_{len(suppliers)}_items.csv"
            
            # Send file
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_file.name)
            except:
                pass
            raise e
            
    except Exception as e:
        current_app.logger.error(f"Error exporting suppliers: {str(e)}")
        return ApiResponse.server_error('Error exporting suppliers.')


@supplier_api_bp.route('/search', methods=['GET'])
def search_suppliers():
    """Search suppliers by code or address."""
    try:
        query_param = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        if not query_param:
            return ApiResponse.validation_error({'q': 'Search query is required.'})
        
        # Build search query
        search_query = Supplier.query.filter(
            db.or_(
                Supplier.supplier_code.ilike(f'%{query_param}%'),
                Supplier.address.ilike(f'%{query_param}%')
            )
        ).order_by(Supplier.supplier_code)
        
        # Paginate results
        pagination = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format results
        suppliers_data = []
        for supplier in pagination.items:
            suppliers_data.append({
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'address': supplier.address,
                'component_count': len(supplier.components),
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None
            })
        
        return ApiResponse.success(
            data={
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
        )
        
    except Exception as e:
        current_app.logger.error(f"Error searching suppliers: {str(e)}")
        return ApiResponse.server_error('Error searching suppliers.')