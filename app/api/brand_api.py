from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Brand, Subbrand
from sqlalchemy import or_

brand_api = Blueprint('brand_api', __name__)


@brand_api.route('/brands/search')
def search_brands():
    """
    Search brands for autocomplete
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'results': []})
        
        # Search for brands
        brands = Brand.query.filter(
            Brand.name.ilike(f'%{query}%')
        ).limit(limit).all()
        
        results = [{
            'id': brand.id,
            'name': brand.name,
            'subbrand_count': len(brand.subbrands)
        } for brand in brands]
        
        return jsonify({'results': results})
        
    except Exception as e:
        current_app.logger.error(f"Brand search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500


@brand_api.route('/brands/<int:brand_id>/subbrands')
def get_brand_subbrands(brand_id):
    """
    Get subbrands for a specific brand
    """
    try:
        brand = Brand.query.get_or_404(brand_id)
        
        subbrands = [{
            'id': sub.id,
            'name': sub.name
        } for sub in brand.subbrands]
        
        return jsonify({
            'success': True,
            'brand': {'id': brand.id, 'name': brand.name},
            'subbrands': subbrands
        })
        
    except Exception as e:
        current_app.logger.error(f"Get subbrands error: {str(e)}")
        return jsonify({'error': 'Failed to get subbrands'}), 500