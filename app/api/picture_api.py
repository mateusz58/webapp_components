from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Picture
import os

picture_api = Blueprint('picture_api', __name__)


@picture_api.route('/picture/<int:picture_id>/delete', methods=['DELETE'])
def delete_picture(picture_id):
    """
    Delete a picture via AJAX
    """
    try:
        picture = Picture.query.get_or_404(picture_id)
        
        # Delete file from filesystem
        if picture.url:
            file_path = os.path.join(current_app.static_folder, picture.url.lstrip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Delete from database
        db.session.delete(picture)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Picture deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Picture deletion error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500