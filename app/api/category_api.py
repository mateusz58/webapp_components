from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Category

category_api = Blueprint('category_api', __name__)


@category_api.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category via AJAX
    """
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Category name is required'}), 400
        
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'error': 'Category already exists'}), 400
        
        # Create new category
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'category': {
                'id': new_category.id,
                'name': new_category.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category creation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500