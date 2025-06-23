from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Component, ComponentType, Supplier, Category, Brand, ComponentBrand, Picture, ComponentVariant, Keyword, keyword_component, ComponentTypeProperty, Color
from sqlalchemy import or_, and_, func, desc, asc
from sqlalchemy.orm import joinedload
import os
import uuid
from datetime import datetime, timedelta

component_web = Blueprint('component_web', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 200
SHOW_ALL_LIMIT = 1000


def _get_form_data():
    """Extract common form data"""
    return {
        'product_number': request.form.get('product_number', '').strip(),
        'description': request.form.get('description', '').strip(),
        'supplier_id': request.form.get('supplier_id', type=int),
        'category_id': request.form.get('category_id', type=int),
        'component_type_id': request.form.get('component_type_id', type=int)
    }


def _validate_required_fields(form_data):
    """Validate required form fields"""
    if not form_data['product_number']:
        flash('Product number is required.', 'error')
        return False
    
    if not form_data['component_type_id']:
        flash('Component type is required.', 'error')
        return False
    
    return True


def _handle_component_properties(component, component_type_id):
    """Handle dynamic component properties"""
    if component_type_id:
        type_properties = ComponentTypeProperty.query.filter_by(
            component_type_id=component_type_id
        ).all()
        
        properties = {}
        for prop in type_properties:
            value = request.form.get(f'property_{prop.property_name}')
            if value:
                properties[prop.property_name] = value
        
        component.properties = properties


def _handle_brand_associations(component, is_edit=False):
    """Handle component-brand associations"""
    if is_edit:
        # Remove existing associations for edit
        ComponentBrand.query.filter_by(component_id=component.id).delete()
    
    brand_ids = request.form.getlist('brand_ids[]')
    for brand_id in brand_ids:
        if brand_id.isdigit():
            brand_assoc = ComponentBrand(
                component_id=component.id,
                brand_id=int(brand_id)
            )
            db.session.add(brand_assoc)


def _handle_keywords(component, is_edit=False):
    """Handle component keywords"""
    keywords_input = request.form.get('keywords', '').strip()
    
    if is_edit:
        component.keywords.clear()
    
    if keywords_input:
        keyword_names = [k.strip() for k in keywords_input.split(',') if k.strip()]
        for keyword_name in keyword_names:
            keyword = Keyword.query.filter_by(name=keyword_name).first()
            if not keyword:
                keyword = Keyword(name=keyword_name)
                db.session.add(keyword)
                db.session.flush()
            
            if not is_edit and keyword not in component.keywords:
                component.keywords.append(keyword)
            elif is_edit:
                component.keywords.append(keyword)


def _handle_picture_uploads(component, is_edit=False):
    """Handle picture uploads"""
    if is_edit:
        pictures = request.files.getlist('new_pictures')
        max_order = db.session.query(func.max(Picture.picture_order)).filter_by(
            component_id=component.id
        ).scalar() or 0
        picture_order = max_order + 1
    else:
        pictures = request.files.getlist('pictures')
        picture_order = 1
    
    for picture_file in pictures:
        if picture_file and allowed_file(picture_file.filename):
            url = save_uploaded_file(picture_file)
            if url:
                picture = Picture(
                    component_id=component.id,
                    url=url,
                    picture_order=picture_order,
                    alt_text=f"{component.product_number} - Image {picture_order}"
                )
                db.session.add(picture)
                picture_order += 1


def _get_form_context_data():
    """Get common context data for forms"""
    return {
        'component_types': ComponentType.query.order_by(ComponentType.name).all(),
        'suppliers': Supplier.query.order_by(Supplier.supplier_code).all(),
        'categories': Category.query.order_by(Category.name).all(),
        'brands': Brand.query.order_by(Brand.name).all(),
        'colors': Color.query.order_by(Color.name).all()
    }


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, folder='uploads'):
    """Save uploaded file"""
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Create upload directory if it doesn't exist
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_path, unique_filename)
            file.save(file_path)
            
            # Return relative URL for web access
            return f"/static/uploads/{unique_filename}"
            
        except Exception as e:
            current_app.logger.error(f"File upload error: {str(e)}")
            flash(f'Error uploading file: {str(e)}', 'error')
            return None
    return None


@component_web.route('/')
@component_web.route('/components')
def index():
    """
    Main components listing with advanced pagination and filtering
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
        
        # Get filter parameters with multi-select support
        search = request.args.get('search', '', type=str).strip()
        
        # Multi-select parameters
        component_type_ids = request.args.getlist('component_type_id')
        component_type_ids = [int(id) for id in component_type_ids if id.isdigit()]
        
        supplier_ids = request.args.getlist('supplier_id')
        supplier_ids = [int(id) for id in supplier_ids if id.isdigit()]
        
        brand_ids = request.args.getlist('brand_id')
        brand_ids = [int(id) for id in brand_ids if id.isdigit()]
        
        # Single-select parameters
        status = request.args.get('status', type=str)
        recent = request.args.get('recent', type=int)
        
        # Sort parameters
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_order = request.args.get('sort_order', 'desc', type=str)
        
        # Build base query with optimized loading
        query = Component.query.options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.pictures),
            joinedload(Component.keywords)
        )
        
        # Apply filters
        filters = []
        
        # Search filter - INCLUDING KEYWORDS
        if search:
            keyword_subquery = db.session.query(keyword_component.c.component_id).join(
                Keyword, keyword_component.c.keyword_id == Keyword.id
            ).filter(
                Keyword.name.ilike(f'%{search}%')
            ).subquery()
            
            search_filter = or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%'),
                and_(
                    Component.supplier_id.isnot(None),
                    Component.supplier.has(Supplier.supplier_code.ilike(f'%{search}%'))
                ),
                Component.component_type.has(ComponentType.name.ilike(f'%{search}%')),
                Component.id.in_(keyword_subquery)
            )
            filters.append(search_filter)
        
        # Multi-select filters
        if component_type_ids:
            filters.append(Component.component_type_id.in_(component_type_ids))
        
        if supplier_ids:
            filters.append(Component.supplier_id.in_(supplier_ids))
        
        if brand_ids:
            brand_components_subquery = db.session.query(ComponentBrand.component_id).filter(
                ComponentBrand.brand_id.in_(brand_ids)
            ).subquery()
            filters.append(Component.id.in_(brand_components_subquery))
        
        # Status filter
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
        
        # Recent filter
        if recent:
            date_threshold = datetime.now() - timedelta(days=recent)
            filters.append(Component.created_at >= date_threshold)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Apply sorting
        sort_mapping = {
            'product_number': Component.product_number,
            'description': Component.description,
            'created_at': Component.created_at,
            'updated_at': Component.updated_at,
            'proto_status': Component.proto_status,
            'sms_status': Component.sms_status,
            'pps_status': Component.pps_status
        }
        
        if sort_by in sort_mapping:
            order_column = sort_mapping[sort_by]
            if sort_order == 'desc':
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(Component.created_at))
        
        # Handle show all
        if show_all:
            total_count = query.count()
            if total_count > SHOW_ALL_LIMIT:
                flash(f'Too many results ({total_count}). Showing first {SHOW_ALL_LIMIT} items.', 'warning')
                components = query.limit(SHOW_ALL_LIMIT).all()
            else:
                components = query.all()
            
            # Create a pagination-like object for show_all case
            class PaginationLike:
                def __init__(self, items, total):
                    self.items = items
                    self.total = total
                    self.page = 1
                    self.per_page = total
                    self.pages = 1
                    self.has_prev = False
                    self.has_next = False
            
            pagination = PaginationLike(components, len(components))
        else:
            # Paginate results
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            components = pagination.items
        
        # Load variants for component previews (cached_variants functionality)
        if pagination and hasattr(pagination, 'items'):
            component_items = pagination.items
        else:
            component_items = components if isinstance(components, list) else []
        
        if component_items:
            component_ids = [comp.id for comp in component_items]
            
            # Query variants with their pictures
            variants_query = db.session.query(
                ComponentVariant.id,
                ComponentVariant.component_id,
                ComponentVariant.color_id,
                Color.name.label('color_name'),
                Picture.url.label('picture_url')
            ).outerjoin(
                Color, ComponentVariant.color_id == Color.id
            ).outerjoin(
                Picture, and_(
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
                    'name': row.color_name,  # Use color name instead of variant name
                    'color_id': row.color_id,
                    'color_name': row.color_name,
                    'picture_url': picture_url
                })

            for component in component_items:
                component._cached_variants = component_variants.get(component.id, [])

        # Get filter options
        component_types = ComponentType.query.order_by(ComponentType.name).all()
        suppliers = Supplier.query.order_by(Supplier.supplier_code).all()
        brands = Brand.query.order_by(Brand.name).all()
        categories = Category.query.order_by(Category.name).all()
        
        # Get brands count
        brands_count = Brand.query.count()
        
        # Prepare pagination info for template
        if pagination:
            pagination_info = {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'show_all': show_all
            }
        else:
            # For show_all case
            pagination_info = {
                'total': len(components),
                'page': 1,
                'per_page': len(components),
                'pages': 1,
                'has_prev': False,
                'has_next': False,
                'show_all': True
            }
        
        # Prepare current filters for template (using the name expected by template)
        current_filters = {
            'component_type_ids': component_type_ids,
            'supplier_ids': supplier_ids,
            'brand_ids': brand_ids,
            'status': status,
            'recent': recent,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        return render_template('index.html',
                             components=pagination,  # Always pass pagination object
                             component_types=component_types,
                             categories=categories,
                             suppliers=suppliers,
                             brands=brands,
                             brands_count=brands_count,
                             search=search,
                             pagination_info=pagination_info,
                             current_filters=current_filters)
    
    except Exception as e:
        current_app.logger.error(f"Index page error: {str(e)}")
        flash(f'An error occurred while loading components: {str(e)}', 'error')
        return render_template('index.html', 
                             components=None,
                             component_types=[],
                             categories=[],
                             suppliers=[],
                             brands=[],
                             brands_count=0,
                             search='',
                             pagination_info={'total': 0, 'page': 1, 'per_page': 20, 'pages': 0},
                             current_filters={
                                 'component_type_ids': [],
                                 'supplier_ids': [],
                                 'brand_ids': [],
                                 'status': '',
                                 'recent': '',
                                 'sort_by': 'created_at',
                                 'sort_order': 'desc'
                             })


@component_web.route('/component/<int:id>')
def component_detail(id):
    """
    Display detailed view of a single component
    """
    try:
        component = Component.query.options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            joinedload(Component.pictures),
            joinedload(Component.variants).joinedload(ComponentVariant.color),
            joinedload(Component.keywords)
        ).get_or_404(id)
        
        # Get component type properties
        type_properties = []
        if component.component_type:
            type_properties = ComponentTypeProperty.query.filter_by(
                component_type_id=component.component_type_id
            ).order_by(ComponentTypeProperty.display_order).all()
        
        return render_template('component_detail.html', 
                             component=component,
                             type_properties=type_properties)
    
    except Exception as e:
        current_app.logger.error(f"Component detail error: {str(e)}")
        flash('Error loading component details.', 'error')
        return redirect(url_for('component_web.index'))


@component_web.route('/component/new', methods=['GET', 'POST'])
def new_component():
    """
    Create a new component
    """
    if request.method == 'POST':
        try:
            # Get and validate form data
            form_data = _get_form_data()
            if not _validate_required_fields(form_data):
                return redirect(request.url)
            
            # Check for duplicate product number
            existing = Component.query.filter_by(
                product_number=form_data['product_number'],
                supplier_id=form_data['supplier_id']
            ).first()
            
            if existing:
                flash('A component with this product number and supplier already exists.', 'error')
                return redirect(request.url)
            
            # Create component
            component = Component(
                product_number=form_data['product_number'],
                description=form_data['description'],
                supplier_id=form_data['supplier_id'],
                category_id=form_data['category_id'],
                component_type_id=form_data['component_type_id'],
                properties={}
            )
            
            db.session.add(component)
            db.session.flush()  # Get component ID before handling associations
            
            # Handle all associations and uploads
            _handle_component_properties(component, form_data['component_type_id'])
            _handle_brand_associations(component, is_edit=False)
            _handle_keywords(component, is_edit=False)
            _handle_picture_uploads(component, is_edit=False)
            
            db.session.commit()
            flash('Component created successfully!', 'success')
            return redirect(url_for('component_web.component_detail', id=component.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Component creation error: {str(e)}")
            flash(f'Error creating component: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    context = _get_form_context_data()
    context['component'] = None
    
    return render_template('component_edit_form.html', **context)


@component_web.route('/component/edit/<int:id>', methods=['GET', 'POST'])
def edit_component(id):
    """
    Edit an existing component
    """
    component = Component.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get and validate form data
            form_data = _get_form_data()
            if not _validate_required_fields(form_data):
                return redirect(request.url)
            
            # Update basic fields
            component.product_number = form_data['product_number']
            component.description = form_data['description']
            component.supplier_id = form_data['supplier_id']
            component.category_id = form_data['category_id']
            component.component_type_id = form_data['component_type_id']
            
            # Handle all associations and uploads
            _handle_component_properties(component, form_data['component_type_id'])
            _handle_brand_associations(component, is_edit=True)
            _handle_keywords(component, is_edit=True)
            _handle_picture_uploads(component, is_edit=True)
            
            db.session.commit()
            flash('Component updated successfully!', 'success')
            return redirect(url_for('component_web.component_detail', id=component.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Component update error: {str(e)}")
            flash(f'Error updating component: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    context = _get_form_context_data()
    context['component'] = component
    
    # Get type properties for display
    type_properties = []
    if component.component_type:
        type_properties = ComponentTypeProperty.query.filter_by(
            component_type_id=component.component_type_id
        ).order_by(ComponentTypeProperty.display_order).all()
    
    context['type_properties'] = type_properties
    
    return render_template('component_edit_form.html', **context)


@component_web.route('/component/delete/<int:id>', methods=['POST'])
def delete_component(id):
    """
    Delete a component
    """
    try:
        component = Component.query.get_or_404(id)
        
        # Delete associated pictures from filesystem
        for picture in component.pictures:
            if picture.url:
                file_path = os.path.join(current_app.static_folder, picture.url.lstrip('/'))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Delete component (cascades will handle related records)
        db.session.delete(component)
        db.session.commit()
        
        flash('Component deleted successfully!', 'success')
        return redirect(url_for('component_web.index'))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Component deletion error: {str(e)}")
        flash(f'Error deleting component: {str(e)}', 'error')
        return redirect(url_for('component_web.component_detail', id=id))


@component_web.route('/component/<int:id>/status/proto', methods=['POST'])
def update_proto_status(id):
    """Update component proto status"""
    try:
        component = Component.query.get_or_404(id)
        
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()
        
        if status not in ['ok', 'not_ok', 'pending']:
            flash('Invalid status value.', 'error')
            return redirect(url_for('component_web.component_detail', id=id))
        
        component.proto_status = status
        component.proto_comment = comment if comment else None
        component.proto_date = datetime.now(datetime.UTC) if status != 'pending' else None
        
        db.session.commit()
        flash('Proto status updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Proto status update error: {str(e)}")
        flash('Error updating proto status.', 'error')
    
    return redirect(url_for('component_web.component_detail', id=id))


@component_web.route('/component/<int:id>/status/sms', methods=['POST'])
def update_sms_status(id):
    """Update component SMS status"""
    try:
        component = Component.query.get_or_404(id)
        
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()
        
        if status not in ['ok', 'not_ok', 'pending']:
            flash('Invalid status value.', 'error')
            return redirect(url_for('component_web.component_detail', id=id))
        
        component.sms_status = status
        component.sms_comment = comment if comment else None
        component.sms_date = datetime.now(datetime.UTC) if status != 'pending' else None
        
        db.session.commit()
        flash('SMS status updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"SMS status update error: {str(e)}")
        flash('Error updating SMS status.', 'error')
    
    return redirect(url_for('component_web.component_detail', id=id))


@component_web.route('/component/<int:id>/status/pps', methods=['POST'])
def update_pps_status(id):
    """Update component PPS status"""
    try:
        component = Component.query.get_or_404(id)
        
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()
        
        if status not in ['ok', 'not_ok', 'pending']:
            flash('Invalid status value.', 'error')
            return redirect(url_for('component_web.component_detail', id=id))
        
        component.pps_status = status
        component.pps_comment = comment if comment else None
        component.pps_date = datetime.now(datetime.UTC) if status != 'pending' else None
        
        db.session.commit()
        flash('PPS status updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"PPS status update error: {str(e)}")
        flash('Error updating PPS status.', 'error')
    
    return redirect(url_for('component_web.component_detail', id=id))