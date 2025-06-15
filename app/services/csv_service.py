"""CSV processing service."""

import csv
import os
from typing import Dict, List, Any
from flask import current_app
from app import db
from app.models import (
    Supplier, Category, Color, Material, Component, Picture, 
    ComponentType, Keyword
)
from app.utils.database import get_or_create, DatabaseTransaction


class CSVProcessingService:
    """Service for processing CSV files for component import/export."""
    
    @staticmethod
    def process_csv_file(file_path: str) -> Dict[str, Any]:
        """Process the uploaded CSV file for the flexible schema."""
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
                required_columns = [
                    'product_number', 'description', 'supplier_code', 
                    'component_type', 'category_name'
                ]
                
                missing_columns = [col for col in required_columns if col not in headers]
                if missing_columns:
                    results['errors'].append(
                        f"Missing required columns: {', '.join(missing_columns)}"
                    )
                    return results

                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header row
                    try:
                        CSVProcessingService._process_component_row(row, results)
                    except Exception as e:
                        current_app.logger.error(f"Error in row {row_num}: {str(e)}")
                        results['errors'].append(f"Error in row {row_num}: {str(e)}")
            
            return results
        
        except Exception as e:
            current_app.logger.error(f"Error processing CSV file: {str(e)}")
            results['errors'].append(f"Error processing CSV file: {str(e)}")
            return results

    @staticmethod
    def _process_component_row(row: Dict[str, str], results: Dict[str, Any]) -> None:
        """Process a single row from the CSV."""
        with DatabaseTransaction():
            # Get or create related entities
            supplier, _ = get_or_create(Supplier, supplier_code=row['supplier_code'])
            component_type, _ = get_or_create(ComponentType, name=row['component_type'])
            category, _ = get_or_create(Category, name=row['category_name'])
            
            # Find or create component
            component = Component.query.filter_by(
                product_number=row['product_number'],
                supplier_id=supplier.id
            ).first()
            
            if component:
                # Update existing component
                component.description = row['description']
                component.component_type_id = component_type.id
                component.category_id = category.id
                results['updated'] += 1
            else:
                # Create new component
                component = Component(
                    product_number=row['product_number'],
                    description=row['description'],
                    component_type_id=component_type.id,
                    supplier_id=supplier.id,
                    category_id=category.id
                )
                db.session.add(component)
                results['created'] += 1
            
            # Commit to get the component ID if it's a new component
            db.session.commit()
            
            # Process keywords
            if 'keywords' in row and row['keywords']:
                CSVProcessingService._process_keywords(row['keywords'], component)
            
            # Process flexible properties based on component type
            CSVProcessingService._process_flexible_properties(row, component, component_type.name)
            
            # Process pictures (up to 5)
            CSVProcessingService._process_pictures(row, component)

    @staticmethod
    def _process_keywords(keywords_str: str, component: Component) -> None:
        """Process keywords from CSV and associate with component."""
        if not keywords_str:
            return
        
        # Clear existing keywords
        component.keywords.clear()
        
        # Split keywords by comma and process
        keyword_names = [k.strip().lower() for k in keywords_str.split(',') if k.strip()]
        
        for keyword_name in keyword_names:
            # Get or create keyword
            keyword, _ = get_or_create(Keyword, name=keyword_name)
            
            # Add to component if not already there
            if keyword not in component.keywords:
                component.keywords.append(keyword)

    @staticmethod
    def _process_flexible_properties(row: Dict[str, str], component: Component, 
                                   component_type_name: str) -> None:
        """Process flexible properties based on component type."""
        
        # Define which properties each component type can have from CSV
        type_properties = {
            'Fabrics': ['material', 'color', 'gender', 'brand', 'finish', 'weight'],
            'Shapes': ['gender', 'style', 'brand', 'subbrand', 'subcategory'],
            'Buttons': ['material', 'color', 'brand', 'size'],
            'Zippers': ['material', 'color', 'brand', 'size'],
            'Labels': ['brand', 'subbrand', 'material'],
            'Hangtags': ['brand', 'subbrand', 'material'],
            'Packaging': ['brand', 'material']
        }
        
        # Clear existing properties
        component.properties = {}
        
        # Get allowed properties for this component type
        allowed_properties = type_properties.get(component_type_name, [])
        
        # Process each allowed property if it exists in the CSV row
        for prop in allowed_properties:
            if prop in row and row[prop]:
                value = row[prop].strip()
                if value:
                    # Handle array properties (multiple values separated by comma)
                    if prop in ['gender', 'style', 'subbrand']:
                        # Split by comma and clean up
                        values = [v.strip() for v in value.split(',') if v.strip()]
                        if values:
                            component.set_property(prop, values, 'array')
                    else:
                        # Single value property
                        component.set_property(prop, value, 'text')

    @staticmethod
    def _process_pictures(row: Dict[str, str], component: Component) -> None:
        """Process picture data from a CSV row - auto-assign picture order."""
        # Remove existing pictures (for update case)
        Picture.query.filter_by(component_id=component.id).delete()

        # Process up to 5 pictures with auto-assigned order
        picture_order = 1
        for i in range(1, 6):
            pic_name_key = f'picture_{i}_name'
            pic_url_key = f'picture_{i}_url'

            # Check if we have this picture data
            if (pic_name_key in row and row[pic_name_key] and
                pic_url_key in row and row[pic_url_key]):

                picture = Picture(
                    component_id=component.id,
                    picture_name=row[pic_name_key],
                    url=row[pic_url_key],
                    picture_order=picture_order  # Auto-assign order
                )
                db.session.add(picture)
                picture_order += 1  # Increment for next picture

    @staticmethod
    def export_components_to_csv(file_path: str, components: List[Component] = None) -> bool:
        """Export components to CSV file."""
        try:
            if components is None:
                components = Component.query.all()

            # Define CSV headers
            headers = [
                'product_number', 'description', 'supplier_code', 'component_type',
                'category_name', 'keywords', 'material', 'color', 'gender', 'style',
                'brand', 'subbrand', 'subcategory', 'finish', 'weight', 'size',
                'picture_1_name', 'picture_1_url',
                'picture_2_name', 'picture_2_url',
                'picture_3_name', 'picture_3_url',
                'picture_4_name', 'picture_4_url',
                'picture_5_name', 'picture_5_url'
            ]

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter=';')
                writer.writeheader()

                for component in components:
                    row = {
                        'product_number': component.product_number,
                        'description': component.description or '',
                        'supplier_code': component.supplier.supplier_code,
                        'component_type': component.component_type.name,
                        'category_name': component.category.name,
                        'keywords': ','.join([k.name for k in component.keywords])
                    }

                    # Add flexible properties
                    for prop in ['material', 'color', 'gender', 'style', 'brand', 'subbrand',
                               'subcategory', 'finish', 'weight', 'size']:
                        value = component.get_property(prop)
                        if value:
                            if isinstance(value, list):
                                row[prop] = ','.join(value)
                            else:
                                row[prop] = str(value)
                        else:
                            row[prop] = ''

                    # Add pictures
                    pictures = sorted(component.pictures, key=lambda p: p.picture_order)
                    for i, picture in enumerate(pictures[:5], 1):  # Max 5 pictures
                        row[f'picture_{i}_name'] = picture.picture_name
                        row[f'picture_{i}_url'] = picture.url

                    # Fill remaining picture fields with empty strings
                    for i in range(len(pictures) + 1, 6):
                        row[f'picture_{i}_name'] = ''
                        row[f'picture_{i}_url'] = ''

                    writer.writerow(row)

            return True

        except Exception as e:
            current_app.logger.error(f"Error exporting to CSV: {str(e)}")
            return False

    @staticmethod
    def create_sample_csv_data() -> List[Dict[str, str]]:
        """Create sample CSV data for testing."""
        sample_data = [
            {
                'product_number': 'F-WL001',
                'description': 'Shiny polyester 50D fabric',
                'supplier_code': 'SUPP001',
                'component_type': 'Fabrics',
                'category_name': 'polyester fabrics',
                'keywords': 'shiny,polyester,jacket,outerwear,waterproof',
                'material': 'polyester',
                'color': 'silver',
                'gender': 'ladies,unisex',
                'brand': 'MAR',
                'picture_1_name': 'fabric_front.jpg',
                'picture_1_url': 'http://example.com/images/fabric_front.jpg',
                'picture_2_name': 'fabric_detail.jpg',
                'picture_2_url': 'http://example.com/images/fabric_detail.jpg'
            },
            {
                'product_number': 'S-WL0001',
                'description': 'Parka with pockets and hood',
                'supplier_code': 'SUPP001',
                'component_type': 'Shapes',
                'category_name': 'jackets/coats',
                'keywords': 'arctic,winterjacket,parka,casual,cold weather',
                'gender': 'ladies',
                'style': 'casual,winter',
                'brand': 'MAR',
                'subbrand': 'MAR,MMC,UBL',
                'subcategory': 'ladies parka',
                'picture_1_name': 'parka_front.jpg',
                'picture_1_url': 'http://example.com/images/parka_front.jpg',
                'picture_2_name': 'parka_back.jpg',
                'picture_2_url': 'http://example.com/images/parka_back.jpg'
            },
            {
                'product_number': 'B-001',
                'description': 'Metal snap button',
                'supplier_code': 'SUPP002',
                'component_type': 'Buttons',
                'category_name': 'metal buttons',
                'keywords': 'snap,metal,closure,fastener',
                'material': 'metal',
                'color': 'silver',
                'brand': 'UBL',
                'size': '12mm',
                'picture_1_name': 'button_front.jpg',
                'picture_1_url': 'http://example.com/images/button_front.jpg'
            }
        ]

        return sample_data