"""
Component Service Layer
Centralized business logic for component management operations with WebDAV integration
Used by both API endpoints and web routes to ensure consistency
Demo change for hook testing
"""
from flask import current_app
from app import db
from app.models import Component, ComponentVariant, ComponentType, Supplier, Color, Picture, ComponentBrand
from app.utils.association_handlers import (
    handle_brand_associations, 
    handle_categories, 
    handle_keywords,
    handle_component_properties,
    get_association_counts
)
from app.utils.file_handling import allowed_file
from app.services.webdav_config_service import WebDAVConfigService
from app.services.interfaces import IFileStorageService
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_
import time
import os
import io


class ComponentService:
    """Service class for component business logic with WebDAV picture management"""
    
    def __init__(self, storage_service: IFileStorageService = None):
        """
        Initialize ComponentService with WebDAV storage.
        
        Args:
            storage_service: Optional storage service for dependency injection
        """
        if storage_service:
            self._storage_service = storage_service
        else:
            # Try to get WebDAV configuration from database, fallback to direct config
            try:
                webdav_config_service = WebDAVConfigService()
                self._storage_service = webdav_config_service.get_storage_service('components_storage')
            except Exception as e:
                current_app.logger.warning(f"Could not get WebDAV config from database: {e}")
                # Fallback to direct configuration using values from config.py
                from app.services.webdav_storage_service import WebDAVStorageService, WebDAVStorageConfig
                
                storage_config = WebDAVStorageConfig(
                    base_url=current_app.config.get('WEBDAV_BASE_URL', 'http://31.182.67.115/webdav/components'),
                    timeout=30,
                    verify_ssl=False,
                    max_retries=3
                )
                
                self._storage_service = WebDAVStorageService(storage_config)
    
    @property
    def storage_service(self) -> IFileStorageService:
        """Get the WebDAV storage service"""
        return self._storage_service
    
    def upload_picture_to_webdav(self, file_data, filename, content_type='image/jpeg'):
        """
        Upload a picture to WebDAV storage.
        
        Args:
            file_data: Binary file data
            filename: Target filename
            content_type: MIME type
            
        Returns:
            dict: Upload result with success status and URL
        """
        try:
            result = self._storage_service.upload_file(file_data, filename, content_type)
            
            if result.success:
                return {
                    'success': True,
                    'url': result.file_info.url,
                    'filename': filename,
                    'message': f'File {filename} uploaded successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.message,
                    'filename': filename
                }
        except Exception as e:
            current_app.logger.error(f"WebDAV upload failed for {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }

    def delete_picture_from_webdav(self, filename):
        """
        Delete a picture from WebDAV storage.
        
        Args:
            filename: Filename to delete
            
        Returns:
            dict: Deletion result
        """
        try:
            # Extract filename from URL if needed
            if filename.startswith('http'):
                filename = filename.split('/')[-1]
            
            result = self._storage_service.delete_file(filename)
            
            return {
                'success': result.success,
                'message': result.message,
                'filename': filename
            }
        except Exception as e:
            current_app.logger.error(f"WebDAV delete failed for {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }

    def move_picture_in_webdav(self, old_filename, new_filename):
        """
        Move/rename a picture in WebDAV storage.
        
        Args:
            old_filename: Current filename
            new_filename: New filename
            
        Returns:
            dict: Move result
        """
        try:
            # Extract filenames from URLs if needed
            if old_filename.startswith('http'):
                old_filename = old_filename.split('/')[-1]
            if new_filename.startswith('http'):
                new_filename = new_filename.split('/')[-1]
            
            result = self._storage_service.move_file(old_filename, new_filename)
            
            if result.success:
                return {
                    'success': True,
                    'new_url': result.file_info.url,
                    'old_filename': old_filename,
                    'new_filename': new_filename
                }
            else:
                return {
                    'success': False,
                    'error': result.message,
                    'old_filename': old_filename,
                    'new_filename': new_filename
                }
        except Exception as e:
            current_app.logger.error(f"WebDAV move failed from {old_filename} to {new_filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'old_filename': old_filename,
                'new_filename': new_filename
            }

    def create_component(self, data, files=None):
        """
        Create a new component with all associations
        
        Args:
            data: Dict containing component data (from form or JSON)
            files: Optional file data for pictures
            
        Returns:
            dict: Result with component info and status
        """
        try:
            current_app.logger.info(f"ComponentService.create_component called with data: {list(data.keys())}")
            
            # Validate required fields
            if not data.get('product_number'):
                raise ValueError('Product number is required')
            if not data.get('component_type_id'):
                raise ValueError('Component type is required')
            
            # Check for duplicate product number
            existing = self._check_duplicate_component(
                data['product_number'], 
                data.get('supplier_id')
            )
            if existing:
                raise ValueError(f'Product number "{data["product_number"]}" already exists for this supplier')
            
            # Create component
            component = Component(
                product_number=data['product_number'],
                description=data.get('description', ''),
                supplier_id=data.get('supplier_id'),
                component_type_id=data['component_type_id'],
                properties={}
            )
            
            db.session.add(component)
            db.session.flush()  # Get component ID
            
            # Handle associations using updated handlers
            self._handle_component_associations(component, data, is_edit=False)
            
            # Handle variants if provided
            variants_created = []
            if 'variants' in data:
                current_app.logger.info(f"Processing {len(data['variants'])} variants")
                variants_created = self._handle_variants_creation(component, data['variants'], files)
            
            # Commit all changes
            db.session.commit()
            
            # Get association counts for response
            association_counts = get_association_counts(component)
            
            current_app.logger.info(f"Component {component.id} created successfully")
            
            return {
                'success': True,
                'component': {
                    'id': component.id,
                    'product_number': component.product_number,
                    'variants_count': len(variants_created),
                    **association_counts
                },
                'variants': variants_created,
                'message': f'Component created with {len(variants_created)} variants'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in ComponentService.create_component: {str(e)}")
            raise
    
    def update_component(self, component_id, data):
        """
        Update an existing component with all associations
        
        Args:
            component_id: ID of component to update
            data: Dict containing updated component data
            
        Returns:
            dict: Result with updated component info and changes
        """
        try:
            current_app.logger.info(f"ComponentService.update_component called for component {component_id}")
            current_app.logger.info(f"Data keys: {list(data.keys())}")
            
            # Get component to update
            component = Component.query.get(component_id)
            if not component:
                raise ValueError(f'Component {component_id} not found')
            
            current_app.logger.info(f"Found component: {component.product_number}")
            
            # Track changes for response
            changes = {}
            
            # Update basic fields
            try:
                field_changes = self._update_basic_fields(component, data)
                changes.update(field_changes)
                current_app.logger.info(f"Basic field changes: {list(field_changes.keys())}")
            except Exception as e:
                current_app.logger.error(f"Error updating basic fields: {str(e)}")
                raise ValueError(f"Error updating basic fields: {str(e)}")
            
            # Handle associations using updated handlers
            try:
                self._handle_component_associations(component, data, is_edit=True)
                changes['associations'] = 'updated'
                current_app.logger.info("Associations updated successfully")
            except Exception as e:
                current_app.logger.error(f"Error updating associations: {str(e)}")
                raise ValueError(f"Error updating associations: {str(e)}")
            
            # Handle picture order changes and renaming
            try:
                picture_changes = self._handle_picture_order_changes(component, data)
                if picture_changes:
                    changes['picture_orders'] = picture_changes
                    current_app.logger.info(f"Picture order changes processed: {len(picture_changes)}")
            except Exception as e:
                current_app.logger.error(f"Error handling picture order changes: {str(e)}")
                # Don't fail the entire update for picture order issues
                changes['picture_order_error'] = str(e)
            
            # Validate no duplicate product number if changed
            if 'product_number' in changes:
                existing = self._check_duplicate_component(
                    component.product_number, 
                    component.supplier_id,
                    exclude_id=component.id
                )
                if existing:
                    raise ValueError(f'Product number "{component.product_number}" already exists for this supplier')
            
            # Handle comprehensive picture renaming if component-level fields changed
            component_level_changed = any(field in changes for field in ['product_number', 'supplier_id'])
            if component_level_changed:
                current_app.logger.info("Component-level fields changed, renaming ALL variant pictures and updating SKUs")
                
                # Flush changes to database and refresh component relationships
                # This ensures supplier relationship is updated before picture renaming
                db.session.flush()
                db.session.refresh(component)
                current_app.logger.info(f"Component refreshed - new supplier_id: {component.supplier_id}, supplier_code: {component.supplier.supplier_code if component.supplier else 'None'}")
                
                try:
                    comprehensive_renames = self._handle_comprehensive_picture_renaming(component)
                    if comprehensive_renames:
                        changes['comprehensive_picture_renames'] = comprehensive_renames
                except Exception as e:
                    current_app.logger.error(f"Error with comprehensive picture renaming: {str(e)}")
                    # Don't fail the entire update for picture renaming issues
                    changes['picture_rename_error'] = str(e)
            
            # Commit changes
            db.session.commit()
            
            current_app.logger.info(f"Component {component_id} updated successfully with changes: {list(changes.keys())}")
            
            return {
                'success': True,
                'component_id': component.id,
                'message': 'Component updated successfully',
                'changes': changes
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in ComponentService.update_component: {str(e)}")
            current_app.logger.error(f"Full error traceback: ", exc_info=True)
            raise
    
    def get_component_for_edit(self, component_id):
        """
        Get component with all relationships for editing
        
        Args:
            component_id: ID of component to fetch
            
        Returns:
            dict: Component data with all relationships
        """
        try:
            # Load component with optimized relationships
            component = Component.query.options(
                joinedload(Component.component_type),
                joinedload(Component.supplier),
                selectinload(Component.variants).joinedload(ComponentVariant.color),
                selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures),
                selectinload(Component.pictures),
                selectinload(Component.keywords),
                selectinload(Component.brand_associations).joinedload(ComponentBrand.brand),
                selectinload(Component.categories)
            ).get(component_id)
            
            if not component:
                raise ValueError(f'Component {component_id} not found')
            
            # Build comprehensive response data
            return self._build_component_data(component)
            
        except Exception as e:
            current_app.logger.error(f"Error in ComponentService.get_component_for_edit: {str(e)}")
            raise
    
    
    # Private helper methods
    
    def _check_duplicate_component(self, product_number, supplier_id, exclude_id=None):
        """Check for duplicate product number with same supplier"""
        query = Component.query.filter_by(product_number=product_number)
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        else:
            query = query.filter(Component.supplier_id.is_(None))
        
        if exclude_id:
            query = query.filter(Component.id != exclude_id)
        
        return query.first()
    
    def _update_basic_fields(self, component, data):
        """Update basic component fields and track changes"""
        changes = {}
        
        # Update basic fields if provided
        if 'product_number' in data and data['product_number'] != component.product_number:
            changes['product_number'] = {
                'old': component.product_number,
                'new': data['product_number']
            }
            component.product_number = data['product_number']
        
        if 'description' in data and data['description'] != component.description:
            changes['description'] = {
                'old': component.description,
                'new': data['description']
            }
            component.description = data['description']
        
        if 'component_type_id' in data:
            new_type_id = int(data['component_type_id'])
            if new_type_id != component.component_type_id:
                changes['component_type_id'] = {
                    'old': component.component_type_id,
                    'new': new_type_id
                }
                component.component_type_id = new_type_id
        
        if 'supplier_id' in data:
            new_supplier_id = int(data['supplier_id']) if data['supplier_id'] else None
            if new_supplier_id != component.supplier_id:
                changes['supplier_id'] = {
                    'old': component.supplier_id,
                    'new': new_supplier_id
                }
                component.supplier_id = new_supplier_id
        
        # Handle properties update
        if 'properties' in data:
            new_properties = data['properties']
            if isinstance(new_properties, str):
                import json
                new_properties = json.loads(new_properties)
            
            if new_properties != component.properties:
                changes['properties'] = {
                    'old': component.properties,
                    'new': new_properties
                }
                component.properties = new_properties
        
        return changes
    
    # Static method wrappers for backward compatibility with tests
    @staticmethod
    def _update_basic_fields_static(component, data):
        """Static wrapper for _update_basic_fields for test compatibility"""
        service = ComponentService()
        return service._update_basic_fields(component, data)
    
    @staticmethod
    def _check_duplicate_component_static(product_number, supplier_id, exclude_id=None):
        """Static wrapper for _check_duplicate_component for test compatibility"""
        service = ComponentService()
        return service._check_duplicate_component(product_number, supplier_id, exclude_id)
    
    @staticmethod
    def _build_component_data_static(component):
        """Static wrapper for _build_component_data for test compatibility"""
        service = ComponentService()
        return service._build_component_data(component)
    
    def _handle_component_associations(self, component, data, is_edit=False):
        """Handle all component associations using updated handlers"""
        # Use updated association handlers with data override
        handle_brand_associations(component, is_edit=is_edit, data_override=data)
        handle_categories(component, is_edit=is_edit, data_override=data)
        handle_keywords(component, is_edit=is_edit, data_override=data)
        handle_component_properties(component, component.component_type_id, data_override=data)
    
    def _handle_variants_creation(self, component, variants_data, files=None):
        """Handle creation of component variants with pictures"""
        created_variants = []
        
        for variant_data in variants_data:
            try:
                # Handle custom color creation if needed
                color_id = variant_data.get('color_id')
                custom_color_name = variant_data.get('custom_color_name', '').strip()
                
                if custom_color_name and not color_id:
                    # Check if color already exists
                    existing_color = Color.query.filter_by(name=custom_color_name).first()
                    if existing_color:
                        color_id = existing_color.id
                    else:
                        # Create new color
                        new_color = Color(name=custom_color_name)
                        db.session.add(new_color)
                        db.session.flush()
                        color_id = new_color.id
                
                if not color_id:
                    continue
                
                # Check if variant already exists
                existing_variant = ComponentVariant.query.filter_by(
                    component_id=component.id,
                    color_id=color_id
                ).first()
                
                if existing_variant:
                    current_app.logger.warning(f"Variant for color {color_id} already exists")
                    continue
                
                # Create variant
                variant = ComponentVariant(
                    component_id=component.id,
                    color_id=color_id,
                    is_active=True
                )
                
                db.session.add(variant)
                db.session.flush()  # Get variant ID
                
                # Handle variant pictures if any
                variant_pictures = []
                images = variant_data.get('images', [])
                
                if images:
                    picture_order = 1
                    for image_file in images:
                        if image_file and image_file.filename and allowed_file(image_file.filename):
                            try:
                                # Generate picture name
                                from app.utils.file_handling import generate_picture_name
                                picture_name = generate_picture_name(component, variant, picture_order)
                                
                                # Create picture record
                                picture = Picture(
                                    component_id=component.id,
                                    variant_id=variant.id,
                                    picture_name=picture_name,
                                    url='',  # Will be set after upload
                                    picture_order=picture_order,
                                    alt_text=f"{component.product_number} - {variant.color.name} - Image {picture_order}"
                                )
                                db.session.add(picture)
                                db.session.flush()
                                
                                # Upload to WebDAV
                                file_ext = os.path.splitext(image_file.filename)[1].lower()
                                filename = f"{picture_name}{file_ext}"
                                
                                # Read file data
                                file_data = io.BytesIO(image_file.read())
                                file_data.seek(0)
                                
                                # Upload to WebDAV
                                upload_result = self.upload_picture_to_webdav(
                                    file_data, 
                                    filename, 
                                    image_file.content_type or 'image/jpeg'
                                )
                                
                                if upload_result['success']:
                                    picture.url = upload_result['url']
                                    variant_pictures.append({
                                        'id': picture.id,
                                        'name': picture.picture_name,
                                        'url': picture.url,
                                        'order': picture.picture_order
                                    })
                                else:
                                    current_app.logger.error(f"Failed to upload picture: {upload_result.get('error')}")
                                    db.session.delete(picture)
                                
                                picture_order += 1
                                
                            except Exception as e:
                                current_app.logger.error(f"Error processing variant picture: {str(e)}")
                
                # Get color info
                color = Color.query.get(color_id)
                
                created_variants.append({
                    'id': variant.id,
                    'color_id': color_id,
                    'color_name': color.name if color else '',
                    'sku': variant.variant_sku or '',
                    'pictures': variant_pictures
                })
                
            except Exception as e:
                current_app.logger.error(f"Error creating variant: {str(e)}")
                continue
        
        return created_variants
    
    def _build_component_data(self, component):
        """Build comprehensive component data for API responses"""
        return {
            'id': component.id,
            'product_number': component.product_number,
            'description': component.description,
            'component_type': {
                'id': component.component_type.id,
                'name': component.component_type.name
            } if component.component_type else None,
            'supplier': {
                'id': component.supplier.id,
                'supplier_code': component.supplier.supplier_code
            } if component.supplier else None,
            'properties': component.properties or {},
            'created_at': component.created_at.isoformat() if component.created_at else None,
            'updated_at': component.updated_at.isoformat() if component.updated_at else None,
            
            # Status information
            'proto_status': component.proto_status,
            'proto_comment': component.proto_comment,
            'proto_date': component.proto_date.isoformat() if component.proto_date else None,
            'sms_status': component.sms_status,
            'sms_comment': component.sms_comment,
            'sms_date': component.sms_date.isoformat() if component.sms_date else None,
            'pps_status': component.pps_status,
            'pps_comment': component.pps_comment,
            'pps_date': component.pps_date.isoformat() if component.pps_date else None,
            
            # Related data  
            'brands': [{'id': assoc.brand.id, 'name': assoc.brand.name} for assoc in component.brand_associations],
            'categories': [{'id': cat.id, 'name': cat.name} for cat in component.categories],
            'keywords': [{'id': kw.id, 'name': kw.name} for kw in component.keywords],
            
            # Variants with pictures (basic structure)
            'variants': self._build_variants_data(component.variants)
        }
    
    def _build_variants_data(self, variants):
        """Build variant data for API responses"""
        variants_data = []
        for variant in variants:
            variant_data = {
                'id': variant.id,
                'color': {
                    'id': variant.color.id,
                    'name': variant.color.name
                },
                'variant_sku': variant.variant_sku,
                'variant_name': variant.variant_name,
                'is_active': variant.is_active,
                'created_at': variant.created_at.isoformat() if variant.created_at else None,
                'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
                'pictures': []
            }
            
            # Add picture data for this variant
            for picture in variant.variant_pictures:
                picture_data = {
                    'id': picture.id,
                    'picture_name': picture.picture_name,
                    'url': picture.url,
                    'picture_order': picture.picture_order,
                    'alt_text': picture.alt_text,
                    'is_primary': picture.is_primary,
                    'file_size': picture.file_size,
                    'created_at': picture.created_at.isoformat() if picture.created_at else None
                }
                variant_data['pictures'].append(picture_data)
            
            # Sort pictures by order
            variant_data['pictures'].sort(key=lambda x: x['picture_order'])
            variants_data.append(variant_data)
        
        return variants_data
    
    def _handle_picture_order_changes(self, component, data):
        """Handle picture order changes and file renaming"""
        import json
        
        changes = {}
        
        # Check for picture order updates in the data
        picture_order_updates = {}
        picture_renames = {}  # Initialize as empty dict
        
        # Extract picture order data from request
        for key, value in data.items():
            if key.startswith('picture_order_'):
                picture_id = key.split('picture_order_')[1]
                try:
                    new_order = int(value)
                    picture_order_updates[int(picture_id)] = new_order
                except (ValueError, TypeError):
                    continue
                    
        # Extract picture rename data (from frontend staging)
        if 'picture_renames' in data:
            picture_renames = data['picture_renames']
            current_app.logger.info(f"Raw picture_renames data: {picture_renames}")
            current_app.logger.info(f"Type of picture_renames: {type(picture_renames)}")
            
            # Handle case where picture_renames might be a JSON string
            if isinstance(picture_renames, str):
                try:
                    picture_renames = json.loads(picture_renames)
                    current_app.logger.info(f"Parsed picture_renames from JSON string: {picture_renames}")
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Failed to parse picture_renames JSON: {e}")
                    picture_renames = {}
        
        if not picture_order_updates and not picture_renames:
            current_app.logger.info("No picture order updates or renames found in data")
            return None
            
        current_app.logger.info(f"Processing picture order changes: {picture_order_updates}")
        current_app.logger.info(f"Processing picture renames: {picture_renames}")
        current_app.logger.info(f"All data keys: {list(data.keys())}")
        
        # Update picture orders in database
        updated_pictures = []
        for picture_id, new_order in picture_order_updates.items():
            picture = Picture.query.filter_by(id=picture_id).first()
            if picture and picture.picture_order != new_order:
                old_order = picture.picture_order
                picture.picture_order = new_order
                updated_pictures.append({
                    'id': picture_id,
                    'old_order': old_order,
                    'new_order': new_order,
                    'picture_name': picture.picture_name
                })
                
        # Handle WebDAV file renaming for order changes
        webdav_url = current_app.config.get('WEBDAV_URL', 'http://31.182.67.115/webdav')
        webdav_base_path = f"{webdav_url}/components"
        
        renamed_files = []
        current_app.logger.info(f"Starting WebDAV file renaming for {len(picture_renames)} files")
        
        # Ensure picture_renames is a dictionary before iterating
        if not isinstance(picture_renames, dict):
            current_app.logger.error(f"picture_renames is not a dictionary: {type(picture_renames)}")
            picture_renames = {}
        
        for old_name, new_name in picture_renames.items():
            if old_name == new_name:
                current_app.logger.info(f"Skipping rename - names are identical: {old_name}")
                continue
                
            try:
                # Use WebDAV service to rename file
                old_filename = f"{old_name}.jpg"
                new_filename = f"{new_name}.jpg"
                
                current_app.logger.info(f"WebDAV rename: {old_filename} → {new_filename}")
                
                # Use WebDAV service's move_file method
                move_result = self.move_picture_in_webdav(old_filename, new_filename)
                
                if move_result['success']:
                    # Update picture_name and URL in database
                    picture = Picture.query.filter_by(picture_name=old_name).first()
                    if picture:
                        current_app.logger.info(f"Updating database: picture_name {old_name} → {new_name}")
                        old_url = picture.url
                        picture.picture_name = new_name
                        picture.url = move_result['new_url']
                        current_app.logger.info(f"Updated picture URL: {old_url} → {picture.url}")
                        
                        # If this picture rename affects variant naming, update variant SKU as well
                        if picture.variant_id:
                            variant = ComponentVariant.query.get(picture.variant_id)
                            if variant:
                                # Trigger SKU regeneration via database trigger by updating the variant
                                old_sku = variant.variant_sku
                                # Touch the variant to trigger SKU regeneration
                                variant.updated_at = db.func.now()
                                current_app.logger.info(f"Triggered SKU regeneration for variant {variant.id}")
                                # The database trigger will automatically update the SKU
                                db.session.flush()  # Execute the update to trigger the function
                                db.session.refresh(variant)  # Refresh to get the new SKU
                                current_app.logger.info(f"Updated variant SKU: {old_sku} → {variant.variant_sku}")
                    else:
                        current_app.logger.warning(f"Picture with name {old_name} not found in database")
                        
                    renamed_files.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': 'success'
                    })
                    current_app.logger.info(f"Successfully renamed {old_name} to {new_name} on WebDAV")
                else:
                    current_app.logger.error(f"Failed to rename {old_name} to {new_name} on WebDAV: {move_result.get('error', 'Unknown error')}")
                    renamed_files.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': 'failed',
                        'error': move_result.get('error', 'WebDAV rename failed')
                    })
                    
            except Exception as e:
                current_app.logger.error(f"Exception renaming {old_name} to {new_name}: {str(e)}")
                renamed_files.append({
                    'old_name': old_name,
                    'new_name': new_name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Build changes response - handle empty cases gracefully
        if updated_pictures or renamed_files:
            changes = {
                'orders_updated': updated_pictures,
                'files_renamed': renamed_files
            }
            return changes
        else:
            return None
    
    def _handle_comprehensive_picture_renaming(self, component):
        """
        Handle renaming of ALL pictures for ALL variants when component-level fields change
        (supplier_id, product_number) - this affects the prefix of all picture names
        
        This function handles the cascading changes when product_number or supplier changes:
        1. Renames all picture files on WebDAV 
        2. Updates all picture names and URLs in database
        3. Triggers SKU regeneration for all variants
        """
        from app.models import Picture
        
        current_app.logger.info(f"Starting comprehensive picture renaming for component {component.id}")
        
        # Get ALL pictures for this component - both component pictures and variant pictures
        all_pictures = db.session.query(Picture).filter(
            Picture.component_id == component.id
        ).all()
        
        if not all_pictures:
            current_app.logger.info("No pictures found for this component")
            return None
        
        current_app.logger.info(f"Found {len(all_pictures)} pictures to potentially rename")
        
        # WebDAV configuration
        webdav_url = current_app.config.get('WEBDAV_URL', 'http://31.182.67.115/webdav')
        webdav_base_path = f"{webdav_url}/components"
        
        renamed_files = []
        updated_pictures = []
        updated_variants = []
        
        for picture in all_pictures:
            try:
                # Get the variant for this picture (if it's a variant picture)
                variant = ComponentVariant.query.get(picture.variant_id) if picture.variant_id else None
                
                # Generate new picture name using the utility function for consistency
                from app.utils.file_handling import generate_picture_name
                new_picture_name = generate_picture_name(component, variant, picture.picture_order)
                
                old_picture_name = picture.picture_name
                
                # Only proceed if the name actually changed
                if old_picture_name == new_picture_name:
                    current_app.logger.info(f"Picture {picture.id} name unchanged: {old_picture_name}")
                    continue
                
                current_app.logger.info(f"Renaming picture {picture.id}: {old_picture_name} → {new_picture_name}")
                
                # Use WebDAV service to rename file
                old_filename = f"{old_picture_name}.jpg"
                new_filename = f"{new_picture_name}.jpg"
                
                # Perform WebDAV rename using service
                move_result = self.move_picture_in_webdav(old_filename, new_filename)
                
                if move_result['success']:
                    # Update picture in database - WebDAV rename succeeded
                    old_url_db = picture.url
                    picture.picture_name = new_picture_name
                    picture.url = move_result['new_url']
                    
                    updated_pictures.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'old_url': old_url_db,
                        'new_url': picture.url
                    })
                    
                    renamed_files.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'status': 'success'
                    })
                    
                    current_app.logger.info(f"Successfully renamed picture file: {old_picture_name} → {new_picture_name}")
                    
                elif "File not found" in move_result.get('error', ''):
                    # File doesn't exist in WebDAV (common in tests) - update database anyway
                    current_app.logger.warning(f"File not found in WebDAV but updating database: {old_picture_name} → {new_picture_name}")
                    old_url_db = picture.url
                    picture.picture_name = new_picture_name
                    # Keep the original URL since file doesn't exist
                    
                    updated_pictures.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'old_url': old_url_db,
                        'new_url': picture.url
                    })
                    
                    renamed_files.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'status': 'db_only',
                        'warning': 'File not found in WebDAV'
                    })
                else:
                    # Other WebDAV errors - don't update database
                    current_app.logger.error(f"Failed to rename file {old_picture_name}: {move_result.get('error', 'Unknown error')}")
                    renamed_files.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'status': 'failed',
                        'error': move_result.get('error', 'WebDAV rename failed')
                    })
                
                # Track variant for SKU update (only for variant pictures, avoid duplicates)
                # Do this for both success and file-not-found cases
                if (move_result['success'] or "File not found" in move_result.get('error', '')) and variant and variant.id not in [v['variant_id'] for v in updated_variants]:
                    old_sku = variant.variant_sku
                    # Touch the variant to trigger SKU regeneration via database trigger
                    variant.updated_at = db.func.now()
                    db.session.flush()
                    db.session.refresh(variant)
                    
                    updated_variants.append({
                        'variant_id': variant.id,
                        'old_sku': old_sku,
                        'new_sku': variant.variant_sku
                    })
                    
                    current_app.logger.info(f"Updated variant {variant.id} SKU: {old_sku} → {variant.variant_sku}")
                    
            except Exception as e:
                current_app.logger.error(f"Exception renaming picture {picture.id}: {str(e)}")
                renamed_files.append({
                    'picture_id': picture.id,
                    'old_name': old_picture_name if 'old_picture_name' in locals() else 'unknown',
                    'new_name': new_picture_name if 'new_picture_name' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })
        
        current_app.logger.info(
            f"Comprehensive renaming completed: "
            f"{len(updated_pictures)} pictures updated, "
            f"{len(updated_variants)} variants updated, "
            f"{len([r for r in renamed_files if r['status'] == 'success'])} files successfully renamed, "
            f"{len([r for r in renamed_files if r['status'] == 'failed'])} failed"
        )
        
        return {
            'renamed_files': renamed_files,
            'updated_pictures': updated_pictures,
            'updated_variants': updated_variants,
            'total_processed': len(all_pictures),
            'successful_renames': len([r for r in renamed_files if r['status'] == 'success']),
            'failed_renames': len([r for r in renamed_files if r['status'] == 'failed'])
        }
    
    def _cleanup_component_files(self, component):
        """Clean up files associated with component deletion using WebDAV"""
        deleted_files = []
        failed_deletions = []
        
        # Delete all component pictures using WebDAV
        all_pictures = []
        
        # Collect component pictures
        for picture in component.pictures:
            if picture.url:
                all_pictures.append(picture)
        
        # Collect variant pictures
        for variant in component.variants:
            for picture in variant.variant_pictures:
                if picture.url:
                    all_pictures.append(picture)
        
        # Delete each picture using WebDAV
        for picture in all_pictures:
            filename = picture.url.split('/')[-1]
            result = self.delete_picture_from_webdav(filename)
            
            if result['success']:
                deleted_files.append(filename)
                current_app.logger.info(f"Deleted picture from WebDAV: {filename}")
            else:
                failed_deletions.append({
                    'filename': filename,
                    'error': result.get('error', 'Unknown error')
                })
                current_app.logger.error(f"Failed to delete picture from WebDAV: {filename}")
        
        return {
            'deleted': deleted_files,
            'failed': failed_deletions
        }

    def delete_component(self, component_id):
        """
        Delete a component and all its associations
        
        Handles:
        - Component variants (auto-deleted via CASCADE)
        - Pictures (component and variant) with WebDAV cleanup
        - Brand associations (auto-deleted via CASCADE)
        - Keyword associations (many-to-many cleanup)
        - Category associations (many-to-many cleanup)
        
        Args:
            component_id: ID of component to delete
            
        Returns:
            dict: Result with deletion summary and status
        """
        try:
            current_app.logger.info(f"ComponentService.delete_component called for component {component_id}")
            
            # Get component with all associations loaded
            component = Component.query.options(
                selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures),
                selectinload(Component.pictures),
                selectinload(Component.brand_associations),
                selectinload(Component.keywords),
                selectinload(Component.categories)
            ).filter_by(id=component_id).first()
            
            if not component:
                raise ValueError(f'Component {component_id} not found')
            
            current_app.logger.info(f"Found component: {component.product_number}")
            
            # Collect all picture files for WebDAV deletion
            picture_files_to_delete = []
            webdav_prefix = current_app.config.get('UPLOAD_URL_PREFIX', 'http://31.182.67.115/webdav/components')
            upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
            
            # Component pictures (only those without variant_id - main component pictures)
            component_only_pictures = [p for p in component.pictures if p.variant_id is None]
            for picture in component_only_pictures:
                if picture.url:
                    filename = picture.url.split('/')[-1]
                    file_path = os.path.join(upload_folder, filename)
                    picture_files_to_delete.append({
                        'id': picture.id,
                        'filename': filename,
                        'file_path': file_path,
                        'url': picture.url,
                        'type': 'component'
                    })
                    current_app.logger.info(f"Scheduled component picture for deletion: {filename}")
            
            # Variant pictures (only those with variant_id)
            variant_pictures = [p for p in component.pictures if p.variant_id is not None]
            for picture in variant_pictures:
                if picture.url:
                    filename = picture.url.split('/')[-1]
                    file_path = os.path.join(upload_folder, filename)
                    picture_files_to_delete.append({
                        'id': picture.id,
                        'filename': filename,
                        'file_path': file_path,
                        'url': picture.url,
                        'type': 'variant',
                        'variant_id': picture.variant_id
                    })
                    current_app.logger.info(f"Scheduled variant picture for deletion: {filename}")
            
            current_app.logger.info(f"Total pictures to delete: {len(picture_files_to_delete)}")
            
            # Log associations before deletion
            variants_count = len(component.variants)
            brands_count = len(component.brand_associations)
            keywords_count = len(component.keywords)
            categories_count = len(component.categories)
            
            current_app.logger.info(f"Component associations: {variants_count} variants, {brands_count} brands, {keywords_count} keywords, {categories_count} categories")
            
            # Store component info before deletion
            product_number = component.product_number
            
            # Delete the component from database
            # This will automatically cascade delete:
            # - ComponentVariant records (variants)
            # - Picture records (both component and variant pictures)
            # - ComponentBrand records (brand associations)
            # The many-to-many relationships (keywords, categories) will also be cleaned up
            db.session.delete(component)
            db.session.commit()
            
            current_app.logger.info(f"Component {component_id} deleted from database")
            
            # Now delete picture files from WebDAV using the WebDAV service
            cleanup_result = self._cleanup_component_files(component)
            deleted_files = cleanup_result['deleted']
            failed_deletions = cleanup_result['failed']
            
            # Prepare response summary
            summary = {
                'component_id': component_id,
                'product_number': product_number,
                'associations_deleted': {
                    'variants': variants_count,
                    'brands': brands_count,
                    'keywords': keywords_count,
                    'categories': categories_count,
                    'pictures': len(picture_files_to_delete)
                },
                'files_deleted': {
                    'successful': len(deleted_files),
                    'failed': len(failed_deletions),
                    'total': len(picture_files_to_delete)
                }
            }
            
            if failed_deletions:
                summary['file_deletion_errors'] = [f"{item['filename']}: {item['error']}" for item in failed_deletions]
            
            current_app.logger.info(f"Component deletion completed: {summary}")
            
            return {
                'success': True,
                'message': f'Component "{product_number}" deleted successfully',
                'summary': summary
            }
            
        except ValueError as e:
            current_app.logger.error(f"Component not found: {str(e)}")
            raise
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting component {component_id}: {str(e)}")
            current_app.logger.error(f"Full traceback: ", exc_info=True)
            raise Exception(f'Failed to delete component: {str(e)}')
    
    def duplicate_component(self, component_id):
        """
        Duplicate a component with all its associations
        
        Args:
            component_id: ID of component to duplicate
            
        Returns:
            dict: Result with new component info
        """
        try:
            from datetime import datetime
            
            # Find the original component
            original = Component.query.get(component_id)
            if not original:
                raise ValueError(f'Component {component_id} not found')
            
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
                new_component.keywords.append(keyword)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Component duplicated successfully',
                'new_component_id': new_component.id,
                'new_product_number': new_component.product_number
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Component duplication error: {str(e)}")
            raise
    
    def bulk_delete_components(self, component_ids):
        """
        Bulk delete multiple components
        
        Args:
            component_ids: List of component IDs to delete
            
        Returns:
            dict: Result with deletion summary
        """
        try:
            deleted_count = 0
            errors = []
            
            for comp_id in component_ids:
                try:
                    result = self.delete_component(comp_id)
                    if result['success']:
                        deleted_count += 1
                except Exception as e:
                    errors.append(f"Error deleting component {comp_id}: {str(e)}")
                    current_app.logger.error(f"Error in bulk delete for component {comp_id}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Deleted {deleted_count} components',
                'deleted_count': deleted_count,
                'errors': errors
            }
            
        except Exception as e:
            current_app.logger.error(f"Bulk delete error: {str(e)}")
            raise