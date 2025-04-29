import csv
import os
from app import db
from app.models import Supplier, Category, Color, Material, Component, Picture
from werkzeug.utils import secure_filename

def get_or_create(model, **kwargs):
    """Get an instance of a model, or create it if it doesn't exist."""
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

def process_csv_file(file_path):
    """Process the uploaded CSV file."""
    results = {
        'created': 0,
        'updated': 0,
        'errors': []
    }

    try:
        # Read CSV with semicolon delimiter
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            headers = reader.fieldnames
            
            # Check for required columns
            required_columns = ['product_number', 'description', 'supplier_code', 
                               'category_name', 'color_name', 'material_name']
            
            missing_columns = [col for col in required_columns if col not in headers]
            if missing_columns:
                results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
                return results

            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
                try:
                    process_component_row(row, results)
                except Exception as e:
                    results['errors'].append(f"Error in row {row_num}: {str(e)}")
        
        return results
    
    except Exception as e:
        results['errors'].append(f"Error processing CSV file: {str(e)}")
        return results

def process_component_row(row, results):
    """Process a single row from the CSV."""
    try:
        # Get or create related entities
        supplier = get_or_create(Supplier, supplier_code=row['supplier_code'])
        category = get_or_create(Category, name=row['category_name'])
        color = get_or_create(Color, name=row['color_name'])
        material = get_or_create(Material, name=row['material_name'])
        
        # Find or create component
        component = Component.query.filter_by(product_number=row['product_number']).first()
        
        if component:
            # Update existing component
            component.description = row['description']
            component.supplier_id = supplier.id
            component.category_id = category.id
            component.color_id = color.id
            component.material_id = material.id
            results['updated'] += 1
        else:
            # Create new component
            component = Component(
                product_number=row['product_number'],
                description=row['description'],
                supplier_id=supplier.id,
                category_id=category.id,
                color_id=color.id,
                material_id=material.id
            )
            db.session.add(component)
            results['created'] += 1
        
        # Commit to get the component ID if it's a new component
        db.session.commit()
        
        # Process pictures (up to 5)
        process_pictures(row, component)
        
        # Final commit for all changes
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def process_pictures(row, component):
    """Process picture data from a CSV row."""
    try:
        # Remove existing pictures (for update case)
        Picture.query.filter_by(component_id=component.id).delete()
        
        # Process up to 5 pictures
        for i in range(1, 6):
            pic_name_key = f'picture_{i}_name'
            pic_url_key = f'picture_{i}_url'
            pic_order_key = f'picture_{i}_order'
            
            # Check if we have this picture data
            if (pic_name_key in row and row[pic_name_key] and 
                pic_url_key in row and row[pic_url_key] and
                pic_order_key in row and row[pic_order_key]):
                
                picture = Picture(
                    component_id=component.id,
                    picture_name=row[pic_name_key],
                    url=row[pic_url_key],
                    picture_order=int(row[pic_order_key])
                )
                db.session.add(picture)
    except Exception as e:
        db.session.rollback()
        raise e
