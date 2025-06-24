from flask import Blueprint, request, jsonify, current_app, make_response
from app import db
from app.models import Brand, Subbrand, Component
from sqlalchemy import or_, func
from datetime import datetime
import io
import csv

brand_api_bp = Blueprint('brand_api', __name__, url_prefix='/api/brands')


@brand_api_bp.route('', methods=['GET'])
def api_brands_list():
    """API endpoint to get brands list for autocomplete/dropdowns"""
    try:
        search = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)

        query = Brand.query
        if search:
            query = query.filter(Brand.name.ilike(f'%{search}%'))

        brands = query.order_by(Brand.name).limit(limit).all()

        results = [{
            'id': brand.id,
            'name': brand.name,
            'subbrands_count': len(brand.subbrands),
            'components_count': brand.get_components_count()
        } for brand in brands]

        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Error in brands API: {str(e)}")
        return jsonify({'error': 'Failed to load brands'}), 500


@brand_api_bp.route('/<int:brand_id>/subbrands', methods=['GET'])
def api_subbrands_list(brand_id):
    """API endpoint to get subbrands for a specific brand"""
    try:
        brand = Brand.query.get_or_404(brand_id)

        results = [{
            'id': subbrand.id,
            'name': subbrand.name,
            'full_name': subbrand.get_full_name()
        } for subbrand in brand.subbrands]

        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Error in subbrands API: {str(e)}")
        return jsonify({'error': 'Failed to load subbrands'}), 500


@brand_api_bp.route('/<int:brand_id>', methods=['PUT'])
def api_update_brand(brand_id):
    """API endpoint to update a brand"""
    try:
        brand = Brand.query.get_or_404(brand_id)
        data = request.get_json()

        brand_name = data.get('name', '').strip()
        if not brand_name:
            return jsonify({'success': False, 'error': 'Brand name is required'}), 400

        # Check for duplicate name
        existing = Brand.query.filter(
            Brand.name == brand_name,
            Brand.id != brand_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': 'Brand name already exists'}), 400

        # Update brand
        brand.name = brand_name
        brand.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Brand updated successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating brand via API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brand_api_bp.route('/<int:brand_id>', methods=['DELETE'])
def api_delete_brand(brand_id):
    """API endpoint to delete a brand"""
    try:
        brand = Brand.query.get_or_404(brand_id)

        # Check if brand has components or subbrands
        components_count = brand.get_components_count()
        if components_count > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete brand. It has {components_count} associated components.'
            }), 400

        if brand.subbrands:
            return jsonify({
                'success': False,
                'error': f'Cannot delete brand. It has {len(brand.subbrands)} subbrands.'
            }), 400

        db.session.delete(brand)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Brand deleted successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting brand via API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brand_api_bp.route('/bulk-delete', methods=['POST'])
def api_bulk_delete_brands():
    """API endpoint for bulk deletion of brands"""
    try:
        data = request.get_json()
        brand_ids = data.get('ids', [])

        if not brand_ids:
            return jsonify({'success': False, 'error': 'No brands selected'}), 400

        # Check if any brands have components or subbrands
        brands_with_dependencies = []
        for brand_id in brand_ids:
            brand = Brand.query.get(brand_id)
            if brand:
                components_count = brand.get_components_count()
                if components_count > 0 or brand.subbrands:
                    brands_with_dependencies.append(brand.name)

        if brands_with_dependencies:
            return jsonify({
                'success': False,
                'error': f'Cannot delete brands with dependencies: {", ".join(brands_with_dependencies)}'
            }), 400

        # Delete brands
        deleted_count = Brand.query.filter(Brand.id.in_(brand_ids)).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} brand(s) deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk delete brands: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brand_api_bp.route('/export')
def api_export_brands():
    """API endpoint to export brands data"""
    try:
        # Get selected IDs if provided
        selected_ids = request.args.get('ids', '')

        if selected_ids:
            brand_ids = [int(id.strip()) for id in selected_ids.split(',') if id.strip()]
            brands = Brand.query.filter(Brand.id.in_(brand_ids)).order_by(Brand.name).all()
        else:
            brands = Brand.query.order_by(Brand.name).all()

        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Brand Name', 'Subbrands Count', 'Components Count', 'Created At', 'Updated At'])

        # Write data
        for brand in brands:
            writer.writerow([
                brand.name,
                len(brand.subbrands),
                brand.get_components_count(),
                brand.created_at.strftime('%Y-%m-%d %H:%M:%S') if brand.created_at else '',
                brand.updated_at.strftime('%Y-%m-%d %H:%M:%S') if brand.updated_at else ''
            ])

        csv_data = output.getvalue()
        output.close()

        # Return as downloadable file
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=brands.csv'
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting brands: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


# Legacy search endpoint for backward compatibility
@brand_api_bp.route('/search')
def search_brands():
    """Legacy search endpoint for autocomplete - redirects to main endpoint"""
    return api_brands_list()