"""
Optimized routes with improved query performance and caching.
This file contains performance-optimized versions of the main routes.
"""

import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_caching import Cache
from app import db
from app.models import (
    Component, Supplier, Category, ComponentType, Brand, ComponentBrand, 
    Color, Material, Picture, ComponentVariant, Keyword, keyword_component
)
from sqlalchemy import or_, and_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from datetime import datetime, timedelta

# Initialize cache (configure in your app factory)
cache = Cache()

optimized_bp = Blueprint('optimized', __name__)

# Cache configuration
CACHE_TIMEOUT = 300  # 5 minutes
FILTER_CACHE_TIMEOUT = 600  # 10 minutes for filter options

@optimized_bp.route('/components-optimized')
@cache.cached(timeout=CACHE_TIMEOUT, query_string=True)
def optimized_components_index():
    """
    Highly optimized components listing with:
    - Efficient eager loading
    - Query optimization
    - Reduced N+1 problems
    - Smart caching
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get filter parameters
        search = request.args.get('search', '').strip()
        component_type_ids = [int(id) for id in request.args.getlist('component_type_id') if id.isdigit()]
        category_ids = [int(id) for id in request.args.getlist('category_id') if id.isdigit()]
        supplier_ids = [int(id) for id in request.args.getlist('supplier_id') if id.isdigit()]
        brand_ids = [int(id) for id in request.args.getlist('brand_id') if id.isdigit()]
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # OPTIMIZED: Build query with efficient joins and loading
        query = db.session.query(Component).options(
            # Use selectinload for one-to-many relationships to avoid N+1
            selectinload(Component.keywords),
            selectinload(Component.pictures),
            selectinload(Component.variants).selectinload(ComponentVariant.color),
            selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures),
            # Use joinedload for many-to-one relationships  
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.category),
        )

        # OPTIMIZED: Apply filters efficiently
        filters = []
        
        if search:
            # Use subquery for keyword search to avoid complex joins
            keyword_subquery = db.session.query(keyword_component.c.component_id).join(
                Keyword, keyword_component.c.keyword_id == Keyword.id
            ).filter(Keyword.name.ilike(f'%{search}%'))
            
            filters.append(or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%'),
                Component.id.in_(keyword_subquery)
            ))

        if component_type_ids:
            filters.append(Component.component_type_id.in_(component_type_ids))
        if category_ids:
            filters.append(Component.category_id.in_(category_ids))
        if supplier_ids:
            filters.append(Component.supplier_id.in_(supplier_ids))
            
        if brand_ids:
            brand_components_subquery = db.session.query(ComponentBrand.component_id).filter(
                ComponentBrand.brand_id.in_(brand_ids)
            )
            filters.append(Component.id.in_(brand_components_subquery))

        if status:
            if status == 'approved':
                filters.append(and_(
                    Component.proto_status == 'ok',
                    Component.sms_status == 'ok', 
                    Component.pps_status == 'ok'
                ))
            elif status == 'pending':
                filters.append(or_(
                    Component.proto_status == 'pending',
                    Component.sms_status == 'pending',
                    Component.pps_status == 'pending'
                ))

        if filters:
            query = query.filter(and_(*filters))

        # Apply sorting
        sort_column = getattr(Component, sort_by, Component.created_at)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Execute pagination
        components_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # OPTIMIZED: Batch load brands for all components
        components = components_pagination.items
        if components:
            component_ids = [c.id for c in components]
            
            # Single query to get all brand associations
            brands_data = db.session.query(
                ComponentBrand.component_id,
                Brand.id.label('brand_id'),
                Brand.name.label('brand_name')
            ).join(Brand).filter(
                ComponentBrand.component_id.in_(component_ids)
            ).all()
            
            # Group brands by component
            component_brands = {}
            for comp_id, brand_id, brand_name in brands_data:
                if comp_id not in component_brands:
                    component_brands[comp_id] = []
                component_brands[comp_id].append({'id': brand_id, 'name': brand_name})
            
            # Attach to components
            for component in components:
                component._cached_brands = component_brands.get(component.id, [])

        # Get filter options (cached separately)
        filter_options = get_cached_filter_options()

        return render_template(
            'index.html',
            components=components_pagination,
            **filter_options,
            search=search,
            current_filters={
                'component_type_ids': component_type_ids,
                'category_ids': category_ids,
                'supplier_ids': supplier_ids,
                'brand_ids': brand_ids,
                'status': status,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error in optimized components route: {str(e)}")
        flash('Error loading components', 'error')
        return render_template('index.html', components=None)


@cache.cached(timeout=FILTER_CACHE_TIMEOUT, key_prefix='filter_options')
def get_cached_filter_options():
    """Get filter options with caching to avoid repeated queries"""
    try:
        # OPTIMIZED: Single queries for filter options, only fetch used ones
        component_types = db.session.query(ComponentType).join(Component).distinct().order_by(ComponentType.name).all()
        suppliers = db.session.query(Supplier).join(Component).distinct().order_by(Supplier.supplier_code).all()  
        categories = db.session.query(Category).join(Component).distinct().order_by(Category.name).all()
        brands = db.session.query(Brand).join(ComponentBrand).join(Component).distinct().order_by(Brand.name).all()
        
        return {
            'component_types': component_types,
            'suppliers': suppliers,
            'categories': categories,
            'brands': brands,
            'brands_count': len(brands)
        }
    except Exception as e:
        current_app.logger.error(f"Error loading filter options: {str(e)}")
        return {
            'component_types': [],
            'suppliers': [],
            'categories': [],
            'brands': [],
            'brands_count': 0
        }


@optimized_bp.route('/component-optimized/<int:id>')
def optimized_component_detail(id):
    """Optimized component detail view with efficient loading"""
    try:
        # OPTIMIZED: Load all related data in single query
        component = db.session.query(Component).options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.category),
            selectinload(Component.keywords),
            selectinload(Component.pictures),
            selectinload(Component.variants).selectinload(ComponentVariant.color),
            selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures),
            selectinload(Component.brand_associations).selectinload(ComponentBrand.brand)
        ).filter(Component.id == id).first_or_404()

        return render_template('component_detail.html', component=component)

    except Exception as e:
        current_app.logger.error(f"Error loading component {id}: {str(e)}")
        flash('Error loading component', 'error')
        return redirect(url_for('optimized.optimized_components_index'))


@optimized_bp.route('/suppliers-optimized')
@cache.cached(timeout=CACHE_TIMEOUT, query_string=True)
def optimized_suppliers():
    """Optimized suppliers list with component counts"""
    try:
        sort_by = request.args.get('sort', 'code')
        
        # OPTIMIZED: Use subquery to get component counts efficiently
        component_count_subquery = db.session.query(
            Component.supplier_id,
            func.count(Component.id).label('component_count')
        ).group_by(Component.supplier_id).subquery()
        
        # Build main query with left join to get counts
        query = db.session.query(
            Supplier,
            func.coalesce(component_count_subquery.c.component_count, 0).label('component_count')
        ).outerjoin(
            component_count_subquery,
            Supplier.id == component_count_subquery.c.supplier_id
        )
        
        # Apply sorting
        if sort_by == 'components':
            query = query.order_by(desc('component_count'))
        elif sort_by == 'created':
            query = query.order_by(desc(Supplier.created_at))
        else:
            query = query.order_by(Supplier.supplier_code)
        
        suppliers_data = query.all()
        
        # Prepare for template
        suppliers = [row[0] for row in suppliers_data]
        suppliers_with_counts = []
        
        for supplier, count in suppliers_data:
            supplier_dict = {
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'address': supplier.address,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
                'component_count': count
            }
            suppliers_with_counts.append(supplier_dict)
        
        return render_template(
            'suppliers.html',
            suppliers=suppliers,
            suppliers_data=suppliers_with_counts,
            sort_by=sort_by
        )
        
    except Exception as e:
        current_app.logger.error(f"Error loading optimized suppliers: {str(e)}")
        flash('Error loading suppliers', 'error')
        return render_template('suppliers.html', suppliers=[], suppliers_data=[])


def clear_component_caches():
    """Clear component-related caches when data changes"""
    cache.delete('filter_options')
    # Clear paginated component cache by pattern
    cache.delete_memoized(optimized_components_index)
    cache.delete_memoized(optimized_suppliers)


# Cache invalidation helpers
@optimized_bp.after_request
def after_request(response):
    """Clear caches on data modification"""
    if request.method in ['POST', 'PUT', 'DELETE'] and response.status_code < 400:
        clear_component_caches()
    return response


@cache.cached(timeout=900, key_prefix='component_stats')  # 15 minutes
def get_dashboard_stats():
    """Get dashboard statistics with caching"""
    try:
        stats = db.session.query(
            func.count(Component.id).label('total_components'),
            func.count(func.distinct(Component.supplier_id)).label('total_suppliers'),
            func.count(func.distinct(ComponentBrand.brand_id)).label('total_brands'),
            func.sum(func.case([(Component.proto_status == 'ok', 1)], else_=0)).label('approved_components')
        ).outerjoin(ComponentBrand).first()
        
        return {
            'total_components': stats.total_components or 0,
            'total_suppliers': stats.total_suppliers or 0,
            'total_brands': stats.total_brands or 0,
            'approved_components': stats.approved_components or 0,
        }
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {str(e)}")
        return {'total_components': 0, 'total_suppliers': 0, 'total_brands': 0, 'approved_components': 0}


@optimized_bp.route('/api/search-optimized')
def optimized_search_api():
    """Optimized search API with minimal data transfer"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if len(query) < 2:
            return {'results': []}
        
        # OPTIMIZED: Only select needed fields
        components = db.session.query(
            Component.id,
            Component.product_number,
            Component.description,
            Supplier.supplier_code,
            ComponentType.name.label('type_name')
        ).join(Supplier).join(ComponentType).filter(
            or_(
                Component.product_number.ilike(f'%{query}%'),
                Component.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        results = [{
            'id': c.id,
            'product_number': c.product_number,
            'description': c.description,
            'supplier': c.supplier_code,
            'type': c.type_name
        } for c in components]
        
        return {'results': results}
        
    except Exception as e:
        current_app.logger.error(f"Error in optimized search: {str(e)}")
        return {'error': 'Search failed'}, 500