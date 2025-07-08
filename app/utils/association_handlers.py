"""
Shared utility functions for handling component associations
Used by both web routes and API endpoints to avoid code duplication
"""
from flask import request, current_app
from app import db
from app.models import ComponentBrand, Category, Keyword, Brand


def _get_data_source():
    """Determine if data comes from form or JSON and return the data source"""
    if request.is_json:
        return request.get_json(), 'json'
    else:
        return request.form, 'form'


def handle_brand_associations(component, is_edit=False, data_override=None):
    """Handle component-brand associations
    
    Args:
        component: Component object to associate brands with
        is_edit: Whether this is an edit operation (clears existing associations)
        data_override: Optional dict to override request data (for API calls)
    """
    if is_edit:
        # Remove existing associations for edit
        ComponentBrand.query.filter_by(component_id=component.id).delete()
    
    # Get data source
    if data_override:
        data_source = data_override
        source_type = 'override'
    else:
        data_source, source_type = _get_data_source()
    
    brand_ids = []
    
    if source_type == 'json' or source_type == 'override':
        # API/JSON data format
        brand_ids = data_source.get('brand_ids', []) or data_source.get('brand_ids[]', [])
        current_app.logger.info(f"Found brand data from JSON: {brand_ids}")
    else:
        # Form data format - check multiple possible field names
        brand_field_names = ['brand_ids[]', 'brand_id', 'brands[]', 'brands', 'selected_brands[]']
        for field_name in brand_field_names:
            values = data_source.getlist(field_name)
            if values:
                current_app.logger.info(f"Found brand data in field '{field_name}': {values}")
                # Convert single value to list if needed
                if field_name == 'brand_id':
                    single_value = data_source.get(field_name)
                    if single_value:
                        values = [single_value]
                brand_ids.extend(values)
    
    current_app.logger.info(f"Final brand_ids to process: {brand_ids}")
    
    # Handle new brand creation first
    new_brand_name = data_source.get('new_brand_name', '').strip()
    if new_brand_name:
        current_app.logger.info(f"Creating new brand: {new_brand_name}")
        
        # Check if brand already exists
        existing_brand = Brand.query.filter_by(name=new_brand_name).first()
        if existing_brand:
            current_app.logger.info(f"Brand '{new_brand_name}' already exists with ID {existing_brand.id}")
            brand_ids.append(str(existing_brand.id))
        else:
            # Create new brand
            new_brand = Brand(name=new_brand_name)
            db.session.add(new_brand)
            db.session.flush()  # Get the ID
            current_app.logger.info(f"Created new brand '{new_brand_name}' with ID {new_brand.id}")
            brand_ids.append(str(new_brand.id))
    
    # Handle existing brand IDs
    for brand_id in brand_ids:
        if str(brand_id).isdigit():
            brand_id_int = int(brand_id)
            
            # Check if brand exists before creating association
            brand = Brand.query.get(brand_id_int)
            if not brand:
                current_app.logger.warning(f"Brand with ID {brand_id_int} not found, skipping association")
                continue
            
            current_app.logger.info(f"Creating brand association: component_id={component.id}, brand_id={brand_id_int}")
            brand_assoc = ComponentBrand(
                component_id=component.id,
                brand_id=brand_id_int
            )
            db.session.add(brand_assoc)


def handle_categories(component, is_edit=False, data_override=None):
    """Handle component-category associations
    
    Args:
        component: Component object to associate categories with
        is_edit: Whether this is an edit operation (clears existing associations)
        data_override: Optional dict to override request data (for API calls)
    """
    # Get data source
    if data_override:
        data_source = data_override
        source_type = 'override'
    else:
        data_source, source_type = _get_data_source()
    
    category_ids = []
    
    if source_type == 'json' or source_type == 'override':
        # API/JSON data format
        category_ids = data_source.get('category_ids', []) or data_source.get('category_ids[]', [])
        current_app.logger.info(f"Found category data from JSON: {category_ids}")
    else:
        # Form data format - check multiple possible field names  
        category_field_names = ['category_ids[]', 'category_ids', 'category_id', 'categories[]', 'categories', 'selected_categories[]']
        for field_name in category_field_names:
            values = data_source.getlist(field_name)
            if values:
                current_app.logger.info(f"Found category data in field '{field_name}': {values}")
                category_ids.extend(values)
    
    current_app.logger.info(f"Final category_ids to process: {category_ids}")
    
    if is_edit:
        component.categories.clear()
    
    for category_id in category_ids:
        if category_id and str(category_id).isdigit():
            category_id_int = int(category_id)
            current_app.logger.info(f"Processing category_id: {category_id_int}")
            category = Category.query.get(category_id_int)
            if not category:
                current_app.logger.warning(f"Category with ID {category_id_int} not found, skipping")
                continue
            
            if category not in component.categories:
                current_app.logger.info(f"Adding category to component: {category.name}")
                component.categories.append(category)
            else:
                current_app.logger.info(f"Category {category.name} already associated with component")


def handle_keywords(component, is_edit=False, data_override=None):
    """Handle component keywords
    
    Args:
        component: Component object to associate keywords with
        is_edit: Whether this is an edit operation (clears existing associations)
        data_override: Optional dict to override request data (for API calls)
    """
    # Get data source
    if data_override:
        data_source = data_override
        source_type = 'override'
    else:
        data_source, source_type = _get_data_source()
    
    keyword_names = []
    
    if source_type == 'json' or source_type == 'override':
        # API/JSON data format - keywords come as array
        keywords_data = data_source.get('keywords', []) or data_source.get('keywords[]', [])
        if isinstance(keywords_data, list):
            keyword_names = [k.strip() for k in keywords_data if k.strip()]
        elif isinstance(keywords_data, str):
            keyword_names = [k.strip() for k in keywords_data.split(',') if k.strip()]
        current_app.logger.info(f"Found keywords from JSON: {keyword_names}")
    else:
        # Form data format - keywords come as comma-separated string
        keywords_input = data_source.get('keywords', '').strip()
        current_app.logger.info(f"Received keywords from form: '{keywords_input}'")
        if keywords_input:
            keyword_names = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    current_app.logger.info(f"Parsed keyword names: {keyword_names}")
    
    if is_edit:
        component.keywords.clear()
    
    for keyword_name in keyword_names:
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        if not keyword:
            current_app.logger.info(f"Creating new keyword: {keyword_name}")
            keyword = Keyword(name=keyword_name)
            db.session.add(keyword)
            db.session.flush()
        else:
            current_app.logger.info(f"Using existing keyword: {keyword_name}")
        
        if keyword not in component.keywords:
            current_app.logger.info(f"Adding keyword to component: {keyword_name}")
            component.keywords.append(keyword)
        else:
            current_app.logger.info(f"Keyword {keyword_name} already associated with component")


def handle_component_properties(component, component_type_id, data_override=None):
    """Handle dynamic component properties
    
    Args:
        component: Component object to set properties on
        component_type_id: ID of the component type to get property definitions
        data_override: Optional dict to override request data (for API calls)
    """
    if component_type_id:
        from app.models import ComponentTypeProperty
        type_properties = ComponentTypeProperty.query.filter_by(
            component_type_id=component_type_id
        ).all()
        
        # Get data source
        if data_override:
            data_source = data_override
            source_type = 'override'
        else:
            data_source, source_type = _get_data_source()
        
        properties = {}
        
        if source_type == 'json' or source_type == 'override':
            # API/JSON data format - properties come as nested object
            properties_data = data_source.get('properties', {})
            if isinstance(properties_data, dict):
                # Direct property mapping
                for prop in type_properties:
                    if prop.property_name in properties_data:
                        properties[prop.property_name] = properties_data[prop.property_name]
            current_app.logger.info(f"Found properties from JSON: {properties}")
        else:
            # Form data format - properties come as property_{name} fields
            for prop in type_properties:
                value = data_source.get(f'property_{prop.property_name}')
                if value:
                    properties[prop.property_name] = value
            current_app.logger.info(f"Found properties from form: {properties}")
        
        if properties:
            component.properties = properties
            current_app.logger.info(f"Set component properties: {component.properties}")


def get_association_counts(component):
    """Get counts of all associations for response/logging"""
    brands_count = len(component.brand_associations)
    categories_count = len(component.categories)  
    keywords_count = len(component.keywords)
    properties_count = len(component.properties) if component.properties else 0
    
    return {
        'brands_count': brands_count,
        'categories_count': categories_count,
        'keywords_count': keywords_count,
        'properties_count': properties_count
    }