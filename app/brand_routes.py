from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from app import db
from app.models import Brand, Subbrand, Component
from sqlalchemy import or_, func
from datetime import datetime
import io
import csv

brand_bp = Blueprint('brands', __name__, url_prefix='/brands')

@brand_bp.route('/')
def brands_list():
    """Display all brands with management interface"""
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')

        # Base query
        query = Brand.query

        # Apply search filter
        if search:
            query = query.filter(Brand.name.ilike(f'%{search}%'))

        # Apply sorting
        if sort_by == 'name':
            if sort_order == 'desc':
                query = query.order_by(Brand.name.desc())
            else:
                query = query.order_by(Brand.name.asc())
        elif sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(Brand.created_at.desc())
            else:
                query = query.order_by(Brand.created_at.asc())
        elif sort_by == 'components_count':
            # Sort by number of components
            query = query.outerjoin(Component.brands).group_by(Brand.id)
            if sort_order == 'desc':
                query = query.order_by(func.count(Component.id).desc())
            else:
                query = query.order_by(func.count(Component.id).asc())

        # Get paginated results
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        brands = query.paginate(
            page=page,
            per_page=min(per_page, 100),
            error_out=False
        )

        # Prepare brands data with statistics
        brands_data = []
        for brand in brands.items:
            brand_dict = {
                'id': brand.id,
                'name': brand.name,
                'created_at': brand.created_at.isoformat() if brand.created_at else None,
                'updated_at': brand.updated_at.isoformat() if brand.updated_at else None,
                'subbrands_count': len(brand.subbrands),
                'components_count': brand.get_components_count(),
                'subbrands': [
                    {
                        'id': sb.id,
                        'name': sb.name,
                        'full_name': sb.get_full_name(),
                        'created_at': sb.created_at.isoformat() if sb.created_at else None
                    } for sb in brand.subbrands
                ]
            }
            brands_data.append(brand_dict)

        return render_template('brands/brands_list.html',
                             brands=brands,
                             brands_data=brands_data,
                             search=search,
                             sort_by=sort_by,
                             sort_order=sort_order)

    except Exception as e:
        current_app.logger.error(f"Error loading brands: {str(e)}")
        flash(f'Error loading brands: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@brand_bp.route('/new', methods=['GET', 'POST'])
def new_brand():
    """Create a new brand"""
    if request.method == 'POST':
        try:
            brand_name = request.form.get('name', '').strip()

            if not brand_name:
                flash('Brand name is required.', 'danger')
                return redirect(request.url)

            # Check if brand already exists
            existing = Brand.query.filter_by(name=brand_name).first()
            if existing:
                flash('Brand name already exists.', 'danger')
                return redirect(request.url)

            # Create new brand
            brand = Brand(name=brand_name)
            db.session.add(brand)
            db.session.commit()

            flash('Brand created successfully!', 'success')
            return redirect(url_for('brands.brands_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating brand: {str(e)}")
            flash(f'Error creating brand: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request
    return render_template('brands/brand_form.html', brand=None)

@brand_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_brand(id):
    """Edit an existing brand"""
    brand = Brand.query.get_or_404(id)

    if request.method == 'POST':
        try:
            brand_name = request.form.get('name', '').strip()

            if not brand_name:
                flash('Brand name is required.', 'danger')
                return redirect(request.url)

            # Check if brand name already exists (excluding current brand)
            existing = Brand.query.filter(
                Brand.name == brand_name,
                Brand.id != id
            ).first()
            if existing:
                flash('Brand name already exists.', 'danger')
                return redirect(request.url)

            # Update brand
            brand.name = brand_name
            brand.updated_at = datetime.utcnow()

            db.session.commit()
            flash('Brand updated successfully!', 'success')
            return redirect(url_for('brands.brands_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating brand {id}: {str(e)}")
            flash(f'Error updating brand: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request
    return render_template('brands/brand_form.html', brand=brand)

@brand_bp.route('/delete/<int:id>', methods=['POST'])
def delete_brand(id):
    """Delete a brand"""
    try:
        brand = Brand.query.get_or_404(id)

        # Check if brand has any components
        components_count = brand.get_components_count()
        if components_count > 0:
            flash(f'Cannot delete brand "{brand.name}". It is associated with {components_count} component(s).', 'danger')
            return redirect(url_for('brands.brands_list'))

        # Check if brand has subbrands
        if brand.subbrands:
            flash(f'Cannot delete brand "{brand.name}". It has {len(brand.subbrands)} subbrand(s). Delete subbrands first.', 'danger')
            return redirect(url_for('brands.brands_list'))

        db.session.delete(brand)
        db.session.commit()

        flash('Brand deleted successfully!', 'success')
        return redirect(url_for('brands.brands_list'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting brand {id}: {str(e)}")
        flash(f'Error deleting brand: {str(e)}', 'danger')
        return redirect(url_for('brands.brands_list'))

@brand_bp.route('/<int:brand_id>/subbrands/new', methods=['GET', 'POST'])
def new_subbrand(brand_id):
    """Create a new subbrand for a brand"""
    brand = Brand.query.get_or_404(brand_id)

    if request.method == 'POST':
        try:
            subbrand_name = request.form.get('name', '').strip()

            if not subbrand_name:
                flash('Subbrand name is required.', 'danger')
                return redirect(request.url)

            # Check if subbrand already exists for this brand
            existing = Subbrand.query.filter_by(
                name=subbrand_name,
                brand_id=brand_id
            ).first()
            if existing:
                flash('Subbrand name already exists for this brand.', 'danger')
                return redirect(request.url)

            # Create new subbrand
            subbrand = Subbrand(
                name=subbrand_name,
                brand_id=brand_id
            )
            db.session.add(subbrand)
            db.session.commit()

            flash('Subbrand created successfully!', 'success')
            return redirect(url_for('brands.brands_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating subbrand: {str(e)}")
            flash(f'Error creating subbrand: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request
    return render_template('brands/subbrand_form.html', brand=brand, subbrand=None)

@brand_bp.route('/<int:brand_id>/subbrands/edit/<int:subbrand_id>', methods=['GET', 'POST'])
def edit_subbrand(brand_id, subbrand_id):
    """Edit an existing subbrand"""
    brand = Brand.query.get_or_404(brand_id)
    subbrand = Subbrand.query.filter_by(id=subbrand_id, brand_id=brand_id).first_or_404()

    if request.method == 'POST':
        try:
            subbrand_name = request.form.get('name', '').strip()

            if not subbrand_name:
                flash('Subbrand name is required.', 'danger')
                return redirect(request.url)

            # Check if subbrand name already exists for this brand (excluding current subbrand)
            existing = Subbrand.query.filter(
                Subbrand.name == subbrand_name,
                Subbrand.brand_id == brand_id,
                Subbrand.id != subbrand_id
            ).first()
            if existing:
                flash('Subbrand name already exists for this brand.', 'danger')
                return redirect(request.url)

            # Update subbrand
            subbrand.name = subbrand_name
            subbrand.updated_at = datetime.utcnow()

            db.session.commit()
            flash('Subbrand updated successfully!', 'success')
            return redirect(url_for('brands.brands_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating subbrand {subbrand_id}: {str(e)}")
            flash(f'Error updating subbrand: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request
    return render_template('brands/subbrand_form.html', brand=brand, subbrand=subbrand)

@brand_bp.route('/<int:brand_id>/subbrands/delete/<int:subbrand_id>', methods=['POST'])
def delete_subbrand(brand_id, subbrand_id):
    """Delete a subbrand"""
    try:
        brand = Brand.query.get_or_404(brand_id)
        subbrand = Subbrand.query.filter_by(id=subbrand_id, brand_id=brand_id).first_or_404()

        db.session.delete(subbrand)
        db.session.commit()

        flash('Subbrand deleted successfully!', 'success')
        return redirect(url_for('brands.brands_list'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting subbrand {subbrand_id}: {str(e)}")
        flash(f'Error deleting subbrand: {str(e)}', 'danger')
        return redirect(url_for('brands.brands_list'))

@brand_bp.route('/<int:brand_id>/components')
def brand_components(brand_id):
    """View all components for a specific brand"""
    try:
        brand = Brand.query.get_or_404(brand_id)

        # Get filter parameters
        search = request.args.get('search', '').strip()
        component_type_id = request.args.get('component_type_id', type=int)

        # Base query for components of this brand
        query = brand.components

        # Apply search filter
        if search:
            query = query.filter(or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%')
            ))

        # Apply component type filter
        if component_type_id:
            query = query.filter(Component.component_type_id == component_type_id)

        # Get paginated results
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        components = query.paginate(
            page=page,
            per_page=min(per_page, 50),
            error_out=False
        )

        # Get component types for filter dropdown
        from app.models import ComponentType
        component_types = ComponentType.query.order_by(ComponentType.name).all()

        return render_template('brands/brand_components.html',
                             brand=brand,
                             components=components,
                             component_types=component_types,
                             search=search)

    except Exception as e:
        current_app.logger.error(f"Error loading brand components: {str(e)}")
        flash(f'Error loading brand components: {str(e)}', 'danger')
        return redirect(url_for('brands.brands_list'))

# API Routes for AJAX functionality
@brand_bp.route('/api/brands', methods=['GET'])
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

@brand_bp.route('/api/brands/<int:brand_id>/subbrands', methods=['GET'])
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

@brand_bp.route('/api/brands/<int:brand_id>', methods=['PUT'])
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

@brand_bp.route('/api/brands/<int:brand_id>', methods=['DELETE'])
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

@brand_bp.route('/api/brands/bulk-delete', methods=['POST'])
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

@brand_bp.route('/api/brands/export')
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
        from flask import make_response
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=brands.csv'
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting brands: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500