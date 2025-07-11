from flask import Blueprint, request, jsonify, current_app, send_file, session, url_for
from werkzeug.utils import secure_filename
from app import db, csrf
from app.models import Component, ComponentType, Supplier, Category, Brand, ComponentBrand, Picture, ComponentVariant, Keyword, keyword_component, Color, ComponentTypeProperty
from app.utils.file_handling import save_uploaded_file, allowed_file, generate_picture_name
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload, selectinload
import io
import csv
import os
import json
from datetime import datetime

component_api = Blueprint('component_api', __name__)


@component_api.route('/component/create', methods=['POST'])
def create_component():
    """
    Create a component with variants and pictures in a single API call
    Handles multipart form data with component details, variants, and file uploads
    """
    try:
        # Use service layer for all component operations
        from app.services.component_service import ComponentService
        service = ComponentService()
        
        # DEBUG: Log all received form data
        current_app.logger.info("=== API CREATE COMPONENT - RECEIVED FORM DATA ===")
        for key, value in request.form.items():
            current_app.logger.info(f"Form field: {key} = {value}")
        
        # Create data dict for component creation
        component_data = {
            'product_number': request.form.get('product_number', '').strip(),
            'description': request.form.get('description', '').strip(),
            'component_type_id': request.form.get('component_type_id', type=int),
            'supplier_id': request.form.get('supplier_id', type=int) if request.form.get('supplier_id') else None
        }
        
        # Add brand data from form/json
        if request.is_json:
            json_data = request.get_json()
            component_data.update(json_data)
        else:
            # Handle form data for brands
            brand_ids = request.form.getlist('brand_ids[]') or [request.form.get('brand_id')] if request.form.get('brand_id') else []
            if brand_ids:
                component_data['brand_ids'] = [id for id in brand_ids if id]
            
            new_brand_name = request.form.get('new_brand_name', '').strip()
            if new_brand_name:
                component_data['new_brand_name'] = new_brand_name
            
            # Handle form data for categories
            category_ids = request.form.getlist('category_ids[]') or request.form.getlist('category_ids') or request.form.getlist('categories[]') or request.form.getlist('selected_categories[]')
            if category_ids:
                component_data['category_ids'] = [id for id in category_ids if id]
            
            # Handle form data for keywords
            keywords_input = request.form.get('keywords', '').strip()
            if keywords_input:
                component_data['keywords'] = keywords_input
        
        # Collect variant data from form
        variants_data = []
        variant_index = 1
        
        # Look for variant data in form (variant_color_1, variant_color_2, etc.)
        while True:
            color_key = f'variant_color_{variant_index}'
            custom_color_key = f'variant_custom_color_{variant_index}'
            images_key = f'variant_images_{variant_index}[]'
            
            color_id = request.form.get(color_key, type=int)
            custom_color_name = request.form.get(custom_color_key, '').strip()
            
            # If no color data found, try new_ prefixed variants
            if not color_id and not custom_color_name:
                color_key = f'variant_color_new_{variant_index}'
                custom_color_key = f'variant_custom_color_new_{variant_index}'
                images_key = f'variant_images_new_{variant_index}[]'
                
                color_id = request.form.get(color_key, type=int)
                custom_color_name = request.form.get(custom_color_key, '').strip()
            
            # If still no color data, break the loop
            if not color_id and not custom_color_name:
                break
            
            # Collect variant data with images
            variant_dict = {
                'color_id': color_id,
                'custom_color_name': custom_color_name,
                'images': request.files.getlist(images_key)
            }
            variants_data.append(variant_dict)
            variant_index += 1
        
        # Add variants to component data if any
        if variants_data:
            component_data['variants'] = variants_data
        
        # Use service to create component with all associations and variants
        result = service.create_component(component_data, request.files)
        
        # Set up loading page session and background verification
        import time
        import threading
        
        component_id = result['component']['id']
        
        # Store creation completion in session for loading page status checking
        session[f'component_creation_{component_id}'] = {
            'status': 'verifying',
            'created_at': time.time()
        }
        
        # Start background verification
        app = current_app._get_current_object()
        
        def verify_in_background():
            with app.app_context():
                try:
                    from app.web.component_routes import _verify_images_accessible
                    images_verified = _verify_images_accessible(component_id)
                    current_app.logger.info(f"API: Background verification completed for component {component_id}: {images_verified}")
                except Exception as e:
                    current_app.logger.error(f"API: Background verification failed for component {component_id}: {e}")
        
        verification_thread = threading.Thread(target=verify_in_background)
        verification_thread.daemon = True
        verification_thread.start()
        
        # Add redirect URL to result
        result['redirect_url'] = url_for('component_web.component_creation_loading', component_id=component_id)
        
        return jsonify(result)
        
    except ValueError as e:
        current_app.logger.error(f"Validation error creating component: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
        
    except Exception as e:
        current_app.logger.error(f"Error creating component: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        # Use service layer for duplication
        from app.services.component_service import ComponentService
        service = ComponentService()
        
        result = service.duplicate_component(component_id)
        
        return jsonify(result)
        
    except ValueError as e:
        current_app.logger.error(f"Component duplication validation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
        
    except Exception as e:
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
    Bulk delete components using service layer
    """
    try:
        data = request.get_json()
        component_ids = data.get('component_ids', [])
        
        if not component_ids:
            return jsonify({'success': False, 'error': 'No components selected'}), 400
        
        # Use service layer for bulk deletion
        from app.services.component_service import ComponentService
        service = ComponentService()
        
        result = service.bulk_delete_components(component_ids)
        
        return jsonify(result)
        
    except Exception as e:
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


@component_api.route('/components/<int:component_id>/variants')
def get_component_variants(component_id):
    """
    API endpoint to get fresh variant data with pictures
    Addresses picture visibility issue by providing fresh data via AJAX
    """
    try:
        # Clear session cache to ensure fresh data
        db.session.expunge_all()
        
        # Query component with variants and pictures
        component = Component.query.options(
            joinedload(Component.variants).joinedload(ComponentVariant.color),
            joinedload(Component.variants).joinedload(ComponentVariant.variant_pictures),
            joinedload(Component.pictures)
        ).get_or_404(component_id)
        
        # Explicitly refresh variant data to ensure pictures are loaded
        for variant in component.variants:
            db.session.refresh(variant)
            for picture in variant.variant_pictures:
                db.session.refresh(picture)
        
        # Format variant data for frontend
        variants_data = []
        for variant in component.variants:
            variant_images = []
            for picture in variant.variant_pictures:
                variant_images.append({
                    'id': picture.id,
                    'name': picture.picture_name,
                    'url': picture.url,
                    'order': picture.picture_order,
                    'altText': picture.alt_text or ""
                })
            
            # Sort images by order
            variant_images.sort(key=lambda x: x['order'])
            
            variants_data.append({
                'id': variant.id,
                'name': variant.get_color_display_name(),
                'colorName': variant.color.name,
                'colorHex': "#ccc",
                'sku': variant.variant_sku or "",
                'images': variant_images
            })
        
        # Also include component images
        component_images = []
        for picture in component.pictures:
            component_images.append({
                'id': picture.id,
                'name': picture.picture_name,
                'url': picture.url,
                'order': picture.picture_order
            })
        
        component_images.sort(key=lambda x: x['order'])
        
        return jsonify({
            'success': True,
            'component_id': component_id,
            'variants': variants_data,
            'component_images': component_images,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting component variants: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@component_api.route('/components/<int:component_id>/edit-data')
def get_component_edit_data(component_id):
    """
    API endpoint to load complete component data for editing using service layer
    """
    try:
        # Use service layer for business logic
        from app.services.component_service import ComponentService
        service = ComponentService()
        component_data = service.get_component_for_edit(component_id)
        
        return jsonify({
            'success': True,
            'component': component_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        current_app.logger.error(f"Component not found: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404
        
    except Exception as e:
        current_app.logger.error(f"Error getting component edit data: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load component data'}), 500


@component_api.route('/component/<int:component_id>', methods=['DELETE'])
def delete_component_api(component_id):
    """
    Delete a component via API using service layer
    
    Following proper architecture with service layer separation
    """
    try:
        current_app.logger.info(f"=== API DELETE COMPONENT {component_id} ===")
        
        # Use service layer for business logic
        from app.services.component_service import ComponentService
        service = ComponentService()
        result = service.delete_component(component_id)
        
        # Return success response with timestamp
        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200
        
    except ValueError as e:
        error_message = str(e)
        current_app.logger.error(f"Validation error deleting component {component_id}: {error_message}")
        
        # Check if it's a "not found" error
        if 'not found' in error_message.lower():
            return jsonify({
                'success': False,
                'error': error_message,
                'code': 'NOT_FOUND'
            }), 404
        
        # Otherwise it's a validation error
        return jsonify({
            'success': False,
            'error': error_message,
            'code': 'VALIDATION_ERROR'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Error deleting component {component_id}: {str(e)}")
        current_app.logger.error(f"Full traceback: ", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Internal server error while deleting component: {str(e)}',
            'code': 'DELETE_ERROR'
        }), 500


@component_api.route('/component/<int:component_id>', methods=['PUT'])
def update_component(component_id):
    """
    Update an existing component via API using service layer
    
    Following proper architecture with service layer separation
    """
    try:
        current_app.logger.info(f"=== API UPDATE COMPONENT {component_id} ===")
        
        # Get data from request
        if request.is_json:
            data = request.get_json()
            current_app.logger.info(f"JSON data received: {data}")
        else:
            data = request.form.to_dict()
            current_app.logger.info(f"Form data received: {data}")
        
        # Log all data keys for debugging
        current_app.logger.info(f"Data keys received: {list(data.keys())}")
        
        # Handle array fields that might come as 'field[]' from JavaScript
        array_fields = ['brand_ids', 'category_ids', 'keywords']
        for field in array_fields:
            if f'{field}[]' in data:
                data[field] = data.pop(f'{field}[]')
                current_app.logger.info(f"Renamed {field}[] to {field}: {data[field]}")
        
        # Parse properties if it's a string (JSON)
        if 'properties' in data and isinstance(data['properties'], str):
            try:
                data['properties'] = json.loads(data['properties'])
                current_app.logger.info(f"Parsed properties from JSON string: {data['properties']}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to parse properties JSON: {e}")
        
        # Use service layer for business logic
        from app.services.component_service import ComponentService
        service = ComponentService()
        result = service.update_component(component_id, data)
        
        # Return success response with timestamp
        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200
        
    except ValueError as e:
        error_message = str(e)
        current_app.logger.error(f"Validation error updating component {component_id}: {error_message}")
        current_app.logger.error(f"Full traceback: ", exc_info=True)
        
        # Check if it's a "not found" error
        if 'not found' in error_message.lower():
            return jsonify({
                'success': False,
                'error': error_message,
                'code': 'NOT_FOUND'
            }), 404
        
        # Otherwise it's a validation error
        return jsonify({
            'success': False,
            'error': error_message,
            'code': 'VALIDATION_ERROR'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Error updating component {component_id}: {str(e)}")
        current_app.logger.error(f"Full traceback: ", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Internal server error while updating component: {str(e)}',
            'code': 'UPDATE_ERROR'
        }), 500