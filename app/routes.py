import os
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from app import db
from app.models import Supplier, Category, Color, Material, Component, Picture, ComponentType, Keyword, \
    ComponentVariant, Brand, ComponentBrand, keyword_component, ComponentTypeProperty
from app.utils_legacy import process_csv_file
from sqlalchemy import or_, text, func
from datetime import datetime, timedelta
import uuid
import io
import csv
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, desc, asc, text
from sqlalchemy.orm import joinedload
import math
from datetime import datetime, timedelta


main = Blueprint('main', __name__)

# Configuration for improved file handling
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
THUMBNAIL_SIZE = (300, 300)

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 200  # Safety limit to prevent too many elements
SHOW_ALL_LIMIT = 1000  # Maximum allowed for "show all"

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def optimize_image(image_file, max_size=(1920, 1920), quality=85):
    """Optimize image for web display"""
    try:
        image = Image.open(image_file)

        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Resize if larger than max_size
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)

        return output
    except Exception as e:
        current_app.logger.error(f"Image optimization error: {str(e)}")
        return image_file

def save_uploaded_file(file, folder='uploads'):
    """Save uploaded file (simplified version without PIL optimization)"""
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            # Create upload directory if it doesn't exist
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)

            # Save file directly
            file_path = os.path.join(upload_path, unique_filename)
            file.save(file_path)

            # Return relative URL for web access
            return f"/static/uploads/{unique_filename}"

        except Exception as e:
            current_app.logger.error(f"File upload error: {str(e)}")
            flash(f'Error uploading file: {str(e)}', 'error')
            return None
    return None

@main.route('/')
@main.route('/components')
def index():
    """
    Main components listing with advanced pagination and filtering
    UPDATED: Multi-select filtering for suppliers, brands, component types, and categories
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)
        show_all = request.args.get('show_all', False, type=bool)

        # Safety checks for per_page
        if per_page > MAX_PER_PAGE:
            per_page = MAX_PER_PAGE
            flash(f'Maximum {MAX_PER_PAGE} items per page allowed. Showing {MAX_PER_PAGE} items.', 'warning')
        elif per_page < 1:
            per_page = DEFAULT_PER_PAGE

        # UPDATED: Get filter parameters with multi-select support
        search = request.args.get('search', '', type=str).strip()

        # Multi-select parameters - get lists of IDs
        component_type_ids = request.args.getlist('component_type_id')
        current_app.logger.info(f"Raw component_type_ids from request: {component_type_ids}")
        component_type_ids = [int(id) for id in component_type_ids if id.isdigit()]
        current_app.logger.info(f"Processed component_type_ids: {component_type_ids}")

        category_ids = request.args.getlist('category_id')
        current_app.logger.info(f"Raw category_ids from request: {category_ids}")
        category_ids = [int(id) for id in category_ids if id.isdigit()]

        supplier_ids = request.args.getlist('supplier_id')
        current_app.logger.info(f"Raw supplier_ids from request: {supplier_ids}")
        supplier_ids = [int(id) for id in supplier_ids if id.isdigit()]

        brand_ids = request.args.getlist('brand_id')
        current_app.logger.info(f"Raw brand_ids from request: {brand_ids}")
        brand_ids = [int(id) for id in brand_ids if id.isdigit()]

        # Single-select parameters (for status and recent)
        status = request.args.get('status', type=str)
        recent = request.args.get('recent', type=int)

        # Sort parameters
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_order = request.args.get('sort_order', 'desc', type=str)

        # Build base query with optimized loading
        query = Component.query.options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.category),
            joinedload(Component.pictures),
            joinedload(Component.keywords)
        )

        # UPDATED: Apply filters with multi-select support
        filters = []

        # Search filter - INCLUDING KEYWORDS
        if search:
            # First, try to find keywords that match the search
            keyword_subquery = db.session.query(keyword_component.c.component_id).join(
                Keyword, keyword_component.c.keyword_id == Keyword.id
            ).filter(
                Keyword.name.ilike(f'%{search}%')
            ).subquery()

            search_filter = or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%'),
                # Handle supplier search - only search if supplier_id is not null
                and_(
                    Component.supplier_id.isnot(None),
                    Component.supplier.has(Supplier.supplier_code.ilike(f'%{search}%'))
                ),
                Component.category.has(Category.name.ilike(f'%{search}%')),
                Component.component_type.has(ComponentType.name.ilike(f'%{search}%')),
                Component.id.in_(keyword_subquery)  # Add keyword search
            )
            filters.append(search_filter)

        # UPDATED: Multi-select component type filter
        if component_type_ids:
            filters.append(Component.component_type_id.in_(component_type_ids))

        # UPDATED: Multi-select category filter
        if category_ids:
            filters.append(Component.category_id.in_(category_ids))

        # UPDATED: Multi-select supplier filter
        if supplier_ids:
            filters.append(Component.supplier_id.in_(supplier_ids))

        # UPDATED: Multi-select brand filter
        if brand_ids:
            # Filter components that have any of the specified brands
            brand_components_subquery = db.session.query(ComponentBrand.component_id).filter(
                ComponentBrand.brand_id.in_(brand_ids)
            ).subquery()
            filters.append(Component.id.in_(brand_components_subquery))

        # Status filter (single select)
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
            elif status == 'rejected':
                filters.append(or_(
                    Component.proto_status == 'not_ok',
                    Component.sms_status == 'not_ok',
                    Component.pps_status == 'not_ok'
                ))

        # Recent filter (single select)
        if recent:
            recent_date = datetime.utcnow() - timedelta(days=recent)
            filters.append(Component.created_at >= recent_date)

        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))

        # Filter out components with missing required relationships BEFORE pagination
        query = query.filter(
            Component.component_type_id.isnot(None),
            Component.category_id.isnot(None)
            # supplier_id is now optional, so we don't filter it out
        )

        # Apply sorting
        sort_column = getattr(Component, sort_by, None)
        if sort_column:
            if sort_order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sort
            query = query.order_by(desc(Component.created_at))

        # Handle "show all" with safety limit
        if show_all:
            total_count = query.count()
            if total_count > SHOW_ALL_LIMIT:
                flash(f'Too many results ({total_count}). Showing first {SHOW_ALL_LIMIT} items. Please use filters to narrow down results.', 'warning')
                components_pagination = query.paginate(
                    page=1,
                    per_page=SHOW_ALL_LIMIT,
                    error_out=False,
                    max_per_page=SHOW_ALL_LIMIT
                )
            else:
                components_pagination = query.paginate(
                    page=1,
                    per_page=total_count,
                    error_out=False,
                    max_per_page=SHOW_ALL_LIMIT
                )
        else:
            # Regular pagination
            components_pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False,
                max_per_page=MAX_PER_PAGE
            )

        # Load components (already filtered for required relationships)
        valid_components = components_pagination.items
        
        # DEBUG: Backend logging temporarily disabled

        # Batch load brands for all components
        component_ids = [c.id for c in valid_components]
        if component_ids:
            brands_query = db.session.query(
                ComponentBrand.component_id,
                Brand.id,
                Brand.name
            ).join(Brand, ComponentBrand.brand_id == Brand.id).filter(
                ComponentBrand.component_id.in_(component_ids)
            ).all()

            component_brands = {}
            for comp_id, brand_id, brand_name in brands_query:
                if comp_id not in component_brands:
                    component_brands[comp_id] = []
                component_brands[comp_id].append({'id': brand_id, 'name': brand_name})

            for component in valid_components:
                component._cached_brands = component_brands.get(component.id, [])

        # Batch load variants with colors and primary pictures
        if component_ids:
            # Load variants with color info and primary picture
            variants_query = db.session.query(
                ComponentVariant.component_id,
                ComponentVariant.id,
                ComponentVariant.variant_name,
                Color.id.label('color_id'),
                Color.name.label('color_name'),
                Picture.url.label('picture_url')
            ).join(
                Color, ComponentVariant.color_id == Color.id
            ).outerjoin(
                Picture,
                and_(
                    Picture.variant_id == ComponentVariant.id,
                    Picture.is_primary == True
                )
            ).filter(
                ComponentVariant.component_id.in_(component_ids),
                ComponentVariant.is_active == True
            ).order_by(
                ComponentVariant.component_id,
                ComponentVariant.id
            ).all()

            component_variants = {}
            for row in variants_query:
                if row.component_id not in component_variants:
                    component_variants[row.component_id] = []

                # If no primary picture, try to get any picture for this variant
                picture_url = row.picture_url
                if not picture_url:
                    any_pic = Picture.query.filter_by(variant_id=row.id).first()
                    picture_url = any_pic.url if any_pic else None

                component_variants[row.component_id].append({
                    'id': row.id,
                    'name': row.variant_name or row.color_name,
                    'color_id': row.color_id,
                    'color_name': row.color_name,
                    'picture_url': picture_url
                })

            for component in valid_components:
                component._cached_variants = component_variants.get(component.id, [])

        # Get filter options - only show options that have components
        component_types_with_components = db.session.query(ComponentType).join(Component).distinct().order_by(ComponentType.name).all()
        suppliers_with_components = db.session.query(Supplier).join(Component).distinct().order_by(Supplier.supplier_code).all()
        categories_with_components = db.session.query(Category).join(Component).distinct().order_by(Category.name).all()
        brands_with_components = db.session.query(Brand).join(ComponentBrand).join(Component).distinct().order_by(Brand.name).all()

        # Get statistics
        brands_count = len(brands_with_components)

        # Pagination info for template
        pagination_info = {
            'page': components_pagination.page if hasattr(components_pagination, 'page') else 1,
            'per_page': per_page,
            'total': components_pagination.total if hasattr(components_pagination, 'total') else len(component_items),
            'pages': components_pagination.pages if hasattr(components_pagination, 'pages') else 1,
            'has_prev': components_pagination.has_prev if hasattr(components_pagination, 'has_prev') else False,
            'has_next': components_pagination.has_next if hasattr(components_pagination, 'has_next') else False,
            'show_all': show_all
        }

        # NEW: Load component type properties from database
        component_type_properties = {}
        for ct in component_types_with_components:
            ct_properties = ComponentTypeProperty.query.filter_by(component_type_id=ct.id).order_by(ComponentTypeProperty.display_order).all()
            component_type_properties[ct.name] = [
                {
                    'property_name': prop.property_name,
                    'property_type': prop.property_type,
                    'is_required': prop.is_required,
                    'options': prop.get_options(),
                    'placeholder': prop.get_placeholder(),
                    'display_name': prop.display_name
                }
                for prop in ct_properties
            ]

        return render_template(
            'index.html',
            components=components_pagination,
            component_types=component_types_with_components,
            categories=categories_with_components,
            suppliers=suppliers_with_components,
            brands=brands_with_components,
            brands_count=brands_count,
            search=search,
            pagination_info=pagination_info,
            current_filters={
                'component_type_ids': component_type_ids,
                'category_ids': category_ids,
                'supplier_ids': supplier_ids,
                'brand_ids': brand_ids,
                'status': status,
                'recent': recent,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        )

    except Exception as e:
        flash(f'An error occurred while loading components: {str(e)}', 'error')
        return render_template('index.html', components=None)

@main.route('/component/<int:id>')
def component_detail(id):
    """Component detail view - MATCHES YOUR component_detail.html"""
    try:
        component = Component.query.options(
            db.joinedload(Component.component_type),
            db.joinedload(Component.supplier),
            db.joinedload(Component.category),
            db.joinedload(Component.keywords),
            db.joinedload(Component.pictures),
            db.joinedload(Component.variants).joinedload(ComponentVariant.color),
            db.joinedload(Component.variants).joinedload(ComponentVariant.variant_pictures)
        ).get_or_404(id)

        # USES YOUR EXACT TEMPLATE: component_detail.html
        return render_template('component_detail.html', component=component)

    except Exception as e:
        current_app.logger.error(f"Error loading component {id}: {str(e)}")
        flash(f'Error loading component: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main.route('/component/new', methods=['GET', 'POST'])
def new_component():
    """Create new component - UPDATED with improved brand handling and type-specific property creation"""
    if request.method == 'POST':
        try:
            # Get form data
            product_number = request.form.get('product_number', '').strip()
            description = request.form.get('description', '').strip()
            component_type_id = request.form.get('component_type_id')
            supplier_id = request.form.get('supplier_id')  # Now optional

            # FIXED: Get or create default category
            category_id = request.form.get('category_id')
            if not category_id:
                # Try to find or create a default category
                default_category = Category.query.filter_by(name='Uncategorized').first()
                if not default_category:
                    default_category = Category(name='Uncategorized')
                    db.session.add(default_category)
                    db.session.flush()
                category_id = default_category.id
            else:
                category_id = int(category_id)

            # Validate required fields (only product_number and component_type_id are required)
            if not all([product_number, component_type_id]):
                flash('Please fill in all required fields (Product Number and Component Type).', 'danger')
                return redirect(request.url)

            # Check if at least one picture is uploaded
            has_picture = False
            for i in range(1, 6):
                picture_file = request.files.get(f'picture_{i}')
                if picture_file and picture_file.filename:
                    has_picture = True
                    break
            
            if not has_picture:
                flash('Please upload at least one picture for the component.', 'danger')
                return redirect(request.url)

            # Handle optional supplier_id
            supplier_id = int(supplier_id) if supplier_id else None

            # Check if product_number already exists for this supplier (or no supplier)
            existing_query = Component.query.filter_by(product_number=product_number)
            if supplier_id:
                existing_query = existing_query.filter_by(supplier_id=supplier_id)
            else:
                existing_query = existing_query.filter_by(supplier_id=None)
            
            existing = existing_query.first()
            if existing:
                flash('Product number already exists for this supplier.', 'danger')
                return redirect(request.url)

            # Create new component
            component = Component(
                product_number=product_number,
                description=description,
                component_type_id=int(component_type_id),
                supplier_id=supplier_id,  # Can be None
                category_id=category_id  # Now guaranteed to have a value
            )

            db.session.add(component)
            db.session.flush()  # Get the ID

            # Process keywords (optional)
            keywords = request.form.get('keywords', '').strip()
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
                for keyword_name in keyword_list:
                    keyword = Keyword.query.filter_by(name=keyword_name).first()
                    if not keyword:
                        keyword = Keyword(name=keyword_name)
                        db.session.add(keyword)

                    if keyword not in component.keywords:
                        component.keywords.append(keyword)

            # IMPROVED: Process brand associations with new options
            brand_option = request.form.get('brand_option', 'none')
            
            if brand_option == 'existing':
                # Handle existing brand selection
                selected_brands = request.form.getlist('brands')  # Get list of selected brand IDs
                if selected_brands:
                    for brand_id in selected_brands:
                        if brand_id:  # Check for empty values
                            brand = Brand.query.get(int(brand_id))
                            if brand:
                                component.add_brand(brand)
            
            elif brand_option == 'new':
                # Handle new brand creation
                new_brand_name = request.form.get('new_brand_name', '').strip()
                new_subbrand_name = request.form.get('new_subbrand_name', '').strip()
                
                if new_brand_name:
                    # Check if brand already exists
                    existing_brand = Brand.query.filter_by(name=new_brand_name).first()
                    if existing_brand:
                        brand = existing_brand
                    else:
                        # Create new brand
                        brand = Brand(name=new_brand_name)
                        db.session.add(brand)
                        db.session.flush()  # Get the brand ID
                    
                    # Add brand to component
                    component.add_brand(brand)
                    
                    # Handle subbrand if provided
                    if new_subbrand_name:
                        # Check if subbrand already exists for this brand
                        existing_subbrand = Subbrand.query.filter_by(
                            name=new_subbrand_name, 
                            brand_id=brand.id
                        ).first()
                        
                        if not existing_subbrand:
                            # Create new subbrand
                            subbrand = Subbrand(
                                name=new_subbrand_name,
                                brand_id=brand.id
                            )
                            db.session.add(subbrand)
            
            # If brand_option is 'none', no brand association is created

            # IMPROVED: Process flexible properties with new entry creation capability
            component_type = ComponentType.query.get(component_type_id)
            if component_type:
                _process_component_properties_enhanced(component, component_type.name, request.form)

            # Process image uploads
            uploaded_count = _process_image_uploads(component, request)
            
            if uploaded_count == 0:
                flash('No pictures were uploaded. Please upload at least one picture.', 'danger')
                db.session.rollback()
                return redirect(request.url)

            db.session.commit()
            flash('Component created successfully!', 'success')
            return redirect(url_for('main.component_detail', id=component.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating component: {str(e)}")
            flash(f'Error creating component: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request
    component_types = ComponentType.query.order_by(ComponentType.name).all()
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.order_by(Supplier.supplier_code).all()
    colors = Color.query.order_by(Color.name).all()
    materials = Material.query.order_by(Material.name).all()
    brands = Brand.query.order_by(Brand.name).all()  # NEW: Add brands

    # NEW: Load component type properties from database
    component_type_properties = {}
    for ct in component_types:
        ct_properties = ComponentTypeProperty.query.filter_by(component_type_id=ct.id).order_by(ComponentTypeProperty.display_order).all()
        component_type_properties[ct.name] = [
            {
                'property_name': prop.property_name,
                'property_type': prop.property_type,
                'is_required': prop.is_required,
                'options': prop.get_options(),
                'placeholder': prop.get_placeholder(),
                'display_name': prop.display_name
            }
            for prop in ct_properties
        ]

    return render_template('component_form.html',
                           component=None,
                           component_types=component_types,
                           categories=categories,
                           suppliers=suppliers,
                           colors=colors,
                           materials=materials,
                           brands=brands,  # NEW: Pass brands to template
                           component_type_properties=component_type_properties)  # NEW: Pass properties to template

@main.route('/component/edit/<int:id>', methods=['GET', 'POST'])
def edit_component(id):
    """Edit component - FIXED with proper brand handling and JSON serialization"""

    # FIXED: Load brand_associations relationship instead of brands property
    component = Component.query.options(
        db.joinedload(Component.keywords),
        db.joinedload(Component.pictures),
        db.joinedload(Component.brand_associations).joinedload(ComponentBrand.brand),
        db.joinedload(Component.variants).joinedload(ComponentVariant.color),
        db.joinedload(Component.variants).joinedload(ComponentVariant.variant_pictures)
    ).get_or_404(id)

    if request.method == 'POST':
        try:
            # Update basic information
            component.product_number = request.form.get('product_number', '').strip()
            component.description = request.form.get('description', '').strip()
            component.component_type_id = int(request.form.get('component_type_id'))
            
            # Handle optional supplier_id
            supplier_id = request.form.get('supplier_id')
            component.supplier_id = int(supplier_id) if supplier_id else None
            
            component.category_id = int(request.form.get('category_id'))
            component.updated_at = datetime.utcnow()

            # Update keywords
            component.keywords.clear()
            keywords = request.form.get('keywords', '').strip()
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
                for keyword_name in keyword_list:
                    keyword = Keyword.query.filter_by(name=keyword_name).first()
                    if not keyword:
                        keyword = Keyword(name=keyword_name)
                        db.session.add(keyword)
                    component.keywords.append(keyword)

            # FIXED: Update brand associations with proper handling
            # Get current brand IDs
            current_brand_ids = {assoc.brand_id for assoc in component.brand_associations}

            # Get new brand IDs from form
            selected_brands = request.form.getlist('brands')
            new_brand_ids = {int(brand_id) for brand_id in selected_brands if brand_id}

            # Find brands to remove and add
            brands_to_remove = current_brand_ids - new_brand_ids
            brands_to_add = new_brand_ids - current_brand_ids

            # Remove associations that are no longer needed
            if brands_to_remove:
                ComponentBrand.query.filter(
                    ComponentBrand.component_id == component.id,
                    ComponentBrand.brand_id.in_(brands_to_remove)
                ).delete(synchronize_session=False)

            # Add new associations
            for brand_id in brands_to_add:
                brand = Brand.query.get(brand_id)
                if brand:
                    association = ComponentBrand(
                        component_id=component.id,
                        brand_id=brand_id
                    )
                    db.session.add(association)

            # Update properties
            component_type = ComponentType.query.get(component.component_type_id)
            if component_type:
                component.properties = {}  # Clear existing properties
                _process_component_properties(component, component_type.name, request.form)

            # Update images with improved handling
            _update_component_images(component, request)

            db.session.commit()
            flash('Component updated successfully!', 'success')
            return redirect(url_for('main.component_detail', id=component.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating component {id}: {str(e)}")
            flash(f'Error updating component: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - show form with existing data
    component_types = ComponentType.query.order_by(ComponentType.name).all()

    # UPDATED: Get only data that is actually used in components
    # For edit form, we might want to show all options (including unused ones)
    # so users can select new suppliers/categories/brands
    # But we can also use filtered data if preferred

    # Option 1: Show all options (recommended for edit forms)
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.order_by(Supplier.supplier_code).all()
    brands = Brand.query.order_by(Brand.name).all()

    # Option 2: Show only options with existing components (uncomment if preferred)
    # categories = db.session.query(Category).join(Component).distinct().order_by(Category.name).all()
    # suppliers = db.session.query(Supplier).join(Component).distinct().order_by(Supplier.supplier_code).all()
    # brands = db.session.query(Brand).join(ComponentBrand).join(Component).distinct().order_by(Brand.name).all()

    colors = Color.query.order_by(Color.name).all()
    materials = Material.query.order_by(Material.name).all()

    # FIXED: Prepare serializable data for template
    try:
        # Convert brands to serializable format
        component_cached_brands = [{'id': brand.id, 'name': brand.name} for brand in component.brands]
        available_brands = [{'id': brand.id, 'name': brand.name} for brand in brands]

        # Set as attributes for template access
        component._cached_brands = component_cached_brands

    except Exception as e:
        # Fallback if brands property fails
        current_app.logger.warning(f"Could not load brands for component {component.id}: {e}")
        component._cached_brands = []
        available_brands = [{'id': brand.id, 'name': brand.name} for brand in brands]

    return render_template('component_edit_form.html',
                           component=component,
                           component_types=component_types,
                           categories=categories,
                           suppliers=suppliers,
                           colors=colors,
                           materials=materials,
                           brands=brands,
                           available_brands_json=available_brands,  # FIXED: Pass serializable data
                           component_brands_json=component_cached_brands)  # FIXED: Pass serializable data

@main.route('/component/delete/<int:id>', methods=['POST'])
def delete_component(id):
    """Delete a component with cascade - improved error handling."""
    try:
        component = Component.query.get_or_404(id)

        # Delete associated files
        for picture in component.pictures:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture.url.lstrip('/static/uploads/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"Could not delete file {picture.url}: {str(e)}")

        # Delete variant files
        for variant in component.variants:
            for picture in variant.variant_pictures:
                try:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture.url.lstrip('/static/uploads/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    current_app.logger.warning(f"Could not delete file {picture.url}: {str(e)}")

        # Delete associated pictures and variants (handled by cascade)
        db.session.delete(component)
        db.session.commit()

        flash('Component deleted successfully!', 'success')
        return redirect(url_for('main.index'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting component {id}: {str(e)}")
        flash(f'Error deleting component: {str(e)}', 'danger')
        return redirect(url_for('main.component_detail', id=id))

# Status Management Routes - Enhanced for new frontend
@main.route('/component/<int:id>/status/proto', methods=['POST'])
def update_proto_status(id):
    """Update proto status for a component."""
    try:
        component = Component.query.get_or_404(id)
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()

        if status not in ['pending', 'ok', 'not_ok']:
            flash('Invalid status value', 'danger')
            return redirect(url_for('main.component_detail', id=id))

        component.proto_status = status
        component.proto_comment = comment if comment else None
        component.proto_date = datetime.utcnow()
        component.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f'Proto status updated to {status}', 'success')
        return redirect(url_for('main.component_detail', id=id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating proto status: {str(e)}")
        flash(f'Error updating status: {str(e)}', 'danger')
        return redirect(url_for('main.component_detail', id=id))

@main.route('/component/<int:id>/status/sms', methods=['POST'])
def update_sms_status(id):
    """Update SMS status for a component."""
    try:
        component = Component.query.get_or_404(id)
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()

        if status not in ['pending', 'ok', 'not_ok']:
            flash('Invalid status value', 'danger')
            return redirect(url_for('main.component_detail', id=id))

        component.sms_status = status
        component.sms_comment = comment if comment else None
        component.sms_date = datetime.utcnow()
        component.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f'SMS status updated to {status}', 'success')
        return redirect(url_for('main.component_detail', id=id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating SMS status: {str(e)}")
        flash(f'Error updating status: {str(e)}', 'danger')
        return redirect(url_for('main.component_detail', id=id))

@main.route('/component/<int:id>/status/pps', methods=['POST'])
def update_pps_status(id):
    """Update PPS status for a component."""
    try:
        component = Component.query.get_or_404(id)
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()

        if status not in ['pending', 'ok', 'not_ok']:
            flash('Invalid status value', 'danger')
            return redirect(url_for('main.component_detail', id=id))

        component.pps_status = status
        component.pps_comment = comment if comment else None
        component.pps_date = datetime.utcnow()
        component.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f'PPS status updated to {status}', 'success')
        return redirect(url_for('main.component_detail', id=id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating PPS status: {str(e)}")
        flash(f'Error updating status: {str(e)}', 'danger')
        return redirect(url_for('main.component_detail', id=id))

# Variant Management Routes
@main.route('/component/<int:id>/variant/new', methods=['GET', 'POST'])
def new_variant(id):
    """Create a new variant for a component - MATCHES YOUR variant_form.html"""
    component = Component.query.get_or_404(id)

    if request.method == 'POST':
        try:
            color_id = request.form.get('color_id')
            variant_name = request.form.get('variant_name', '').strip()
            description = request.form.get('description', '').strip()

            if not color_id:
                flash('Please select a color for the variant.', 'danger')
                return redirect(request.url)

            # Check if variant with this color already exists
            existing_variant = ComponentVariant.query.filter_by(
                component_id=component.id,
                color_id=color_id
            ).first()
            if existing_variant:
                color = Color.query.get(color_id)
                flash(f'Variant with color {color.name} already exists', 'danger')
                return redirect(request.url)

            # Create new variant
            variant = ComponentVariant(
                component_id=component.id,
                color_id=int(color_id),
                variant_name=variant_name if variant_name else None,
                description=description if description else None,
                is_active=True
            )

            db.session.add(variant)
            db.session.flush()

            # Process variant images
            _process_variant_images(variant, request)

            db.session.commit()

            flash('Variant created successfully!', 'success')
            return redirect(url_for('main.component_detail', id=id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating variant: {str(e)}")
            flash(f'Error creating variant: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - Get available colors (exclude already used ones)
    used_color_ids = [v.color_id for v in component.variants]
    available_colors = Color.query.filter(
        ~Color.id.in_(used_color_ids)
    ).order_by(Color.name).all()

    # USES YOUR EXACT TEMPLATE: variant_form.html
    return render_template('variant_form.html',
                           component=component,
                           variant=None,
                           colors=available_colors)

@main.route('/component/<int:component_id>/variant/<int:variant_id>/edit', methods=['GET', 'POST'])
def edit_variant(component_id, variant_id):
    """Edit an existing variant - MATCHES YOUR variant_form.html"""
    component = Component.query.get_or_404(component_id)
    variant = ComponentVariant.query.filter_by(
        id=variant_id,
        component_id=component_id
    ).first_or_404()

    if request.method == 'POST':
        try:
            variant_name = request.form.get('variant_name', '').strip()
            description = request.form.get('description', '').strip()
            is_active = 'is_active' in request.form

            # Update variant details
            variant.variant_name = variant_name if variant_name else None
            variant.description = description if description else None
            variant.is_active = is_active
            variant.updated_at = datetime.utcnow()

            # Update variant images
            _update_variant_images(variant, request)

            db.session.commit()

            flash('Variant updated successfully!', 'success')
            return redirect(url_for('main.component_detail', id=component_id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating variant: {str(e)}")
            flash(f'Error updating variant: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - USES YOUR EXACT TEMPLATE: variant_form.html
    return render_template('variant_form.html',
                           component=component,
                           variant=variant,
                           colors=[])  # No color selection when editing

@main.route('/component/<int:component_id>/variant/<int:variant_id>/delete', methods=['POST'])
def delete_variant(component_id, variant_id):
    """Delete a variant."""
    try:
        component = Component.query.get_or_404(component_id)
        variant = ComponentVariant.query.filter_by(
            id=variant_id,
            component_id=component_id
        ).first_or_404()

        # Delete variant image files
        for picture in variant.variant_pictures:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture.url.lstrip('/static/uploads/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"Could not delete file {picture.url}: {str(e)}")

        # Delete variant (pictures will be cascade deleted)
        db.session.delete(variant)
        db.session.commit()

        flash('Color variant deleted successfully!', 'success')
        return redirect(url_for('main.component_detail', id=component_id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting variant: {str(e)}")
        flash(f'Error deleting variant: {str(e)}', 'danger')
        return redirect(url_for('main.component_detail', id=component_id))

@main.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    """Enhanced CSV upload with progress tracking."""
    if request.method == 'POST':
        try:
            # Check if a file was uploaded
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'}), 400

            file = request.files['file']

            # Check if a file was selected
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            # Check if the file has an allowed extension
            if file and file.filename.lower().endswith('.csv'):
                filename = secure_filename(file.filename)
                temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex}_{filename}")
                file.save(temp_path)

                # Process the CSV file
                results = process_csv_file(temp_path)

                # Delete the temporary file
                os.remove(temp_path)

                # Return results as JSON for AJAX requests
                if request.headers.get('Content-Type') == 'application/json':
                    return jsonify({
                        'success': True,
                        'results': results
                    })

                # Handle traditional form submission
                if results['errors']:
                    for error in results['errors']:
                        flash(error, 'danger')
                else:
                    flash(f"CSV processed successfully! Created: {results['created']}, Updated: {results['updated']}", 'success')

                return redirect(url_for('main.index'))
            else:
                error_msg = 'File type not allowed. Please upload a CSV file.'
                if request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'danger')
                return redirect(request.url)

        except Exception as e:
            current_app.logger.error(f"Error processing CSV: {str(e)}")
            error_msg = f'Error processing file: {str(e)}'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'danger')
            return redirect(request.url)

    # GET request - show upload form
    return render_template('upload.html')

# API Routes for AJAX functionality - Enhanced for new frontend
@main.route('/api/components/search')
def api_search_components():
    """API endpoint for component search with autocomplete."""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)

        if len(query) < 2:
            return jsonify([])

        components = Component.query.filter(
            or_(
                Component.product_number.ilike(f'%{query}%'),
                Component.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()

        results = [{
            'id': c.id,
            'product_number': c.product_number,
            'description': c.description,
            'supplier': c.supplier.supplier_code,
            'type': c.component_type.name
        } for c in components]

        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Error in component search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@main.route('/api/components/<int:component_id>/duplicate', methods=['POST'])
def api_duplicate_component(component_id):
    """API endpoint to duplicate a component - enhanced for new frontend."""
    try:
        original = Component.query.get_or_404(component_id)

        # Create new component with modified product number
        base_number = original.product_number
        new_product_number = f"{base_number}_COPY"
        counter = 1
        while Component.query.filter_by(product_number=new_product_number).first():
            new_product_number = f"{base_number}_COPY_{counter}"
            counter += 1

        new_component = Component(
            product_number=new_product_number,
            description=f"Copy of {original.description}" if original.description else None,
            component_type_id=original.component_type_id,
            supplier_id=original.supplier_id,
            category_id=original.category_id,
            properties=original.properties.copy() if original.properties else {}
        )

        db.session.add(new_component)
        db.session.flush()

        # Copy keywords
        for keyword in original.keywords:
            new_component.keywords.append(keyword)

        db.session.commit()

        return jsonify({
            'success': True,
            'new_id': new_component.id,
            'new_product_number': new_product_number
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error duplicating component: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/api/components/<int:component_id>/export')
def api_export_component(component_id):
    """API endpoint to export component data - enhanced for new frontend."""
    try:
        component = Component.query.options(
            db.joinedload(Component.component_type),
            db.joinedload(Component.supplier),
            db.joinedload(Component.category),
            db.joinedload(Component.keywords),
            db.joinedload(Component.pictures),
            db.joinedload(Component.variants)
        ).get_or_404(component_id)

        export_data = {
            'product_number': component.product_number,
            'description': component.description,
            'component_type': component.component_type.name,
            'supplier_code': component.supplier.supplier_code,
            'category_name': component.category.name,
            'keywords': [k.name for k in component.keywords],
            'properties': component.properties,
            'pictures': [{
                'name': p.picture_name,
                'url': p.url,
                'order': p.picture_order
            } for p in component.pictures],
            'variants': [{
                'variant_name': v.variant_name,
                'color_name': v.color.name if v.color else None,
                'description': v.description,
                'is_active': v.is_active,
                'pictures': [{
                    'name': vp.picture_name,
                    'url': vp.url,
                    'order': vp.picture_order
                } for vp in v.variant_pictures]
            } for v in component.variants],
            'status': {
                'proto': {
                    'status': component.proto_status,
                    'comment': component.proto_comment,
                    'date': component.proto_date.isoformat() if component.proto_date else None
                },
                'sms': {
                    'status': component.sms_status,
                    'comment': component.sms_comment,
                    'date': component.sms_date.isoformat() if component.sms_date else None
                },
                'pps': {
                    'status': component.pps_status,
                    'comment': component.pps_comment,
                    'date': component.pps_date.isoformat() if component.pps_date else None
                }
            },
            'created_at': component.created_at.isoformat() if component.created_at else None,
            'updated_at': component.updated_at.isoformat() if component.updated_at else None
        }

        # Return as JSON download
        json_data = json.dumps(export_data, indent=2)
        return current_app.response_class(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=component_{component.product_number}.json'
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error exporting component: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

@main.route('/api/components/bulk-delete', methods=['POST'])
def api_bulk_delete_components():
    """API endpoint for bulk deletion of components - enhanced for new frontend."""
    try:
        data = request.get_json()
        component_ids = data.get('ids', [])

        if not component_ids:
            return jsonify({'success': False, 'error': 'No components selected'}), 400

        deleted_count = 0
        for component_id in component_ids:
            component = Component.query.get(component_id)
            if component:
                # Delete associated files
                for picture in component.pictures:
                    try:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture.url.lstrip('/static/uploads/'))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception:
                        pass  # Continue even if file deletion fails

                # Delete variant files
                for variant in component.variants:
                    for picture in variant.variant_pictures:
                        try:
                            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture.url.lstrip('/static/uploads/'))
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception:
                            pass

                db.session.delete(component)
                deleted_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk delete: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/api/components/export')
def api_export_components():
    """API endpoint to export multiple components data."""
    try:
        component_ids = request.args.get('ids', '').split(',')

        if component_ids and component_ids[0]:
            components = Component.query.filter(Component.id.in_(component_ids)).all()
        else:
            components = Component.query.all()

        export_data = []
        for component in components:
            export_data.append({
                'id': component.id,
                'product_number': component.product_number,
                'description': component.description,
                'component_type': component.component_type.name,
                'supplier': component.supplier.supplier_code,
                'category': component.category.name,
                'properties': component.properties,
                'keywords': [k.name for k in component.keywords],
                'variants_count': len(component.variants),
                'images_count': len(component.pictures),
                'overall_status': component.get_overall_status() if hasattr(component, 'get_overall_status') else 'pending',
                'created_at': component.created_at.isoformat() if component.created_at else None
            })

        return jsonify({
            'success': True,
            'data': export_data,
            'total_count': len(export_data)
        })

    except Exception as e:
        current_app.logger.error(f"Export error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error exporting data'
        }), 500

# Enhanced Supplier Routes - adapted for new frontend
@main.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def api_update_supplier(supplier_id):
    """API endpoint to update a supplier."""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)

        # Handle both JSON and form data
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form

        supplier_code = data.get('supplier_code', '').strip()
        address = data.get('address', '').strip()

        if not supplier_code:
            return jsonify({'success': False, 'error': 'Supplier code is required'}), 400

        # Check for duplicate supplier code
        existing = Supplier.query.filter(
            Supplier.supplier_code == supplier_code,
            Supplier.id != supplier_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': 'Supplier code already exists'}), 400

        # Update supplier
        supplier.supplier_code = supplier_code
        supplier.address = address if address else None

        db.session.commit()

        return jsonify({'success': True, 'message': 'Supplier updated successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating supplier via API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
def api_delete_supplier(supplier_id):
    """API endpoint to delete a supplier."""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)

        # Check if supplier has any components
        if supplier.components:
            return jsonify({
                'success': False,
                'error': f'Cannot delete supplier. It has {len(supplier.components)} associated components.'
            }), 400

        db.session.delete(supplier)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Supplier deleted successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting supplier via API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/api/suppliers/bulk-delete', methods=['POST'])
def api_bulk_delete_suppliers():
    """API endpoint for bulk deletion of suppliers."""
    try:
        data = request.get_json()
        supplier_ids = data.get('ids', [])

        if not supplier_ids:
            return jsonify({'success': False, 'error': 'No suppliers selected'}), 400

        # Check if any suppliers have components
        suppliers_with_components = Supplier.query.filter(
            Supplier.id.in_(supplier_ids)
        ).filter(Supplier.components.any()).all()

        if suppliers_with_components:
            supplier_codes = [s.supplier_code for s in suppliers_with_components]
            return jsonify({
                'success': False,
                'error': f'Cannot delete suppliers with components: {", ".join(supplier_codes)}'
            }), 400

        # Delete suppliers
        deleted_count = Supplier.query.filter(Supplier.id.in_(supplier_ids)).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} supplier(s) deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk delete suppliers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/api/suppliers/export')
def api_export_suppliers():
    """API endpoint to export suppliers data."""
    try:
        # Get selected IDs if provided
        selected_ids = request.args.get('ids', '')

        if selected_ids:
            supplier_ids = [int(id.strip()) for id in selected_ids.split(',') if id.strip()]
            suppliers = Supplier.query.filter(Supplier.id.in_(supplier_ids)).order_by(Supplier.supplier_code).all()
        else:
            suppliers = Supplier.query.order_by(Supplier.supplier_code).all()

        # Create CSV data
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Supplier Code', 'Address', 'Components Count', 'Created At', 'Updated At'])

        # Write data
        for supplier in suppliers:
            writer.writerow([
                supplier.supplier_code,
                supplier.address or '',
                len(supplier.components),
                supplier.created_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.created_at else '',
                supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.updated_at else ''
            ])

        csv_data = output.getvalue()
        output.close()

        # Return as downloadable file
        from flask import make_response
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=suppliers.csv'
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting suppliers: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

@main.route('/suppliers')
def suppliers():
    """Display all suppliers with management interface."""
    try:
        suppliers_query = Supplier.query.order_by(Supplier.supplier_code).all()

        # Convert suppliers to JSON-serializable format for JavaScript
        suppliers_data = []
        for supplier in suppliers_query:
            supplier_dict = {
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'address': supplier.address,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
                'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
                'components': [
                    {
                        'id': comp.id,
                        'product_number': comp.product_number,
                        'description': comp.description,
                        'created_at': comp.created_at.isoformat() if comp.created_at else None
                    } for comp in supplier.components
                ]
            }
            suppliers_data.append(supplier_dict)

        return render_template('suppliers.html',
                               suppliers=suppliers_query,  # For server-side rendering
                               suppliers_data=suppliers_data)  # For JavaScript

    except Exception as e:
        current_app.logger.error(f"Error loading suppliers: {str(e)}")
        flash(f'Error loading suppliers: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main.route('/supplier/new', methods=['GET', 'POST'])
def new_supplier():
    """Create a new supplier - MATCHES YOUR supplier_form.html"""
    if request.method == 'POST':
        try:
            supplier_code = request.form.get('supplier_code', '').strip()
            address = request.form.get('address', '').strip()

            if not supplier_code:
                flash('Supplier code is required.', 'danger')
                return redirect(request.url)

            # Check if supplier code already exists
            existing = Supplier.query.filter_by(supplier_code=supplier_code).first()
            if existing:
                flash('Supplier code already exists.', 'danger')
                return redirect(request.url)

            # Create new supplier
            supplier = Supplier(
                supplier_code=supplier_code,
                address=address if address else None
            )

            db.session.add(supplier)
            db.session.commit()

            flash('Supplier created successfully!', 'success')
            return redirect(url_for('main.suppliers'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating supplier: {str(e)}")
            flash(f'Error creating supplier: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - USES YOUR EXACT TEMPLATE: supplier_form.html
    return render_template('supplier_form.html')

@main.route('/supplier/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    """Edit an existing supplier with enhanced debugging"""
    try:
        supplier = Supplier.query.get_or_404(id)
        current_app.logger.info(f"Found supplier: {supplier.supplier_code}, ID: {supplier.id}")
    except Exception as e:
        current_app.logger.error(f"Error finding supplier {id}: {str(e)}")
        flash(f'Supplier not found: {str(e)}', 'danger')
        return redirect(url_for('main.suppliers'))

    if request.method == 'POST':
        try:
            # Log form data for debugging
            current_app.logger.info(f"Form data received: {dict(request.form)}")

            supplier_code = request.form.get('supplier_code', '').strip()
            address = request.form.get('address', '').strip()

            current_app.logger.info(f"Updating supplier {id}: code='{supplier_code}', address='{address}'")

            if not supplier_code:
                flash('Supplier code is required.', 'danger')
                return redirect(request.url)

            # Check if supplier code already exists (excluding current supplier)
            existing = Supplier.query.filter(
                Supplier.supplier_code == supplier_code,
                Supplier.id != id
            ).first()

            if existing:
                current_app.logger.warning(f"Duplicate supplier code found: {supplier_code}")
                flash('Supplier code already exists.', 'danger')
                return redirect(request.url)

            # Log before update
            current_app.logger.info(f"Before update - Supplier: {supplier.supplier_code}, Address: {supplier.address}")

            # Update supplier fields
            old_code = supplier.supplier_code
            old_address = supplier.address

            supplier.supplier_code = supplier_code
            supplier.address = address if address else None

            current_app.logger.info(f"After field update - Old: ({old_code}, {old_address}) -> New: ({supplier.supplier_code}, {supplier.address})")

            # Commit the changes
            db.session.commit()
            current_app.logger.info(f"Successfully updated supplier {id}")

            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('main.suppliers'))

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            current_app.logger.error(f"Error updating supplier {id}: {error_msg}")
            current_app.logger.error(f"Exception type: {type(e).__name__}")

            # More detailed error logging
            import traceback
            current_app.logger.error(f"Full traceback: {traceback.format_exc()}")

            flash(f'Error updating supplier: {error_msg}', 'danger')
            return redirect(request.url)

    # GET request - show form with existing data
    try:
        current_app.logger.info(f"Rendering edit form for supplier {id}: {supplier.supplier_code}")

        # Log the supplier object structure for debugging
        current_app.logger.info(f"Supplier object: supplier_code={supplier.supplier_code}, address={supplier.address}, id={supplier.id}")

        return render_template('supplier_form.html', supplier=supplier)

    except Exception as e:
        current_app.logger.error(f"Error rendering template: {str(e)}")
        flash(f'Error loading edit form: {str(e)}', 'danger')
        return redirect(url_for('main.suppliers'))

@main.route('/supplier/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    """Delete a supplier."""
    try:
        supplier = Supplier.query.get_or_404(id)

        # Check if supplier has any components
        if supplier.components:
            flash(f'Cannot delete supplier {supplier.supplier_code}. It has {len(supplier.components)} associated components.', 'danger')
            return redirect(url_for('main.suppliers'))

        db.session.delete(supplier)
        db.session.commit()

        flash('Supplier deleted successfully!', 'success')
        return redirect(url_for('main.suppliers'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting supplier {id}: {str(e)}")
        flash(f'Error deleting supplier: {str(e)}', 'danger')
        return redirect(url_for('main.suppliers'))

# Helper functions - Enhanced for new frontend
def _process_component_properties_enhanced(component, component_type_name, form_data):
    """Process component properties with enhanced capability to create new entries for type-specific properties"""
    # Get properties from database for this component type
    component_type = ComponentType.query.filter_by(name=component_type_name).first()
    if not component_type:
        return
    
    type_properties = ComponentTypeProperty.query.filter_by(component_type_id=component_type.id).order_by(ComponentTypeProperty.display_order).all()
    
    # Initialize properties dict if it doesn't exist
    if not hasattr(component, 'properties') or component.properties is None:
        component.properties = {}

    for prop in type_properties:
        prop_value = form_data.get(prop.property_name)
        new_prop_value = form_data.get(f'new_{prop.property_name}')
        
        # Use new value if provided, otherwise use existing value
        final_value = new_prop_value.strip() if new_prop_value and new_prop_value.strip() else prop_value
        
        if final_value:
            # Handle different property types
            if prop.property_type == 'multiselect':
                if isinstance(final_value, list):
                    values = final_value
                else:
                    # Convert string to array if needed
                    values = [v.strip() for v in final_value.split(',') if v.strip()]
                
                if values:
                    # For multiselect, we might need to create new entries in the database
                    processed_values = []
                    for value in values:
                        processed_value = _process_property_value(prop.property_name, value, component_type_name)
                        processed_values.append(processed_value)
                    
                    component.properties[prop.property_name] = {
                        'value': processed_values,
                        'updated_at': datetime.utcnow().isoformat()
                    }
            else:
                # For text and select types
                processed_value = _process_property_value(prop.property_name, final_value, component_type_name)
                component.properties[prop.property_name] = {
                    'value': processed_value,
                    'updated_at': datetime.utcnow().isoformat()
                }

def _process_property_value(property_name, value, component_type_name):
    """Process a property value, creating new database entries if needed"""
    property_name_lower = property_name.lower()
    
    # Map property names to their corresponding models
    property_mappings = {
        'material': (Material, 'name'),
        'color': (Color, 'name'),
        'category': (Category, 'name'),
        'keywords': (Keyword, 'name')
    }
    
    if property_name_lower in property_mappings:
        model_class, field_name = property_mappings[property_name_lower]
        
        # Check if the value already exists
        existing = model_class.query.filter_by(**{field_name: value}).first()
        
        if not existing:
            # Create new entry
            new_entry = model_class(**{field_name: value})
            db.session.add(new_entry)
            db.session.flush()  # Get the ID
            
            # Log the creation for debugging
            current_app.logger.info(f"Created new {model_class.__name__}: {value} for component type: {component_type_name}")
        
        return value  # Return the value (not the ID) for consistency with existing properties
    
    # For properties that don't map to specific models, just return the value
    return value

def _process_image_uploads(component, request):
    """Process image uploads for a component with auto-assigned order - enhanced for new frontend."""
    uploaded_count = 0
    picture_order = 1

    for i in range(1, 11):  # Up to 10 pictures for better capacity
        picture_file = request.files.get(f'picture_{i}')

        if picture_file and picture_file.filename:
            try:
                # Use the improved save_uploaded_file function
                file_url = save_uploaded_file(picture_file)
                if file_url:
                    picture = Picture(
                        component_id=component.id,
                        picture_name=picture_file.filename,
                        url=file_url,
                        picture_order=picture_order
                    )
                    db.session.add(picture)
                    uploaded_count += 1
                    picture_order += 1

            except Exception as e:
                current_app.logger.error(f"Error uploading image {i}: {str(e)}")
                continue

    return uploaded_count

def _update_component_images(component, request):
    """Update component images, handling both new uploads and existing images - enhanced for new frontend."""
    # Handle existing picture updates
    for picture in component.pictures:
        picture_index = None
        for i, existing_picture in enumerate(component.pictures, 1):
            if existing_picture.id == picture.id:
                picture_index = i
                break

        if picture_index:
            name_key = f'existing_picture_{picture_index}_name'
            order_key = f'existing_picture_{picture_index}_order'

            if name_key in request.form:
                picture.picture_name = request.form[name_key]
            if order_key in request.form:
                picture.picture_order = int(request.form[order_key] or picture.picture_order)

    # Process new uploaded images
    max_order = max([p.picture_order for p in component.pictures] + [0])
    for i in range(1, 11):  # Up to 10 new images
        picture_file = request.files.get(f'picture_{i}')
        if picture_file and picture_file.filename:
            try:
                file_url = save_uploaded_file(picture_file)
                if file_url:
                    max_order += 1
                    picture = Picture(
                        component_id=component.id,
                        picture_name=picture_file.filename,
                        url=file_url,
                        picture_order=max_order
                    )
                    db.session.add(picture)
            except Exception as e:
                current_app.logger.error(f"Error uploading new image {i}: {str(e)}")

# Helper functions for variant image processing
def _process_variant_images(variant, request):
    """Process image uploads for a variant with auto-assigned order - enhanced for new frontend."""
    uploaded_count = 0
    picture_order = 1

    for i in range(1, 11):  # Up to 10 pictures per variant
        picture_file = request.files.get(f'variant_picture_{i}')

        if picture_file and picture_file.filename:
            try:
                # Use the improved save_uploaded_file function
                file_url = save_uploaded_file(picture_file, 'variant_uploads')
                if file_url:
                    picture = Picture(
                        variant_id=variant.id,
                        picture_name=picture_file.filename,
                        url=file_url,
                        picture_order=picture_order
                    )
                    db.session.add(picture)
                    uploaded_count += 1
                    picture_order += 1

            except Exception as e:
                current_app.logger.error(f"Error uploading variant image {i}: {str(e)}")
                continue

    return uploaded_count

def _update_variant_images(variant, request):
    """Update variant images, handling both new uploads and existing images - enhanced for new frontend."""
    # Handle existing picture updates
    for picture in variant.variant_pictures:
        picture_index = None
        for i, existing_picture in enumerate(variant.variant_pictures, 1):
            if existing_picture.id == picture.id:
                picture_index = i
                break

        if picture_index:
            name_key = f'existing_variant_picture_{picture_index}_name'
            order_key = f'existing_variant_picture_{picture_index}_order'

            if name_key in request.form:
                picture.picture_name = request.form[name_key]
            if order_key in request.form:
                picture.picture_order = int(request.form[order_key] or picture.picture_order)

    # Process new uploaded images
    max_order = max([p.picture_order for p in variant.variant_pictures] + [0])
    for i in range(1, 11):  # Up to 10 new images
        picture_file = request.files.get(f'variant_picture_{i}')
        if picture_file and picture_file.filename:
            try:
                file_url = save_uploaded_file(picture_file, 'variant_uploads')
                if file_url:
                    max_order += 1
                    picture = Picture(
                        variant_id=variant.id,
                        picture_name=picture_file.filename,
                        url=file_url,
                        picture_order=max_order
                    )
                    db.session.add(picture)
            except Exception as e:
                current_app.logger.error(f"Error uploading new variant image {i}: {str(e)}")

@main.route('/api/brands/search')
def api_search_brands():
    """API endpoint for brand search with autocomplete."""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)

        if len(query) < 1:
            return jsonify([])

        brands = Brand.query.filter(
            Brand.name.ilike(f'%{query}%')
        ).limit(limit).all()

        results = [{
            'id': b.id,
            'name': b.name,
            'components_count': b.get_components_count(),
            'subbrands_count': len(b.subbrands)
        } for b in brands]

        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"Error in brand search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

def get_brands_list(self):
    """Get brands for this component (with caching support)"""
    # Check if we have cached brands from the index route
    if hasattr(self, '_cached_brands'):
        return [type('Brand', (), brand) for brand in self._cached_brands]

    # Fallback to normal relationship access
    return list(self.brands)

@main.route('/api/components/<int:component_id>/brands', methods=['GET', 'POST', 'DELETE'])
def api_component_brands(component_id):
    """API endpoint to manage component brand associations"""
    try:
        component = Component.query.get_or_404(component_id)

        if request.method == 'GET':
            # Return current brands for this component
            brands = [{
                'id': brand.id,
                'name': brand.name
            } for brand in component.brands]
            return jsonify(brands)

        elif request.method == 'POST':
            # Add brand to component
            data = request.get_json()
            brand_id = data.get('brand_id')

            if not brand_id:
                return jsonify({'success': False, 'error': 'Brand ID required'}), 400

            brand = Brand.query.get(brand_id)
            if not brand:
                return jsonify({'success': False, 'error': 'Brand not found'}), 404

            if brand not in component.brands:
                component.add_brand(brand)
                db.session.commit()
                return jsonify({'success': True, 'message': f'Brand {brand.name} added'})
            else:
                return jsonify({'success': False, 'error': 'Brand already associated'}), 400

        elif request.method == 'DELETE':
            # Remove brand from component
            data = request.get_json()
            brand_id = data.get('brand_id')

            if not brand_id:
                return jsonify({'success': False, 'error': 'Brand ID required'}), 400

            brand = Brand.query.get(brand_id)
            if not brand:
                return jsonify({'success': False, 'error': 'Brand not found'}), 404

            if brand in component.brands:
                component.remove_brand(brand)
                db.session.commit()
                return jsonify({'success': True, 'message': f'Brand {brand.name} removed'})
            else:
                return jsonify({'success': False, 'error': 'Brand not associated'}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error managing component brands: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers for better UX
@main.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@main.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

@main.errorhandler(RequestEntityTooLarge)
def file_too_large_error(error):
    """Handle file upload size errors"""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(request.url or url_for('main.index'))

@main.route('/download/csv-template')
def download_csv_template():
    """Generate and download CSV template - UPDATED with brand fields."""
    try:
        # Create CSV template with brand fields
        template_data = [
            [
                'product_number', 'description', 'component_type', 'supplier_code',
                'category_name', 'keywords', 'material', 'color', 'gender', 'style',
                'brands', 'subbrand', 'size', 'finish', 'weight',  # NEW: Added 'brands' field
                'picture_1_name', 'picture_1_url',
                'picture_2_name', 'picture_2_url',
                'picture_3_name', 'picture_3_url',
                'picture_4_name', 'picture_4_url',
                'picture_5_name', 'picture_5_url'
            ],
            [
                'F-WL001', 'Shiny polyester 50D fabric', 'Fabrics', 'SUPP001',
                'Polyester Fabrics', 'shiny,polyester,jacket,outerwear', 'polyester', 'silver',
                'ladies,unisex', 'casual', 'MAR,MMC', 'MAR Sport,MMC Pro', '50D', 'waterproof', '120gsm',  # NEW: Example brand data
                'fabric_front.jpg', 'http://example.com/fabric_front.jpg',
                'fabric_detail.jpg', 'http://example.com/fabric_detail.jpg',
                '', '', '', '', '', ''
            ]
        ]

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        for row in template_data:
            writer.writerow(row)

        # Create file-like object
        csv_data = output.getvalue()
        output.close()

        # Return as downloadable file
        return current_app.response_class(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=component_template.csv'
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error generating CSV template: {str(e)}")
        flash('Error generating template', 'danger')
        return redirect(url_for('main.upload_csv'))

def _process_component_properties(component, component_type_name, form_data):
    """Process component properties based on component type - UPDATED to use database-driven properties"""
    # Get properties from database for this component type
    component_type = ComponentType.query.filter_by(name=component_type_name).first()
    if not component_type:
        return
    
    type_properties = ComponentTypeProperty.query.filter_by(component_type_id=component_type.id).order_by(ComponentTypeProperty.display_order).all()
    
    # Initialize properties dict if it doesn't exist
    if not hasattr(component, 'properties') or component.properties is None:
        component.properties = {}

    for prop in type_properties:
        prop_value = form_data.get(prop.property_name)
        if prop_value:
            # Handle different property types
            if prop.property_type == 'multiselect':
                if isinstance(prop_value, list):
                    component.properties[prop.property_name] = {
                        'value': prop_value,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                else:
                    # Convert string to array if needed
                    values = [v.strip() for v in prop_value.split(',') if v.strip()]
                    if values:
                        component.properties[prop.property_name] = {
                            'value': values,
                            'updated_at': datetime.utcnow().isoformat()
                        }
            else:
                # For text and select types
                component.properties[prop.property_name] = {
                    'value': prop_value,
                    'updated_at': datetime.utcnow().isoformat()
                }