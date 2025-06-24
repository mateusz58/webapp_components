"""
Variant API endpoints for REST interactions
Extracted from main routes.py for better organization
"""
from flask import Blueprint, request, jsonify, current_app
from app.models import ComponentVariant, Component, Color, Picture
from app import db
from app.utils.file_handling import save_uploaded_file

variant_api = Blueprint('variant_api', __name__, url_prefix='/api/variant')

@variant_api.route('/<int:variant_id>/pictures', methods=['POST'])
def add_variant_pictures(variant_id):
    """Add pictures to a specific variant via API"""
    try:
        variant = ComponentVariant.query.get_or_404(variant_id)
        
        # Get uploaded files
        files = request.files.getlist('images')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        added_pictures = []
        max_order = max([p.picture_order for p in variant.variant_pictures] + [0])
        
        for picture_file in files:
            if picture_file and picture_file.filename:
                try:
                    file_url = save_uploaded_file(picture_file)
                    if file_url:
                        max_order += 1
                        picture = Picture(
                            variant_id=variant.id,
                            component_id=variant.component_id,
                            picture_name=picture_file.filename,
                            url=file_url,
                            picture_order=max_order
                        )
                        db.session.add(picture)
                        added_pictures.append({
                            'filename': picture_file.filename,
                            'url': file_url,
                            'order': max_order
                        })
                except Exception as e:
                    current_app.logger.error(f"Error uploading picture: {str(e)}")
                    continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added {len(added_pictures)} pictures',
            'pictures': added_pictures
        })
        
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
        
        # Remove the file from storage
        # TODO: Implement file deletion from storage
        
        db.session.delete(picture)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Picture deleted successfully'
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
            'message': 'Primary picture updated'
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