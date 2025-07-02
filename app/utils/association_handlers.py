"""
Shared utility functions for handling component associations
Used by both web routes and API endpoints to avoid code duplication
"""
from flask import request, current_app
from app import db
from app.models import ComponentBrand, Category, Keyword


def handle_brand_associations(component, is_edit=False):
    """Handle component-brand associations"""
    if is_edit:
        # Remove existing associations for edit
        ComponentBrand.query.filter_by(component_id=component.id).delete()
    
    # Handle brand associations - check multiple possible field names
    brand_ids = []
    
    # Check all possible brand field names from frontend
    brand_field_names = ['brand_ids[]', 'brand_id', 'brands[]', 'brands', 'selected_brands[]']
    for field_name in brand_field_names:
        values = request.form.getlist(field_name)
        if values:
            current_app.logger.info(f"Found brand data in field '{field_name}': {values}")
            # Convert single value to list if needed
            if field_name == 'brand_id':
                single_value = request.form.get(field_name)
                if single_value:
                    values = [single_value]
            brand_ids.extend(values)
    
    current_app.logger.info(f"Final brand_ids to process: {brand_ids}")
    
    for brand_id in brand_ids:
        if brand_id.isdigit():
            current_app.logger.info(f"Creating brand association: component_id={component.id}, brand_id={brand_id}")
            brand_assoc = ComponentBrand(
                component_id=component.id,
                brand_id=int(brand_id)
            )
            db.session.add(brand_assoc)


def handle_categories(component, is_edit=False):
    """Handle component-category associations"""
    # Handle categories - check multiple possible field names  
    category_ids = []
    
    # Check all possible category field names from frontend
    category_field_names = ['category_ids[]', 'category_ids', 'category_id', 'categories[]', 'categories', 'selected_categories[]']
    for field_name in category_field_names:
        values = request.form.getlist(field_name)
        if values:
            current_app.logger.info(f"Found category data in field '{field_name}': {values}")
            category_ids.extend(values)
    
    current_app.logger.info(f"Final category_ids to process: {category_ids}")
    
    if is_edit:
        component.categories.clear()
    
    for category_id in category_ids:
        if category_id and str(category_id).isdigit():
            current_app.logger.info(f"Processing category_id: {category_id}")
            category = Category.query.get(int(category_id))
            if category and category not in component.categories:
                current_app.logger.info(f"Adding category to component: {category.name}")
                component.categories.append(category)
            elif category:
                current_app.logger.info(f"Category {category.name} already associated with component")
            else:
                current_app.logger.warning(f"Category with id {category_id} not found")


def handle_keywords(component, is_edit=False):
    """Handle component keywords"""
    keywords_input = request.form.get('keywords', '').strip()
    current_app.logger.info(f"Received keywords: '{keywords_input}'")
    
    if is_edit:
        component.keywords.clear()
    
    if keywords_input:
        keyword_names = [k.strip() for k in keywords_input.split(',') if k.strip()]
        current_app.logger.info(f"Parsed keyword names: {keyword_names}")
        
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


def handle_component_properties(component, component_type_id):
    """Handle dynamic component properties"""
    if component_type_id:
        from app.models import ComponentTypeProperty
        type_properties = ComponentTypeProperty.query.filter_by(
            component_type_id=component_type_id
        ).all()
        
        properties = {}
        for prop in type_properties:
            value = request.form.get(f'property_{prop.property_name}')
            if value:
                properties[prop.property_name] = value
        
        component.properties = properties


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