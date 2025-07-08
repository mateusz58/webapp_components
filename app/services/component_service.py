"""
Component Service Layer
Centralized business logic for component management operations
Used by both API endpoints and web routes to ensure consistency
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
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_
import time


class ComponentService:
    """Service class for component business logic"""
    
    @staticmethod
    def create_component(data, files=None):
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
            existing = ComponentService._check_duplicate_component(
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
            ComponentService._handle_component_associations(component, data, is_edit=False)
            
            # Handle variants if provided
            variants_created = []
            if 'variants' in data:
                variants_created = ComponentService._handle_variants_creation(component, data['variants'], files)
            
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
    
    @staticmethod
    def update_component(component_id, data):
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
                field_changes = ComponentService._update_basic_fields(component, data)
                changes.update(field_changes)
                current_app.logger.info(f"Basic field changes: {list(field_changes.keys())}")
            except Exception as e:
                current_app.logger.error(f"Error updating basic fields: {str(e)}")
                raise ValueError(f"Error updating basic fields: {str(e)}")
            
            # Handle associations using updated handlers
            try:
                ComponentService._handle_component_associations(component, data, is_edit=True)
                changes['associations'] = 'updated'
                current_app.logger.info("Associations updated successfully")
            except Exception as e:
                current_app.logger.error(f"Error updating associations: {str(e)}")
                raise ValueError(f"Error updating associations: {str(e)}")
            
            # Handle picture order changes and renaming
            try:
                picture_changes = ComponentService._handle_picture_order_changes(component, data)
                if picture_changes:
                    changes['picture_orders'] = picture_changes
                    current_app.logger.info(f"Picture order changes processed: {len(picture_changes)}")
            except Exception as e:
                current_app.logger.error(f"Error handling picture order changes: {str(e)}")
                # Don't fail the entire update for picture order issues
                changes['picture_order_error'] = str(e)
            
            # Validate no duplicate product number if changed
            if 'product_number' in changes:
                existing = ComponentService._check_duplicate_component(
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
                try:
                    comprehensive_renames = ComponentService._handle_comprehensive_picture_renaming(component)
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
    
    @staticmethod
    def get_component_for_edit(component_id):
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
            return ComponentService._build_component_data(component)
            
        except Exception as e:
            current_app.logger.error(f"Error in ComponentService.get_component_for_edit: {str(e)}")
            raise
    
    @staticmethod
    def delete_component(component_id):
        """
        Delete a component and all associated data
        
        Args:
            component_id: ID of component to delete
            
        Returns:
            dict: Result with deletion status
        """
        try:
            component = Component.query.get(component_id)
            if not component:
                raise ValueError(f'Component {component_id} not found')
            
            # Delete associated pictures from filesystem
            ComponentService._cleanup_component_files(component)
            
            # Delete component (cascades will handle related records)
            db.session.delete(component)
            db.session.commit()
            
            current_app.logger.info(f"Component {component_id} deleted successfully")
            
            return {
                'success': True,
                'message': 'Component deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in ComponentService.delete_component: {str(e)}")
            raise
    
    # Private helper methods
    
    @staticmethod
    def _check_duplicate_component(product_number, supplier_id, exclude_id=None):
        """Check for duplicate product number with same supplier"""
        query = Component.query.filter_by(product_number=product_number)
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        else:
            query = query.filter(Component.supplier_id.is_(None))
        
        if exclude_id:
            query = query.filter(Component.id != exclude_id)
        
        return query.first()
    
    @staticmethod
    def _update_basic_fields(component, data):
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
    
    @staticmethod
    def _handle_component_associations(component, data, is_edit=False):
        """Handle all component associations using updated handlers"""
        # Use updated association handlers with data override
        handle_brand_associations(component, is_edit=is_edit, data_override=data)
        handle_categories(component, is_edit=is_edit, data_override=data)
        handle_keywords(component, is_edit=is_edit, data_override=data)
        handle_component_properties(component, component.component_type_id, data_override=data)
    
    @staticmethod
    def _handle_variants_creation(component, variants_data, files=None):
        """Handle creation of component variants"""
        # This would be implemented for variant creation during component creation
        # For now, return empty list since variants are typically managed separately
        return []
    
    @staticmethod
    def _build_component_data(component):
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
            'variants': ComponentService._build_variants_data(component.variants)
        }
    
    @staticmethod
    def _build_variants_data(variants):
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
    
    @staticmethod
    def _handle_picture_order_changes(component, data):
        """Handle picture order changes and file renaming"""
        import os
        import requests
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
                # WebDAV MOVE operation to rename file
                old_url = f"{webdav_base_path}/{old_name}.jpg"
                new_url = f"{webdav_base_path}/{new_name}.jpg"
                
                current_app.logger.info(f"WebDAV MOVE: {old_url} → {new_url}")
                
                # First check if source file exists
                check_response = requests.head(old_url)
                if check_response.status_code != 200:
                    current_app.logger.error(f"Source file does not exist: {old_url} (status: {check_response.status_code})")
                    renamed_files.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': 'failed',
                        'error': f"Source file not found: {old_url}"
                    })
                    continue
                
                # Use WebDAV MOVE method
                response = requests.request('MOVE', old_url, headers={
                    'Destination': new_url,
                    'Overwrite': 'F'  # Don't overwrite existing files
                })
                
                current_app.logger.info(f"WebDAV MOVE response: {response.status_code}")
                
                if response.status_code in [201, 204]:  # Created or No Content (success)
                    # Update picture_name and URL in database
                    picture = Picture.query.filter_by(picture_name=old_name).first()
                    if picture:
                        current_app.logger.info(f"Updating database: picture_name {old_name} → {new_name}")
                        old_url = picture.url
                        picture.picture_name = new_name
                        picture.url = f"{webdav_base_path}/{new_name}.jpg"
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
                    current_app.logger.error(f"Failed to rename {old_name} to {new_name} on WebDAV: {response.status_code}")
                    renamed_files.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': 'failed',
                        'error': f"WebDAV error: {response.status_code}"
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
    
    @staticmethod
    def _handle_comprehensive_picture_renaming(component):
        """
        Handle renaming of ALL pictures for ALL variants when component-level fields change
        (supplier_id, product_number) - this affects the prefix of all picture names
        
        This function handles the cascading changes when product_number or supplier changes:
        1. Renames all picture files on WebDAV 
        2. Updates all picture names and URLs in database
        3. Triggers SKU regeneration for all variants
        """
        import requests
        from app.models import Picture
        
        current_app.logger.info(f"Starting comprehensive picture renaming for component {component.id}")
        
        # Get all pictures for all variants of this component
        all_pictures = db.session.query(Picture).join(ComponentVariant, Picture.variant_id == ComponentVariant.id).filter(
            ComponentVariant.component_id == component.id
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
                # Get the variant for this picture
                variant = ComponentVariant.query.get(picture.variant_id) if picture.variant_id else None
                if not variant:
                    continue
                
                # Generate new picture name based on current component data
                supplier_code = component.supplier.supplier_code if component.supplier else ''
                product_number = component.product_number.lower().replace(' ', '_')
                color_name = variant.color.name.lower().replace(' ', '_') if variant.color else 'unknown'
                picture_order = picture.picture_order
                
                # Generate new picture name using same logic as database trigger
                if supplier_code:
                    new_picture_name = f"{supplier_code.lower()}_{product_number}_{color_name}_{picture_order}"
                else:
                    new_picture_name = f"{product_number}_{color_name}_{picture_order}"
                
                old_picture_name = picture.picture_name
                
                # Only proceed if the name actually changed
                if old_picture_name == new_picture_name:
                    current_app.logger.info(f"Picture {picture.id} name unchanged: {old_picture_name}")
                    continue
                
                current_app.logger.info(f"Renaming picture {picture.id}: {old_picture_name} → {new_picture_name}")
                
                # WebDAV file renaming
                old_url = f"{webdav_base_path}/{old_picture_name}.jpg"
                new_url = f"{webdav_base_path}/{new_picture_name}.jpg"
                
                # Check if source file exists
                check_response = requests.head(old_url)
                if check_response.status_code != 200:
                    current_app.logger.error(f"Source file does not exist: {old_url}")
                    renamed_files.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'status': 'failed',
                        'error': 'Source file not found'
                    })
                    continue
                
                # Perform WebDAV MOVE to rename file
                response = requests.request('MOVE', old_url, headers={
                    'Destination': new_url,
                    'Overwrite': 'F'
                })
                
                if response.status_code in [201, 204]:
                    # Update picture in database
                    old_url_db = picture.url
                    picture.picture_name = new_picture_name
                    picture.url = f"{webdav_base_path}/{new_picture_name}.jpg"
                    
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
                    
                    # Track variant for SKU update (avoid duplicates)
                    if variant.id not in [v['variant_id'] for v in updated_variants]:
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
                else:
                    current_app.logger.error(f"Failed to rename file {old_picture_name}: WebDAV response {response.status_code}")
                    renamed_files.append({
                        'picture_id': picture.id,
                        'old_name': old_picture_name,
                        'new_name': new_picture_name,
                        'status': 'failed',
                        'error': f'WebDAV error: {response.status_code}'
                    })
                    
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
    
    @staticmethod
    def _cleanup_component_files(component):
        """Clean up files associated with component deletion"""
        import os
        
        # Delete component pictures
        for picture in component.pictures:
            if picture.url:
                file_path = os.path.join(current_app.static_folder, picture.url.lstrip('/'))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Delete variant pictures
        for variant in component.variants:
            for picture in variant.variant_pictures:
                if picture.url:
                    file_path = os.path.join(current_app.static_folder, picture.url.lstrip('/'))
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError as e:
                            current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")