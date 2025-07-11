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
        # DEBUG: Log all received form data
        current_app.logger.info("=== API CREATE COMPONENT - RECEIVED FORM DATA ===")
        for key, value in request.form.items():
            current_app.logger.info(f"Form field: {key} = {value}")
        
        current_app.logger.info("=== API CREATE COMPONENT - RECEIVED FORM LISTS ===")
        for key in request.form.keys():
            if key.endswith('[]'):
                values = request.form.getlist(key)
                current_app.logger.info(f"Form list: {key} = {values}")
        
        # Get basic component data
        product_number = request.form.get('product_number', '').strip()
        description = request.form.get('description', '').strip()
        component_type_id = request.form.get('component_type_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int) if request.form.get('supplier_id') else None
        
        current_app.logger.info(f"Basic data: product_number={product_number}, component_type_id={component_type_id}, supplier_id={supplier_id}")
        
        # Validate required fields
        if not product_number:
            return jsonify({'success': False, 'error': 'Product number is required'}), 400
        if not component_type_id:
            return jsonify({'success': False, 'error': 'Component type is required'}), 400
        
        # Check for duplicate product number
        existing_query = Component.query.filter_by(product_number=product_number)
        if supplier_id:
            existing_query = existing_query.filter_by(supplier_id=supplier_id)
        else:
            existing_query = existing_query.filter(Component.supplier_id.is_(None))
        
        if existing_query.first():
            supplier_name = f" for supplier {supplier_id}" if supplier_id else " (no supplier)"
            return jsonify({
                'success': False, 
                'error': f'Product number "{product_number}" already exists{supplier_name}'
            }), 400
        
        # Create component
        component = Component(
            product_number=product_number,
            description=description,
            supplier_id=supplier_id,
            component_type_id=component_type_id,
            properties={}
        )
        
        db.session.add(component)
        db.session.flush()  # Get component ID
        
        # Handle all associations using service layer (proper MVC)
        from app.services.component_service import ComponentService
        
        # Create data dict for associations
        component_data = {
            'product_number': product_number,
            'description': description,
            'component_type_id': component_type_id,
            'supplier_id': supplier_id
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
        
        # Use service layer for associations
        ComponentService._handle_component_associations(component, component_data, is_edit=False)
        
        # Process variants
        created_variants = []
        variant_index = 1
        all_pending_files = []  # Track ALL files to save after DB commit
        
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
            
            # Handle custom color creation
            if custom_color_name:
                existing_color = Color.query.filter_by(name=custom_color_name).first()
                if existing_color:
                    color_id = existing_color.id
                else:
                    new_color = Color(name=custom_color_name)
                    db.session.add(new_color)
                    db.session.flush()
                    color_id = new_color.id
            
            if not color_id:
                variant_index += 1
                continue
            
            # Check if variant already exists for this color
            existing_variant = ComponentVariant.query.filter_by(
                component_id=component.id,
                color_id=color_id
            ).first()
            
            if existing_variant:
                current_app.logger.warning(f"Variant for color {color_id} already exists for component {component.id}")
                variant_index += 1
                continue
            
            # Create variant
            variant = ComponentVariant(
                component_id=component.id,
                color_id=color_id,
                is_active=True
            )
            
            db.session.add(variant)
            db.session.flush()  # Get variant ID
            
            # Handle variant pictures - prepare for atomic file operations
            variant_pictures = []
            uploaded_files = request.files.getlist(images_key)
            
            current_app.logger.info(f"Processing variant {variant_index}, images_key: {images_key}")
            current_app.logger.info(f"Found {len(uploaded_files)} files: {[f.filename for f in uploaded_files]}")
            
            if uploaded_files and any(f.filename for f in uploaded_files):
                picture_order = 1
                
                for picture_file in uploaded_files:
                    if picture_file and picture_file.filename and allowed_file(picture_file.filename):
                        try:
                            # Read file into memory for later processing
                            file_data = io.BytesIO(picture_file.read())
                            file_ext = os.path.splitext(picture_file.filename)[1].lower()
                            
                            # Create picture record (database trigger will generate picture_name)
                            current_app.logger.info(f"Creating picture: component_id={component.id}, variant_id={variant.id}, order={picture_order}")
                            
                            # Check if variant and color are properly loaded
                            db.session.refresh(variant)
                            db.session.refresh(component)
                            current_app.logger.info(f"Variant color check: variant.color={getattr(variant, 'color', 'NOT_LOADED')}")
                            current_app.logger.info(f"Component supplier check: component.supplier={getattr(component, 'supplier', 'NOT_LOADED')}")
                            
                            # Generate picture name using Python utility function (reliable and maintainable)
                            generated_name = generate_picture_name(component, variant, picture_order)
                            current_app.logger.info(f"Generated picture name: '{generated_name}'")
                            
                            if not generated_name:
                                current_app.logger.error(f"Failed to generate picture name for component {component.id}, variant {variant.id}, order {picture_order}")
                                continue
                            
                            picture = Picture(
                                component_id=component.id,
                                variant_id=variant.id,
                                picture_name=generated_name,  # Set directly instead of relying on trigger
                                url='',  # Will be set after files are saved
                                picture_order=picture_order,
                                alt_text=f"{component.product_number} - Image {picture_order}"
                            )
                            db.session.add(picture)
                            db.session.flush()  # Get picture ID
                            current_app.logger.info(f"Picture created: ID={picture.id}, name='{picture.picture_name}'")
                            
                            # Store file data for atomic save after DB commit
                            current_app.logger.info(f"Picture created with ID {picture.id}, name: '{picture.picture_name}', order: {picture.picture_order}")
                            if picture.picture_name:
                                filename = f"{picture.picture_name}{file_ext}"
                                webdav_prefix = current_app.config.get('UPLOAD_URL_PREFIX', 'http://31.182.67.115/webdav/components')
                                
                                current_app.logger.info(f"Preparing file for atomic save: {filename} -> {webdav_prefix}/{filename}")
                                all_pending_files.append({
                                    'picture': picture,
                                    'file_data': file_data,
                                    'filename': filename,
                                    'url': f"{webdav_prefix}/{filename}"
                                })
                                
                                # Add to variant pictures list for response
                                variant_pictures.append({
                                    'id': picture.id,
                                    'name': picture.picture_name,
                                    'url': f"{webdav_prefix}/{filename}",
                                    'order': picture.picture_order
                                })
                            else:
                                current_app.logger.error(f"Picture name is empty for picture ID {picture.id} - database trigger may have failed")
                            
                            picture_order += 1
                                
                        except Exception as e:
                            current_app.logger.error(f"Error preparing picture: {str(e)}")
                            continue
            
            # Add variant to created list
            color = Color.query.get(color_id)
            created_variants.append({
                'id': variant.id,
                'color_id': color_id,
                'color_name': color.name,
                'sku': variant.variant_sku or '',
                'pictures': variant_pictures
            })
            
            variant_index += 1
        
        # Commit database changes first
        current_app.logger.info(f"Committing database changes. Pending files to save: {len(all_pending_files)}")
        db.session.commit()
        
        # Now save all files atomically
        saved_files = []
        current_app.logger.info(f"Starting atomic file save for {len(all_pending_files)} files")
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
            current_app.logger.info(f"Upload folder: {upload_folder}")
            
            # Create upload directory if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)
            
            if not all_pending_files:
                current_app.logger.warning("No files to save - all_pending_files is empty!")
            
            for file_info in all_pending_files:
                file_path = os.path.join(upload_folder, file_info['filename'])
                
                # Save file to WebDAV
                file_info['file_data'].seek(0)
                with open(file_path, 'wb') as f:
                    f.write(file_info['file_data'].read())
                
                # Track saved file for potential cleanup
                saved_files.append(file_path)
                
                # Update picture URL in database - get fresh picture object from database
                picture_id = file_info['picture'].id
                picture = Picture.query.get(picture_id)
                if picture:
                    current_app.logger.info(f"Setting URL for picture {picture_id}: {file_info['url']}")
                    picture.url = file_info['url']
                    db.session.add(picture)
                else:
                    current_app.logger.error(f"Could not find picture with ID {picture_id}")
            
            # Commit URL updates
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error saving files: {str(e)}")
            
            # Cleanup any files that were saved
            for file_path in saved_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    current_app.logger.error(f"Error cleaning up file {file_path}: {cleanup_error}")
            
            # Rollback URL updates
            db.session.rollback()
            
            return jsonify({'success': False, 'error': f'Failed to save files: {str(e)}'}), 500
        
        # Integrate with web workflow: set up loading page session and background verification
        import time
        import threading
        
        component_id = component.id
        
        # Store creation completion in session for loading page status checking
        session[f'component_creation_{component_id}'] = {
            'status': 'verifying',
            'created_at': time.time()
        }
        
        # Start background verification (same as web route)
        def verify_in_background():
            try:
                # Import here to avoid circular imports
                from app.web.component_routes import _verify_images_accessible
                images_verified = _verify_images_accessible(component_id)
                session[f'component_creation_{component_id}'] = {
                    'status': 'ready' if images_verified else 'ready_with_warning',
                    'created_at': time.time(),
                    'verified': images_verified
                }
                current_app.logger.info(f"API: Background verification completed for component {component_id}: {images_verified}")
            except Exception as e:
                current_app.logger.error(f"API: Background verification failed for component {component_id}: {e}")
                session[f'component_creation_{component_id}'] = {
                    'status': 'ready_with_warning',
                    'created_at': time.time(),
                    'verified': False
                }
        
        verification_thread = threading.Thread(target=verify_in_background)
        verification_thread.daemon = True
        verification_thread.start()
        
        # Return redirect URL to integrate with loading page workflow
        loading_url = url_for('component_web.component_creation_loading', component_id=component_id)
        
        # Build summary of what was created
        from app.utils.association_handlers import get_association_counts
        association_counts = get_association_counts(component)
        
        current_app.logger.info(f"Component {component.id} created with: {len(created_variants)} variants, {association_counts['brands_count']} brands, {association_counts['categories_count']} categories, {association_counts['keywords_count']} keywords, {association_counts['properties_count']} properties")
        
        return jsonify({
            'success': True,
            'redirect_url': loading_url,
            'message': f'Component created with {len(created_variants)} variants, {association_counts["brands_count"]} brands, {association_counts["categories_count"]} categories, {association_counts["keywords_count"]} keywords',
            'component': {
                'id': component.id,
                'product_number': component.product_number,
                'variants_count': len(created_variants),
                **association_counts
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating component with variants: {str(e)}")
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
        component_data = ComponentService.get_component_for_edit(component_id)
        
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
        result = ComponentService.delete_component(component_id)
        
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
        result = ComponentService.update_component(component_id, data)
        
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