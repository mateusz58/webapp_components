"""Supplier web routes."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import db
from app.models import Supplier, Component
from app.utils.response import WebResponse
from app.utils.validators import validate_data, supplier_code_validator, description_validator
from app.utils.database import safe_commit, safe_delete
from flask import current_app

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')
# Additional blueprint for /suppliers route without prefix
suppliers_bp = Blueprint('suppliers', __name__)


@supplier_bp.route('s')
def suppliers():
    """Display all suppliers with their statistics."""
    try:
        # Get sorting parameter
        sort_by = request.args.get('sort', 'code')
        
        # Build query with sorting
        query = Supplier.query
        
        if sort_by == 'name':
            query = query.order_by(Supplier.supplier_code)
        elif sort_by == 'components':
            # Sort by component count (requires a subquery)
            query = query.outerjoin(Component).group_by(Supplier.id).order_by(
                db.func.count(Component.id).desc()
            )
        elif sort_by == 'created':
            query = query.order_by(Supplier.created_at.desc())
        else:  # default to code
            query = query.order_by(Supplier.supplier_code)
        
        suppliers = query.all()
        
        # Prepare suppliers data for JavaScript
        suppliers_data = []
        for supplier in suppliers:
            supplier_dict = {
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'address': supplier.address,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
                'components': [{'id': c.id, 'product_number': c.product_number} for c in supplier.components]
            }
            suppliers_data.append(supplier_dict)
        
        return render_template('suppliers.html', 
                             suppliers=suppliers,
                             suppliers_data=suppliers_data,
                             sort_by=sort_by)
        
    except Exception as e:
        current_app.logger.error(f"Error loading suppliers: {str(e)}")
        flash('Error loading suppliers. Please try again.', 'error')
        return render_template('suppliers.html', suppliers=[], suppliers_data=[])


@supplier_bp.route('/new', methods=['GET', 'POST'])
def new_supplier():
    """Add a new supplier."""
    if request.method == 'POST':
        try:
            # Validate form data
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
            
            # Check if supplier code already exists
            existing = Supplier.query.filter_by(
                supplier_code=validated_data['supplier_code']
            ).first()
            
            if existing:
                flash(f'Supplier with code "{validated_data["supplier_code"]}" already exists.', 'error')
                return render_template('supplier_form.html')
            
            # Create new supplier
            supplier = Supplier(
                supplier_code=validated_data['supplier_code'],
                address=validated_data['address'] if validated_data['address'] else None
            )
            
            db.session.add(supplier)
            
            if safe_commit():
                return WebResponse.success_redirect(
                    f'Supplier "{supplier.supplier_code}" created successfully.',
                    'supplier.suppliers'
                )
            else:
                flash('Error creating supplier. Please try again.', 'error')
                return render_template('supplier_form.html')
                
        except Exception as e:
            current_app.logger.error(f"Error creating supplier: {str(e)}")
            flash('Error creating supplier. Please check your input and try again.', 'error')
            return render_template('supplier_form.html')
    
    # GET request - show form
    return render_template('supplier_form.html')


@supplier_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    """Edit an existing supplier."""
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validate form data
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
                Supplier.id != id
            ).first()
            
            if existing:
                flash(f'Supplier with code "{validated_data["supplier_code"]}" already exists.', 'error')
                return render_template('supplier_form.html', supplier=supplier)
            
            # Update supplier
            supplier.supplier_code = validated_data['supplier_code']
            supplier.address = validated_data['address'] if validated_data['address'] else None
            
            if safe_commit():
                return WebResponse.success_redirect(
                    f'Supplier "{supplier.supplier_code}" updated successfully.',
                    'supplier.suppliers'
                )
            else:
                flash('Error updating supplier. Please try again.', 'error')
                return render_template('supplier_form.html', supplier=supplier)
                
        except Exception as e:
            current_app.logger.error(f"Error updating supplier {id}: {str(e)}")
            flash('Error updating supplier. Please check your input and try again.', 'error')
            return render_template('supplier_form.html', supplier=supplier)
    
    # GET request - show form
    return render_template('supplier_form.html', supplier=supplier)


@supplier_bp.route('/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    """Delete a supplier."""
    supplier = Supplier.query.get_or_404(id)
    
    try:
        # Check if supplier has associated components
        component_count = Component.query.filter_by(supplier_id=id).count()
        
        if component_count > 0:
            flash(
                f'Cannot delete supplier "{supplier.supplier_code}" because it has '
                f'{component_count} associated component(s). Please remove or reassign '
                f'the components first.',
                'error'
            )
            return redirect(url_for('supplier.suppliers'))
        
        # Safe to delete
        supplier_code = supplier.supplier_code
        
        if safe_delete(supplier):
            return WebResponse.success_redirect(
                f'Supplier "{supplier_code}" deleted successfully.',
                'supplier.suppliers'
            )
        else:
            flash('Error deleting supplier. Please try again.', 'error')
            return redirect(url_for('supplier.suppliers'))
            
    except Exception as e:
        current_app.logger.error(f"Error deleting supplier {id}: {str(e)}")
        return WebResponse.error_redirect(
            'Error deleting supplier. Please try again.',
            'supplier.suppliers'
        )


# Route for /suppliers (without prefix)
@suppliers_bp.route('/suppliers')
def suppliers_main():
    """Display all suppliers - main route."""
    return suppliers()