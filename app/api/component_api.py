from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from app import db
from app.models import Component, ComponentType, Supplier, Category, Brand, ComponentBrand, Picture, ComponentVariant, Keyword, keyword_component
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
import io
import csv
import os
from datetime import datetime

component_api = Blueprint('component_api', __name__)


@component_api.route('/components/search')
def search_components():
    """
    API endpoint for searching components with autocomplete support
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'results': []})
        
        # Search for components
        components = Component.query.filter(
            or_(
                Component.product_number.ilike(f'%{query}%'),
                Component.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        results = []
        for comp in components:
            # Get the first brand if available
            first_brand = None
            if comp.brands:
                first_brand = comp.brands[0].name
            
            results.append({
                'id': comp.id,
                'product_number': comp.product_number,
                'description': comp.description or '',
                'supplier': comp.supplier.supplier_code if comp.supplier else 'No Supplier',
                'brand': first_brand or 'No Brand',
                'type': comp.component_type.name if comp.component_type else 'Unknown'
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        current_app.logger.error(f"Component search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500


@component_api.route('/components/<int:component_id>/duplicate', methods=['POST'])
def duplicate_component(component_id):
    """
    API endpoint to duplicate a component
    """
    try:
        # Find the original component
        original = Component.query.get_or_404(component_id)
        
        # Create a new component with copied data
        new_component = Component(
            product_number=f"{original.product_number}_copy_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            description=f"Copy of {original.description}" if original.description else "Copy",
            supplier_id=original.supplier_id,
            component_type_id=original.component_type_id,
            properties=original.properties.copy() if original.properties else {},
            proto_status='pending',
            sms_status='pending',
            pps_status='pending'
        )
        
        db.session.add(new_component)
        db.session.flush()  # Get the new component ID
        
        # Copy categories
        for category in original.categories:
            new_component.categories.append(category)
        
        # Copy brand associations
        for brand_assoc in original.brand_associations:
            new_brand_assoc = ComponentBrand(
                component_id=new_component.id,
                brand_id=brand_assoc.brand_id
            )
            db.session.add(new_brand_assoc)
        
        # Copy keywords
        for keyword in original.keywords:
            db.session.execute(
                keyword_component.insert().values(
                    component_id=new_component.id,
                    keyword_id=keyword.id
                )
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Component duplicated successfully',
            'new_component_id': new_component.id,
            'new_product_number': new_component.product_number
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Component duplication error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@component_api.route('/components/<int:component_id>/export')
def export_component(component_id):
    """
    Export single component data as CSV
    """
    try:
        component = Component.query.get_or_404(component_id)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['Product Number', 'Description', 'Supplier', 'Category', 'Type', 
                  'Proto Status', 'SMS Status', 'PPS Status', 'Created', 'Updated']
        
        # Add dynamic property headers
        if component.properties:
            headers.extend(component.properties.keys())
        
        writer.writerow(headers)
        
        # Write component data
        row = [
            component.product_number,
            component.description or '',
            component.supplier.supplier_code if component.supplier else '',
            component.category.name if component.category else '',
            component.component_type.name if component.component_type else '',
            component.proto_status or '',
            component.sms_status or '',
            component.pps_status or '',
            component.created_at.strftime('%Y-%m-%d %H:%M') if component.created_at else '',
            component.updated_at.strftime('%Y-%m-%d %H:%M') if component.updated_at else ''
        ]
        
        # Add property values
        if component.properties:
            row.extend(component.properties.values())
        
        writer.writerow(row)
        
        # Create response
        output.seek(0)
        response = current_app.response_class(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=component_{component.product_number}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Component export error: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


@component_api.route('/components/bulk-delete', methods=['POST'])
def bulk_delete_components():
    """
    Bulk delete components
    """
    try:
        data = request.get_json()
        component_ids = data.get('component_ids', [])
        
        if not component_ids:
            return jsonify({'success': False, 'error': 'No components selected'}), 400
        
        # Delete components
        deleted_count = 0
        errors = []
        
        for comp_id in component_ids:
            try:
                component = Component.query.get(comp_id)
                if component:
                    # Delete associated pictures
                    for picture in component.pictures:
                        if picture.url and os.path.exists(os.path.join(current_app.static_folder, picture.url.lstrip('/'))):
                            try:
                                os.remove(os.path.join(current_app.static_folder, picture.url.lstrip('/')))
                            except OSError:
                                pass
                    
                    db.session.delete(component)
                    deleted_count += 1
                
            except Exception as e:
                errors.append(f"Error deleting component {comp_id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} components',
            'deleted_count': deleted_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk delete error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@component_api.route('/components/export')
def export_components():
    """
    Export filtered components as CSV
    """
    try:
        # Get filter parameters (same as index route)
        search = request.args.get('search', '', type=str).strip()
        component_type_ids = request.args.getlist('component_type_id')
        component_type_ids = [int(id) for id in component_type_ids if id.isdigit()]
        supplier_ids = request.args.getlist('supplier_id')
        supplier_ids = [int(id) for id in supplier_ids if id.isdigit()]
        brand_ids = request.args.getlist('brand_id')
        brand_ids = [int(id) for id in brand_ids if id.isdigit()]
        status = request.args.get('status', type=str)
        
        # Build query
        query = Component.query.options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.category),
            joinedload(Component.brands)
        )
        
        # Apply filters
        filters = []
        
        if search:
            filters.append(or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%')
            ))
        
        if component_type_ids:
            filters.append(Component.component_type_id.in_(component_type_ids))
        
        if supplier_ids:
            filters.append(Component.supplier_id.in_(supplier_ids))
        
        if brand_ids:
            brand_components_subquery = db.session.query(ComponentBrand.component_id).filter(
                ComponentBrand.brand_id.in_(brand_ids)
            ).subquery()
            filters.append(Component.id.in_(brand_components_subquery))
        
        if status:
            if status == 'approved':
                filters.append(and_(
                    Component.proto_status == 'ok',
                    Component.sms_status == 'ok',
                    Component.pps_status == 'ok'
                ))
            elif status == 'pending':
                filters.append(or_(
                    Component.proto_status == 'pending',
                    Component.sms_status == 'pending',
                    Component.pps_status == 'pending'
                ))
        
        if filters:
            query = query.filter(and_(*filters))
        
        components = query.all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Product Number', 'Description', 'Supplier', 'Category', 'Type', 
                        'Brands', 'Proto Status', 'SMS Status', 'PPS Status', 'Created', 'Updated'])
        
        # Write data
        for comp in components:
            brands = ', '.join([b.name for b in comp.brands])
            writer.writerow([
                comp.product_number,
                comp.description or '',
                comp.supplier.supplier_code if comp.supplier else '',
                comp.category.name if comp.category else '',
                comp.component_type.name if comp.component_type else '',
                brands,
                comp.proto_status or '',
                comp.sms_status or '',
                comp.pps_status or '',
                comp.created_at.strftime('%Y-%m-%d %H:%M') if comp.created_at else '',
                comp.updated_at.strftime('%Y-%m-%d %H:%M') if comp.updated_at else ''
            ])
        
        # Create response
        output.seek(0)
        response = current_app.response_class(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=components_export_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Components export error: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


@component_api.route('/components/<int:component_id>/brands', methods=['GET', 'POST', 'DELETE'])
def manage_component_brands(component_id):
    """
    Manage component-brand associations
    """
    try:
        component = Component.query.get_or_404(component_id)
        
        if request.method == 'GET':
            # Get current brands
            brands = [{
                'id': cb.brand.id,
                'name': cb.brand.name,
                'created_at': cb.created_at.isoformat() if cb.created_at else None
            } for cb in component.component_brands]
            
            return jsonify({'success': True, 'brands': brands})
        
        elif request.method == 'POST':
            # Add brand association
            data = request.get_json()
            brand_id = data.get('brand_id')
            
            if not brand_id:
                return jsonify({'success': False, 'error': 'Brand ID required'}), 400
            
            # Check if association already exists
            existing = ComponentBrand.query.filter_by(
                component_id=component_id,
                brand_id=brand_id
            ).first()
            
            if existing:
                return jsonify({'success': False, 'error': 'Brand already associated'}), 400
            
            # Create new association
            new_assoc = ComponentBrand(
                component_id=component_id,
                brand_id=brand_id
            )
            db.session.add(new_assoc)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Brand associated successfully'})
        
        elif request.method == 'DELETE':
            # Remove brand association
            data = request.get_json()
            brand_id = data.get('brand_id')
            
            if not brand_id:
                return jsonify({'success': False, 'error': 'Brand ID required'}), 400
            
            # Find and delete association
            assoc = ComponentBrand.query.filter_by(
                component_id=component_id,
                brand_id=brand_id
            ).first()
            
            if not assoc:
                return jsonify({'success': False, 'error': 'Association not found'}), 404
            
            db.session.delete(assoc)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Brand association removed'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Component brand management error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500