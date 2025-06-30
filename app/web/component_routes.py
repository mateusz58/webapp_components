from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, session
from werkzeug.utils import secure_filename
from app import db
from app.models import Component, ComponentType, Supplier, Category, Brand, ComponentBrand, Picture, ComponentVariant, Keyword, keyword_component, ComponentTypeProperty, Color
from app.utils.file_handling import save_uploaded_file, allowed_file, delete_file
from sqlalchemy import or_, and_, func, desc, asc
from sqlalchemy.orm import joinedload, selectinload
import os
import uuid
import time
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


def _validate_component_variants(is_edit=False, component_id=None):
    """Validate component variants and their pictures"""
    errors = []
    
    # Check if component has at least one variant
    has_variants = False
    variant_count = 0
    
    # Check existing variants (for edit mode)
    if is_edit and component_id:
        existing_variants = ComponentVariant.query.filter_by(component_id=component_id).all()
        for variant in existing_variants:
            variant_key = f'variant_color_{variant.id}'
            if variant_key in request.form:
                has_variants = True
                variant_count += 1
                
                # Check if this variant has pictures
                picture_files = request.files.getlist(f'variant_images_{variant.id}[]')
                existing_pictures = request.form.getlist('existing_pictures')
                variant_pictures = [p for p in variant.variant_pictures if str(p.id) in existing_pictures]
                
                if not picture_files and not variant_pictures:
                    color_name = variant.color.name if variant.color else "Unknown"
                    errors.append(f'Variant "{color_name}" must have at least one picture.')
    
    # Check new variants
    new_variant_count = 1
    while True:
        color_key = f'variant_color_new_{new_variant_count}'
        if color_key not in request.form:
            break
            
        color_id = request.form.get(color_key)
        custom_color_key = f'variant_custom_color_new_{new_variant_count}'
        custom_color_name = request.form.get(custom_color_key, '').strip()
        
        # Check if color is selected
        if color_id or custom_color_name:
            has_variants = True
            variant_count += 1
            
            # Check if this variant has pictures
            picture_files = request.files.getlist(f'variant_images_new_{new_variant_count}[]')
            valid_files = [f for f in picture_files if f and f.filename and allowed_file(f.filename)]
            
            if not valid_files:
                color_display = custom_color_name if custom_color_name else f"Color ID {color_id}"
                errors.append(f'Variant "{color_display}" must have at least one picture.')
        
        new_variant_count += 1
    
    # Check if component has at least one variant
    if not has_variants:
        errors.append('Component must have at least one color variant.')
    
    return errors


def _validate_duplicate_product_number(product_number, supplier_id, component_id=None):
    """Check for duplicate product number with same supplier"""
    query = Component.query.filter_by(
        product_number=product_number,
        supplier_id=supplier_id
    )
    
    # Exclude current component in edit mode
    if component_id:
        query = query.filter(Component.id != component_id)
    
    existing = query.first()
    
    if existing:
        supplier_name = existing.supplier.supplier_code if existing.supplier else "No Supplier"
        return f'A component with product number "{product_number}" already exists for supplier "{supplier_name}".'
    
    return None


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


def _handle_categories(component, is_edit=False):
    """Handle component-category associations"""
    # Try to get category_ids[] (multiple categories) or fall back to category_id (single category)
    category_ids = request.form.getlist('category_ids[]')
    if not category_ids:
        # Fall back to single category_id for backward compatibility
        single_category_id = request.form.get('category_id')
        if single_category_id:
            category_ids = [single_category_id]
    
    if is_edit:
        component.categories.clear()
    
    for category_id in category_ids:
        if category_id and str(category_id).isdigit():
            category = Category.query.get(int(category_id))
            if category and category not in component.categories:
                component.categories.append(category)


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


def _handle_variants(component, is_edit=False):
    """Handle component variants and their pictures"""
    
    all_pending_pictures = []
    
    if is_edit:
        # Handle existing variants - check for updates/removals
        existing_variant_ids = []
        for variant in component.variants:
            variant_key = f'variant_color_{variant.id}'
            if variant_key in request.form:
                # Update variant color if changed
                new_color_id = request.form.get(variant_key, type=int)
                custom_color_key = f'variant_custom_color_{variant.id}'
                
                # Handle custom color creation
                if new_color_id == 0 or request.form.get(variant_key) == 'custom':
                    custom_color_name = request.form.get(custom_color_key, '').strip()
                    if custom_color_name:
                        # Create new color
                        new_color = Color(name=custom_color_name)
                        db.session.add(new_color)
                        db.session.flush()
                        new_color_id = new_color.id
                
                if new_color_id and new_color_id != variant.color_id:
                    # Color changed - mark for picture renaming
                    variant.color_id = new_color_id
                    # SKU will be regenerated by database trigger
                    # Picture names will be regenerated and files renamed after commit
                
                existing_variant_ids.append(variant.id)
                
                # Handle variant picture uploads (returns pending pictures)
                pending_pictures = _handle_variant_pictures(variant, variant.id)
                all_pending_pictures.extend(pending_pictures)
            else:
                # Variant was removed - delete it (cascade will handle pictures)
                db.session.delete(variant)
    
    # Handle new variants
    new_variant_count = 1
    while True:
        color_key = f'variant_color_new_{new_variant_count}'
        if color_key not in request.form:
            break
            
        color_id = request.form.get(color_key, type=int)
        custom_color_key = f'variant_custom_color_new_{new_variant_count}'
        
        # Handle custom color for new variant
        if color_id == 0 or request.form.get(color_key) == 'custom':
            custom_color_name = request.form.get(custom_color_key, '').strip()
            if custom_color_name:
                # Create new color
                new_color = Color(name=custom_color_name)
                db.session.add(new_color)
                db.session.flush()
                color_id = new_color.id
        
        if color_id:
            # Create new variant
            variant = ComponentVariant(
                component_id=component.id,
                color_id=color_id,
                is_active=True
            )
            db.session.add(variant)
            db.session.flush()  # Get variant ID for pictures
            
            # Handle pictures for new variant (returns pending pictures)
            pending_pictures = _handle_variant_pictures(variant, f'new_{new_variant_count}')
            all_pending_pictures.extend(pending_pictures)
        
        new_variant_count += 1
    
    return all_pending_pictures


def _handle_variant_pictures(variant, variant_form_id):
    """Handle picture uploads and management for a specific variant"""
    import os
    import io
    
    # Handle new picture uploads
    picture_files = request.files.getlist(f'variant_images_{variant_form_id}[]')
    
    # Get current max order for this variant
    max_order = db.session.query(func.max(Picture.picture_order)).filter_by(
        variant_id=variant.id
    ).scalar() or 0
    
    # Store file data in memory until we have the database-generated names
    pending_pictures = []
    
    for picture_file in picture_files:
        if picture_file and allowed_file(picture_file.filename):
            # Read file into memory
            file_data = io.BytesIO(picture_file.read())
            file_ext = os.path.splitext(picture_file.filename)[1].lower()
            max_order += 1
            
            # Create picture record (database trigger will generate picture_name)
            picture = Picture(
                component_id=variant.component_id,
                variant_id=variant.id,
                url='',  # Will be set after we save the file with proper name
                picture_order=max_order,
                alt_text=f"{variant.component.product_number} - {variant.color.name} - Image {max_order}"
            )
            db.session.add(picture)
            
            # Store file data for later saving
            pending_pictures.append({
                'picture': picture,
                'file_data': file_data,
                'extension': file_ext
            })
    
    # Handle existing pictures (for edit mode)
    if isinstance(variant_form_id, int):  # Only for existing variants
        # Check which pictures to keep
        existing_picture_ids = request.form.getlist('existing_pictures')
        for picture in variant.variant_pictures:
            if str(picture.id) not in existing_picture_ids:
                # Delete the file
                if picture.url:
                    delete_file(picture.url)
                # Delete the record (will be handled by cascade)
                db.session.delete(picture)
    
    return pending_pictures


def _handle_picture_renames(component, old_data=None):
    """Handle renaming of existing picture files when component/supplier/color data changes"""
    import os
    
    webdav_prefix = current_app.config.get('UPLOAD_URL_PREFIX', 'http://31.182.67.115/webdav/components')
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
    
    # Get all pictures for this component
    all_pictures = Picture.query.filter_by(component_id=component.id).all()
    
    for picture in all_pictures:
        if picture.url:
            try:
                # Get current filename from URL
                current_filename = picture.url.split('/')[-1]
                current_path = os.path.join(upload_folder, current_filename)
                
                # Refresh picture to get new database-generated name
                db.session.refresh(picture)
                
                if picture.picture_name:
                    # Get file extension from current filename
                    ext = os.path.splitext(current_filename)[1]
                    new_filename = f"{picture.picture_name}{ext}"
                    new_path = os.path.join(upload_folder, new_filename)
                    
                    # Only rename if filename actually changed
                    if current_filename != new_filename:
                        if os.path.exists(current_path):
                            # Remove new file if it exists (shouldn't happen but safety)
                            if os.path.exists(new_path):
                                os.remove(new_path)
                            
                            # Rename file
                            os.rename(current_path, new_path)
                            
                            # Update URL in database
                            picture.url = f"{webdav_prefix}/{new_filename}"
                            db.session.add(picture)
                            
                            current_app.logger.info(f"Renamed picture from {current_filename} to {new_filename}")
                        
            except Exception as e:
                current_app.logger.error(f"Error renaming picture {picture.id}: {str(e)}")
                continue


def _handle_picture_deletions(component):
    """Handle deletion of pictures marked for removal"""
    
    # Handle component picture deletions
    pictures_to_delete = request.form.getlist('delete_pictures')
    for picture_id in pictures_to_delete:
        if picture_id.isdigit():
            picture = Picture.query.filter_by(
                id=int(picture_id),
                component_id=component.id,
                variant_id=None  # Component pictures only
            ).first()
            
            if picture:
                # Delete file from disk
                if picture.url:
                    delete_file(picture.url)
                
                # Delete from database
                db.session.delete(picture)
    
    # Handle variant picture deletions (already handled in _handle_variant_pictures)
    # This is handled per-variant in the variant processing


def _verify_images_accessible(component_id, max_retries=3, retry_delay=2):
    """Fast parallel verification of image accessibility"""
    import requests
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    current_app.logger.info(f"Starting fast image verification for component {component_id}")
    
    # Get fresh component data with optimized query
    component = Component.query.options(
        selectinload(Component.pictures),
        selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures)
    ).get(component_id)
    
    if not component:
        current_app.logger.error(f"Component {component_id} not found for verification")
        return False
    
    # Collect all image URLs
    all_urls = []
    for picture in component.pictures:
        if picture.url:
            all_urls.append(picture.url)
    
    for variant in component.variants:
        for picture in variant.variant_pictures:
            if picture.url:
                all_urls.append(picture.url)
    
    if not all_urls:
        current_app.logger.info(f"No images to verify for component {component_id}")
        return True
    
    current_app.logger.info(f"Verifying {len(all_urls)} images in parallel for component {component_id}")
    
    def check_single_url(url):
        """Check a single URL with optimized settings"""
        try:
            response = requests.head(url, timeout=3, allow_redirects=False)
            return url, response.status_code == 200, response.status_code
        except Exception as e:
            return url, False, str(e)
    
    for attempt in range(1, max_retries + 1):
        current_app.logger.info(f"Verification attempt {attempt}/{max_retries}")
        
        failed_urls = []
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=min(10, len(all_urls))) as executor:
            future_to_url = {executor.submit(check_single_url, url): url for url in all_urls}
            
            for future in as_completed(future_to_url, timeout=15):
                url, success, status = future.result()
                if not success:
                    failed_urls.append(f"{url} ({status})")
        
        if not failed_urls:
            current_app.logger.info(f"All {len(all_urls)} images verified accessible for component {component_id}")
            return True
        else:
            current_app.logger.warning(f"Attempt {attempt}: {len(failed_urls)} images not accessible")
            
            if attempt < max_retries:
                current_app.logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
    
    current_app.logger.error(f"Image verification failed after {max_retries} attempts for component {component_id}")
    return False


def _save_pending_pictures(pending_pictures):
    """Save pending pictures with database-generated names to /components/"""
    import os
    from PIL import Image
    
    webdav_prefix = current_app.config.get('UPLOAD_URL_PREFIX', 'http://31.182.67.115/webdav/components')
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
    
    # Track saved files for rollback
    saved_files = []
    
    try:
        for pending in pending_pictures:
            picture = pending['picture']
            file_data = pending['file_data']
            extension = pending['extension']
            
            try:
                # Refresh picture from database to get the generated picture_name
                db.session.flush()  # Ensure the picture is in database first
                db.session.refresh(picture)
                
                if not picture.picture_name:
                    current_app.logger.error(f"No picture_name generated for picture {picture.id}")
                    continue
                
                # Final filename with extension - ALL pictures go directly in /components/
                filename = f"{picture.picture_name}{extension}"
                file_path = os.path.join(upload_folder, filename)
                
                # Save the file from memory
                file_data.seek(0)
                
                # Optimize image if it's an image file
                if extension.lower() in ['.jpg', '.jpeg', '.png']:
                    try:
                        image = Image.open(file_data)
                        
                        # Convert RGBA to RGB if necessary
                        if image.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', image.size, (255, 255, 255))
                            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                            image = background
                        
                        # Resize if larger than max size
                        max_size = (1920, 1920)
                        image.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Save optimized image
                        image.save(file_path, format='JPEG', quality=85, optimize=True)
                    except Exception as e:
                        # If optimization fails, save original
                        current_app.logger.warning(f"Image optimization failed, saving original: {e}")
                        file_data.seek(0)
                        with open(file_path, 'wb') as f:
                            f.write(file_data.read())
                else:
                    # Save non-image files directly
                    with open(file_path, 'wb') as f:
                        f.write(file_data.read())
                
                # Track saved file for potential rollback
                saved_files.append(file_path)
                
                # Set the proper URL - direct path, no subfolders
                picture.url = f"{webdav_prefix}/{filename}"
                db.session.add(picture)
                
                current_app.logger.info(f"Set picture URL for {picture.id}: {picture.url}")
                current_app.logger.info(f"Picture saved to: {file_path}")
                
            except Exception as e:
                current_app.logger.error(f"Error saving picture {picture.id}: {str(e)}")
                # Continue with other pictures even if one fails
                continue
        
        # Commit all URL updates in batch
        db.session.commit()
        current_app.logger.info(f"Committed URLs for {len(pending_pictures)} pictures")
            
    except Exception as e:
        current_app.logger.error(f"Error committing picture URLs: {str(e)}")
        db.session.rollback()
        
        # Clean up any saved files on failure
        for file_path in saved_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    current_app.logger.info(f"Cleaned up file after rollback: {file_path}")
                except Exception as cleanup_error:
                    current_app.logger.error(f"Failed to clean up file {file_path}: {cleanup_error}")
        
        raise


def _get_form_context_data():
    """Get common context data for forms"""
    return {
        'component_types': ComponentType.query.order_by(ComponentType.name).all(),
        'suppliers': Supplier.query.order_by(Supplier.supplier_code).all(),
        'categories': Category.query.order_by(Category.name).all(),
        'brands': Brand.query.order_by(Brand.name).all(),
        'colors': Color.query.order_by(Color.name).all()
    }


# File handling functions are imported from app.utils.file_handling


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
            selectinload(Component.keywords)
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
        # Clear any existing session state to avoid caching issues
        db.session.expunge_all()
        
        # Force fresh query to avoid any session caching issues
        # Using selectinload for better performance with multiple collections
        component = Component.query.options(
            joinedload(Component.component_type),
            joinedload(Component.supplier),
            selectinload(Component.pictures),
            selectinload(Component.variants).joinedload(ComponentVariant.color),
            selectinload(Component.variants).selectinload(ComponentVariant.variant_pictures),
            selectinload(Component.keywords),
            selectinload(Component.brand_associations).joinedload(ComponentBrand.brand),
            selectinload(Component.categories)
        ).get_or_404(id)
        
        # Explicitly refresh variant pictures to ensure they're loaded
        for variant in component.variants:
            db.session.refresh(variant)
            for picture in variant.variant_pictures:
                db.session.refresh(picture)
        
        # Get component type properties
        type_properties = []
        if component.component_type:
            type_properties = ComponentTypeProperty.query.filter_by(
                component_type_id=component.component_type_id
            ).order_by(ComponentTypeProperty.display_order).all()
        
        # Debug logging for picture investigation
        current_app.logger.info(f"Component {component.id} loaded for detail view")
        current_app.logger.info(f"Component has {len(component.pictures)} component pictures")
        for comp_pic in component.pictures:
            current_app.logger.info(f"  Component picture {comp_pic.id}: {comp_pic.picture_name}, URL: {comp_pic.url}")
        
        current_app.logger.info(f"Component has {len(component.variants)} variants")
        for variant in component.variants:
            current_app.logger.info(f"Variant {variant.id} ({variant.color.name}) has {len(variant.variant_pictures)} pictures")
            for picture in variant.variant_pictures:
                current_app.logger.info(f"  Variant picture {picture.id}: {picture.picture_name}, URL: {picture.url}")
                
        # Check if picture files exist on filesystem
        import os
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/components')
        for variant in component.variants:
            for picture in variant.variant_pictures:
                if picture.url:
                    filename = picture.url.split('/')[-1]
                    file_path = os.path.join(upload_folder, filename)
                    file_exists = os.path.exists(file_path)
                    current_app.logger.info(f"File {filename} exists on disk: {file_exists}")
        
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
            duplicate_error = _validate_duplicate_product_number(
                form_data['product_number'], 
                form_data['supplier_id']
            )
            if duplicate_error:
                flash(duplicate_error, 'error')
                return redirect(request.url)
            
            # Validate variants and pictures
            variant_errors = _validate_component_variants(is_edit=False)
            if variant_errors:
                for error in variant_errors:
                    flash(error, 'error')
                return redirect(request.url)
            
            # Create component
            component = Component(
                product_number=form_data['product_number'],
                description=form_data['description'],
                supplier_id=form_data['supplier_id'],
                component_type_id=form_data['component_type_id'],
                properties={}
            )
            
            db.session.add(component)
            db.session.flush()  # Get component ID before handling associations
            
            # Handle all associations and uploads
            _handle_component_properties(component, form_data['component_type_id'])
            _handle_categories(component, is_edit=False)
            _handle_brand_associations(component, is_edit=False)
            _handle_keywords(component, is_edit=False)
            _handle_picture_uploads(component, is_edit=False)
            pending_pictures = _handle_variants(component, is_edit=False)
            
            # Commit to trigger database functions (SKU generation, picture naming)
            db.session.commit()
            
            # Store component ID before session operations
            component_id = component.id
            
            # Now save pictures with proper names (single commit)
            _save_pending_pictures(pending_pictures)
            
            # Clear session cache to ensure fresh data load on redirect
            db.session.expunge_all()
            
            current_app.logger.info(f"Component {component_id} creation completed, starting background verification")
            
            # Store creation completion in session for status checking
            session[f'component_creation_{component_id}'] = {
                'status': 'verifying',
                'created_at': time.time()
            }
            
            # Start background verification (async-like using threading)
            import threading
            
            def verify_in_background():
                try:
                    images_verified = _verify_images_accessible(component_id)
                    session[f'component_creation_{component_id}'] = {
                        'status': 'ready' if images_verified else 'ready_with_warning',
                        'created_at': time.time(),
                        'verified': images_verified
                    }
                    current_app.logger.info(f"Background verification completed for component {component_id}: {images_verified}")
                except Exception as e:
                    current_app.logger.error(f"Background verification failed for component {component_id}: {e}")
                    session[f'component_creation_{component_id}'] = {
                        'status': 'ready_with_warning',
                        'created_at': time.time(),
                        'verified': False
                    }
            
            # Start verification in background
            verification_thread = threading.Thread(target=verify_in_background)
            verification_thread.daemon = True
            verification_thread.start()
            
            # Redirect immediately to loading page
            flash('Component is being created...', 'info')
            return redirect(url_for('component_web.component_creation_loading', component_id=component_id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Component creation error: {str(e)}")
            flash(f'Error creating component: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    context = _get_form_context_data()
    context['component'] = None
    
    return render_template('component_edit_form.html', **context)


@component_web.route('/component/creation-loading/<int:component_id>')
def component_creation_loading(component_id):
    """Show loading page while component creation completes"""
    # Verify component exists
    component = Component.query.get_or_404(component_id)
    
    return render_template('component_creation_loading.html', component_id=component_id)


@component_web.route('/api/component/creation-status/<int:component_id>')
def check_creation_status(component_id):
    """Check if component creation and verification is complete"""
    import time
    
    # Get status from session
    session_key = f'component_creation_{component_id}'
    creation_info = session.get(session_key)
    
    if not creation_info:
        # If no session info, assume it's ready (fallback)
        return jsonify({'ready': True, 'verified': False})
    
    status = creation_info.get('status', 'verifying')
    created_at = creation_info.get('created_at', time.time())
    verified = creation_info.get('verified', False)
    
    # Auto-complete after 20 seconds regardless of verification status
    if time.time() - created_at > 20:
        # Clean up session
        session.pop(session_key, None)
        return jsonify({'ready': True, 'verified': verified, 'timeout': True})
    
    # Check if ready
    if status in ['ready', 'ready_with_warning']:
        # Clean up session
        session.pop(session_key, None)
        return jsonify({'ready': True, 'verified': verified})
    
    return jsonify({'ready': False, 'status': status})


@component_web.route('/component/edit/<int:id>', methods=['GET', 'POST'])
def edit_component(id):
    """
    Edit an existing component
    """
    component = Component.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Capture old data for comparison
            old_data = {
                'product_number': component.product_number,
                'supplier_id': component.supplier_id,
                'variant_colors': {v.id: v.color_id for v in component.variants}
            }
            
            # Get and validate form data
            form_data = _get_form_data()
            if not _validate_required_fields(form_data):
                return redirect(request.url)
            
            # Check if key fields changed (affects picture naming)
            product_changed = component.product_number != form_data['product_number']
            supplier_changed = component.supplier_id != form_data['supplier_id']
            
            # Update basic fields
            component.product_number = form_data['product_number']
            component.description = form_data['description']
            component.supplier_id = form_data['supplier_id']
            component.component_type_id = form_data['component_type_id']
            
            # Handle all associations and uploads
            _handle_component_properties(component, form_data['component_type_id'])
            _handle_categories(component, is_edit=True)
            _handle_brand_associations(component, is_edit=True)
            _handle_keywords(component, is_edit=True)
            _handle_picture_deletions(component)  # Handle picture deletions
            _handle_picture_uploads(component, is_edit=True)
            pending_pictures = _handle_variants(component, is_edit=True)
            
            # Commit to trigger database functions (SKU generation, picture naming)
            db.session.commit()
            
            # Handle picture file renames if key data changed
            if product_changed or supplier_changed:
                _handle_picture_renames(component, old_data)
            
            # Store component ID before session operations
            component_id = component.id
            
            # Save new pictures with proper names (commits internally)
            _save_pending_pictures(pending_pictures)
            
            # Clear session cache to ensure fresh data load on redirect
            db.session.expunge_all()
            
            # For edits, if new pictures were added, verify accessibility
            if pending_pictures:
                current_app.logger.info(f"Component {component_id} edit completed with new pictures, verifying accessibility")
                images_verified = _verify_images_accessible(component_id)
                
                if images_verified:
                    flash('Component updated successfully!', 'success')
                else:
                    flash('Component updated successfully! New images may take a moment to load.', 'warning')
            else:
                flash('Component updated successfully!', 'success')
            
            return redirect(url_for('component_web.component_detail', id=component_id))
        
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


@component_web.route('/api/component/validate-product-number', methods=['POST'])
def validate_product_number():
    """Validate product number uniqueness"""
    try:
        data = request.get_json()
        product_number = data.get('product_number', '').strip()
        supplier_id = data.get('supplier_id')
        component_id = data.get('component_id')
        
        if not product_number:
            return jsonify({'available': False, 'message': 'Product number is required'})
        
        if len(product_number) < 2:
            return jsonify({'available': False, 'message': 'Product number must be at least 2 characters'})
        
        # Build query to check for existing components
        query = Component.query.filter_by(product_number=product_number)
        
        # If supplier is selected, check uniqueness within that supplier
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
            supplier = Supplier.query.get(supplier_id)
            supplier_name = supplier.supplier_code if supplier else f"Supplier {supplier_id}"
        else:
            # If no supplier, check global uniqueness (supplier_id is NULL)
            query = query.filter(Component.supplier_id.is_(None))
            supplier_name = "components without supplier"
        
        # Exclude current component in edit mode
        if component_id:
            query = query.filter(Component.id != component_id)
        
        existing = query.first()
        
        if existing:
            if supplier_id:
                message = f'Product number "{product_number}" already exists for supplier "{supplier_name}"'
            else:
                message = f'Product number "{product_number}" already exists for {supplier_name}'
            
            return jsonify({'available': False, 'message': message})
        
        return jsonify({'available': True, 'message': 'Product number is available'})
        
    except Exception as e:
        current_app.logger.error(f"Product number validation error: {str(e)}")
        return jsonify({'available': False, 'message': 'Error validating product number'}), 500