"""
Variant API endpoints for REST interactions
Handles variant and variant picture management via AJAX/API calls
"""
from flask import Blueprint, request, jsonify, current_app
from app.models import ComponentVariant, Component, Color, Picture
from app import db
from app.utils.file_handling import save_uploaded_file, delete_file, allowed_file
from sqlalchemy import func
import io
import os

variant_api = Blueprint('variant_api', __name__, url_prefix='/api/variant')

@variant_api.route('/<int:variant_id>/pictures', methods=['POST'])
def add_variant_pictures(variant_id):
    """Add pictures to a specific variant via API"""
    try:
        variant = ComponentVariant.query.get_or_404(variant_id)
        
        # Get uploaded files
        files = request.files.getlist('images')
        
        if not files or not any(f.filename for f in files):
            return jsonify({'error': 'No files provided'}), 400
        
        # Get current max order for this variant
        max_order = db.session.query(func.max(Picture.picture_order)).filter_by(
            variant_id=variant.id
        ).scalar() or 0
        
        # Store file data in memory for proper processing
        pending_pictures = []
        
        for picture_file in files:
            if picture_file and picture_file.filename and allowed_file(picture_file.filename):
                try:
                    # Read file into memory
                    file_data = io.BytesIO(picture_file.read())
                    file_ext = os.path.splitext(picture_file.filename)[1].lower()
                    max_order += 1
                    
                    # Create picture record (database trigger will generate picture_name)
                    picture = Picture(
                        component_id=variant.component_id,
                        variant_id=variant.id,
                        url='',  # Will be set after file is saved with proper name
                        picture_order=max_order,
                        alt_text=f"{variant.component.product_number} - {variant.color.name} - Image {max_order}"
                    )
                    db.session.add(picture)
                    
                    # Store file data for later saving
                    pending_pictures.append({
                        'picture': picture,
                        'file_data': file_data,
                        'extension': file_ext
                    })
                    
                except Exception as e:
                    current_app.logger.error(f"Error processing picture: {str(e)}")
                    continue
        
        if not pending_pictures:
            return jsonify({'error': 'No valid image files provided'}), 400
        
        # Commit to trigger database functions (picture naming)
        db.session.commit()
        
        # Now save files with database-generated names
        saved_pictures = []
        webdav_prefix = current_app.config.get('UPLOAD_URL_PREFIX', 'http://31.182.67.115/webdav/components')
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
        
        try:
            for pending in pending_pictures:
                picture = pending['picture']
                file_data = pending['file_data']
                extension = pending['extension']
                
                # Refresh picture from database to get the generated picture_name
                db.session.refresh(picture)
                
                if picture.picture_name:
                    # Save file with database-generated name
                    filename = f"{picture.picture_name}{extension}"
                    file_path = os.path.join(upload_folder, filename)
                    
                    file_data.seek(0)
                    with open(file_path, 'wb') as f:
                        f.write(file_data.read())
                    
                    # Set the proper URL
                    picture.url = f"{webdav_prefix}/{filename}"
                    db.session.add(picture)
                    
                    saved_pictures.append({
                        'id': picture.id,
                        'name': picture.picture_name,
                        'url': picture.url,
                        'order': picture.picture_order,
                        'alt_text': picture.alt_text
                    })
            
            # Commit URL updates
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Added {len(saved_pictures)} pictures',
                'pictures': saved_pictures
            })
            
        except Exception as save_error:
            db.session.rollback()
            current_app.logger.error(f"Error saving picture files: {str(save_error)}")
            return jsonify({'error': f'Failed to save files: {str(save_error)}'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding variant pictures: {str(e)}")
        return jsonify({'error': str(e)}), 500

@variant_api.route('/<int:variant_id>/pictures/<int:picture_id>', methods=['DELETE'])
def delete_variant_picture(variant_id, picture_id):
    """Delete a specific picture from a variant"""
    try:
        picture = Picture.query.filter_by(
            id=picture_id,
            variant_id=variant_id
        ).first_or_404()
        
        # Delete the file from storage
        file_deleted = False
        if picture.url:
            file_deleted = delete_file(picture.url)
            if not file_deleted:
                current_app.logger.warning(f"Failed to delete file for picture {picture_id}: {picture.url}")
        
        # Delete from database
        db.session.delete(picture)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Picture deleted successfully',
            'file_deleted': file_deleted
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting picture: {str(e)}")
        return jsonify({'error': str(e)}), 500

@variant_api.route('/<int:variant_id>/pictures/<int:picture_id>/primary', methods=['POST'])
def set_primary_picture(variant_id, picture_id):
    """Set a picture as primary for the variant"""
    try:
        variant = ComponentVariant.query.get_or_404(variant_id)
        
        # Remove primary status from all pictures in this variant
        Picture.query.filter_by(variant_id=variant_id).update({'is_primary': False})
        
        # Set the specified picture as primary
        picture = Picture.query.filter_by(
            id=picture_id,
            variant_id=variant_id
        ).first_or_404()
        
        picture.is_primary = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Primary picture updated',
            'picture_id': picture_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error setting primary picture: {str(e)}")
        return jsonify({'error': str(e)}), 500

@variant_api.route('/colors/available/<int:component_id>', methods=['GET'])
def get_available_colors(component_id):
    """Get colors that are not yet used by any variant of this component"""
    try:
        component = Component.query.get_or_404(component_id)
        
        # Get colors already used by this component's variants
        used_color_ids = [v.color_id for v in component.variants]
        
        # Get all colors not used by this component
        available_colors = Color.query.filter(
            ~Color.id.in_(used_color_ids) if used_color_ids else True
        ).order_by(Color.name).all()
        
        return jsonify({
            'colors': [{'id': c.id, 'name': c.name} for c in available_colors]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting available colors: {str(e)}")
        return jsonify({'error': str(e)}), 500


@variant_api.route('/create', methods=['POST'])
def create_variant():
    """Create a new variant for a component"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        component_id = data.get('component_id')
        color_id = data.get('color_id')
        custom_color_name = data.get('custom_color_name', '').strip()
        
        if not component_id:
            return jsonify({'error': 'Component ID is required'}), 400
        
        # Verify component exists
        component = Component.query.get_or_404(component_id)
        
        # Handle custom color creation
        if custom_color_name:
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
            return jsonify({'error': 'Color selection or custom color name is required'}), 400
        
        # Check if variant already exists for this color
        existing_variant = ComponentVariant.query.filter_by(
            component_id=component_id,
            color_id=color_id
        ).first()
        
        if existing_variant:
            return jsonify({'error': 'A variant with this color already exists'}), 400
        
        # Create variant
        variant = ComponentVariant(
            component_id=component_id,
            color_id=color_id,
            is_active=True
        )
        
        db.session.add(variant)
        db.session.commit()
        
        # Get color info for response
        color = Color.query.get(color_id)
        
        return jsonify({
            'success': True,
            'message': 'Variant created successfully',
            'variant': {
                'id': variant.id,
                'color_id': color_id,
                'color_name': color.name,
                'sku': variant.variant_sku or '',
                'component_id': component_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating variant: {str(e)}")
        return jsonify({'error': str(e)}), 500


@variant_api.route('/<int:variant_id>/update', methods=['PUT'])
def update_variant(variant_id):
    """Update variant properties"""
    try:
        variant = ComponentVariant.query.get_or_404(variant_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'is_active' in data:
            variant.is_active = data['is_active']
        
        if 'variant_name' in data:
            variant.variant_name = data['variant_name']
        
        if 'description' in data:
            variant.description = data['description']
        
        # Note: Color changes are not allowed via update to maintain SKU consistency
        # Color changes should be handled by creating a new variant
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Variant updated successfully',
            'variant': {
                'id': variant.id,
                'color_name': variant.color.name,
                'sku': variant.variant_sku or '',
                'is_active': variant.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating variant: {str(e)}")
        return jsonify({'error': str(e)}), 500


@variant_api.route('/<int:variant_id>/delete', methods=['DELETE'])
def delete_variant(variant_id):
    """Delete a variant and all its pictures"""
    try:
        variant = ComponentVariant.query.get_or_404(variant_id)
        
        # Delete all variant pictures from filesystem
        deleted_files = []
        failed_files = []
        
        for picture in variant.variant_pictures:
            if picture.url:
                if delete_file(picture.url):
                    deleted_files.append(picture.url)
                else:
                    failed_files.append(picture.url)
        
        # Delete variant (cascade will handle pictures)
        component_id = variant.component_id
        db.session.delete(variant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Variant deleted successfully',
            'component_id': component_id,
            'files_deleted': len(deleted_files),
            'files_failed': len(failed_files)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting variant: {str(e)}")
        return jsonify({'error': str(e)}), 500


@variant_api.route('/<int:variant_id>/pictures/<int:picture_id>/alt-text', methods=['PUT'])
def update_picture_alt_text(variant_id, picture_id):
    """Update alt text for a picture"""
    try:
        data = request.get_json()
        alt_text = data.get('alt_text', '') if data else ''
        
        picture = Picture.query.filter_by(
            id=picture_id,
            variant_id=variant_id
        ).first_or_404()
        
        picture.alt_text = alt_text
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alt text updated',
            'alt_text': alt_text
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating alt text: {str(e)}")
        return jsonify({'error': str(e)}), 500