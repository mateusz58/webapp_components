from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Picture
from app.utils.file_handling import delete_file
import os

picture_api = Blueprint('picture_api', __name__, url_prefix='/api/picture')


@picture_api.route('/<int:picture_id>/delete', methods=['DELETE'])
def delete_picture(picture_id):
    """
    Delete a picture via AJAX (handles both component and variant pictures)
    """
    try:
        picture = Picture.query.get_or_404(picture_id)
        
        # Delete file from storage using proper file handling
        file_deleted = False
        if picture.url:
            file_deleted = delete_file(picture.url)
            if not file_deleted:
                current_app.logger.warning(f"Failed to delete file for picture {picture_id}: {picture.url}")
        
        # Store component/variant info for response
        component_id = picture.component_id
        variant_id = picture.variant_id
        
        # Delete from database
        db.session.delete(picture)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Picture deleted successfully',
            'file_deleted': file_deleted,
            'component_id': component_id,
            'variant_id': variant_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Picture deletion error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@picture_api.route('/<int:picture_id>/primary', methods=['POST'])
def set_picture_primary(picture_id):
    """
    Set a picture as primary (for component or variant)
    """
    try:
        picture = Picture.query.get_or_404(picture_id)
        
        if picture.variant_id:
            # Variant picture - remove primary from all variant pictures
            Picture.query.filter_by(variant_id=picture.variant_id).update({'is_primary': False})
        else:
            # Component picture - remove primary from all component pictures
            Picture.query.filter_by(
                component_id=picture.component_id,
                variant_id=None
            ).update({'is_primary': False})
        
        # Set this picture as primary
        picture.is_primary = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Primary picture updated',
            'picture_id': picture_id,
            'component_id': picture.component_id,
            'variant_id': picture.variant_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error setting primary picture: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@picture_api.route('/<int:picture_id>/alt-text', methods=['PUT'])
def update_picture_alt_text(picture_id):
    """
    Update alt text for a picture
    """
    try:
        data = request.get_json()
        alt_text = data.get('alt_text', '') if data else ''
        
        picture = Picture.query.get_or_404(picture_id)
        picture.alt_text = alt_text
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alt text updated',
            'alt_text': alt_text,
            'picture_id': picture_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating alt text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500