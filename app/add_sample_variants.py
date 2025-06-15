#!/usr/bin/env python3
"""
Add Sample Component Variants with Internet Images
This script adds a few new components with multiple variants and internet image URLs
to demonstrate the variant color functionality.
"""

from app import create_app, db
from app.models import (
    Component, ComponentVariant, ComponentType, Supplier, Category, 
    Color, Brand, ComponentBrand, Keyword, Picture
)
from datetime import datetime, timedelta
import random

def add_sample_variants():
    """Add sample components with multiple variants and internet images"""
    print("📱 Adding sample components with variants...")
    
    # Get existing reference data
    suppliers = Supplier.query.all()
    component_types = ComponentType.query.all()
    categories = Category.query.all()
    colors = Color.query.all()
    brands = Brand.query.all()
    keywords = Keyword.query.all()
    
    if not all([suppliers, component_types, categories, colors]):
        print("❌ Missing required reference data")
        return
    
    # Sample shoe components with multiple variants and internet images
    # Using existing component types and categories from the shoe database
    sample_components = [
        {
            'product_number': 'DEMO-OUTSOLE-01',
            'description': 'Demo Premium Outsole - High-performance rubber outsole available in multiple colors',
            'component_type': 'Outsole',
            'category': 'Running Shoes',
            'brands': ['Asics'],
            'keywords': ['durable', 'premium'],
            'variants': [
                {
                    'color': 'Black',
                    'images': [
                        'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300&h=300&fit=crop',
                        'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Red',
                    'images': [
                        'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Navy',
                    'images': [
                        'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Green',
                    'images': [
                        'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Orange',
                    'images': [
                        'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=300&h=300&fit=crop'
                    ]
                }
            ]
        },
        {
            'product_number': 'DEMO-BUCKLE-01',
            'description': 'Demo Metal Buckle - Premium shoe buckle component in various finishes',
            'component_type': 'Buckle',
            'category': 'Derby Shoes',
            'brands': ['Converse Elite'],
            'keywords': ['premium'],
            'variants': [
                {
                    'color': 'Gold',
                    'images': [
                        'https://images.unsplash.com/photo-1570124477782-53c4ec18e4b9?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Copper',
                    'images': [
                        'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Silver',
                    'images': [
                        'https://images.unsplash.com/photo-1562183241-b937e95585b6?w=300&h=300&fit=crop'
                    ]
                }
            ]
        },
        {
            'product_number': 'DEMO-TONGUE-01',
            'description': 'Demo Shoe Tongue - Comfortable padded tongue in colorful designs',
            'component_type': 'Tongue',
            'category': 'Sneakers',
            'brands': ['Mizuno'],
            'keywords': ['comfortable'],
            'variants': [
                {
                    'color': 'Pink',
                    'images': [
                        'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Teal',
                    'images': [
                        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Royal Blue',
                    'images': [
                        'https://images.unsplash.com/photo-1524863479829-916d8e77f114?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Orange',
                    'images': [
                        'https://images.unsplash.com/photo-1552346154-21d32810aba3?w=300&h=300&fit=crop'
                    ]
                }
            ]
        },
        {
            'product_number': 'DEMO-CUSHIONING-01',
            'description': 'Demo Cushioning Insole - Advanced comfort cushioning in multiple densities and colors',
            'component_type': 'Cushioning',
            'category': 'Running Shoes',
            'brands': ['Asics'],
            'keywords': ['comfortable', 'premium'],
            'variants': [
                {
                    'color': 'Green',
                    'images': [
                        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Pink',
                    'images': [
                        'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Royal Blue',
                    'images': [
                        'https://images.unsplash.com/photo-1586525198428-225f6f12cbbe?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Holographic',
                    'images': [
                        'https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Gold',
                    'images': [
                        'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=300&h=300&fit=crop'
                    ]
                },
                {
                    'color': 'Red',
                    'images': [
                        'https://images.unsplash.com/photo-1611085583191-a3b181a88401?w=300&h=300&fit=crop'
                    ]
                }
            ]
        }
    ]
    
    # Helper functions
    def find_by_name(objects, name):
        return next((obj for obj in objects if hasattr(obj, 'name') and obj.name == name), None)
    
    added_components = []
    
    for comp_def in sample_components:
        # Check if component already exists
        existing = Component.query.filter_by(product_number=comp_def['product_number']).first()
        if existing:
            print(f"   ⚠️  Component {comp_def['product_number']} already exists, skipping...")
            continue
        
        # Find required objects
        component_type = find_by_name(component_types, comp_def['component_type'])
        category = find_by_name(categories, comp_def['category'])
        supplier = suppliers[0] if suppliers else None  # Use first available supplier
        
        if not all([component_type, category, supplier]):
            print(f"   ❌ Missing required data for {comp_def['product_number']}")
            continue
        
        # Create component
        component = Component(
            product_number=comp_def['product_number'],
            description=comp_def['description'],
            component_type_id=component_type.id,
            category_id=category.id,
            supplier_id=supplier.id,
            proto_status=random.choice(['pending', 'ok']),
            sms_status=random.choice(['pending', 'ok']),
            pps_status=random.choice(['pending', 'ok']),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        # Set properties
        component.properties = {
            'demo': {
                'value': 'true',
                'type': 'boolean',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        db.session.add(component)
        db.session.flush()  # Get the ID
        
        # Add brands
        for brand_name in comp_def['brands']:
            brand = find_by_name(brands, brand_name)
            if brand:
                component_brand = ComponentBrand(
                    component_id=component.id,
                    brand_id=brand.id
                )
                db.session.add(component_brand)
        
        # Add keywords
        for keyword_name in comp_def['keywords']:
            keyword = find_by_name(keywords, keyword_name)
            if keyword:
                component.keywords.append(keyword)
        
        # Create variants
        variant_count = 0
        for variant_def in comp_def['variants']:
            color = find_by_name(colors, variant_def['color'])
            if not color:
                print(f"   ⚠️  Color '{variant_def['color']}' not found, skipping variant...")
                continue
            
            variant = ComponentVariant(
                component_id=component.id,
                color_id=color.id,
                variant_name=f"{comp_def['product_number']}-{variant_def['color']}",
                description=f"{variant_def['color']} variant of {comp_def['product_number']}",
                is_active=True
            )
            db.session.add(variant)
            db.session.flush()  # Get the ID
            
            # Add variant pictures
            for i, image_url in enumerate(variant_def['images']):
                picture = Picture(
                    variant_id=variant.id,
                    picture_name=f"{comp_def['product_number']}_{variant_def['color']}_{i+1}.jpg",
                    url=image_url,
                    picture_order=i + 1,
                    is_primary=(i == 0),  # First image is primary
                    alt_text=f"{comp_def['product_number']} in {variant_def['color']} color"
                )
                db.session.add(picture)
            
            variant_count += 1
        
        # Add main component picture (use first variant's first image)
        if comp_def['variants'] and variant_count > 0:
            main_image = comp_def['variants'][0]['images'][0]
            main_picture = Picture(
                component_id=component.id,
                picture_name=f"{comp_def['product_number']}_main.jpg",
                url=main_image,
                picture_order=1,
                is_primary=True,
                alt_text=f"{comp_def['product_number']} main product image"
            )
            db.session.add(main_picture)
        
        added_components.append(component)
        print(f"   ✅ Added {comp_def['product_number']} with {variant_count} variants")
    
    db.session.commit()
    print(f"✅ Added {len(added_components)} new components with variants!")
    
    return added_components

def main():
    """Main function to add sample variants"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Adding sample component variants...")
        print("=" * 50)
        
        # Add sample components with variants
        components = add_sample_variants()
        print()
        
        # Summary
        print("📊 SUMMARY:")
        print("=" * 50)
        
        # Count total data after additions
        from app.models import Component, ComponentVariant, Picture
        total_components = Component.query.count()
        total_variants = ComponentVariant.query.count()
        total_pictures = Picture.query.count()
        
        print(f"✅ Total Components: {total_components}")
        print(f"✅ Total Component Variants: {total_variants}")
        print(f"✅ Total Pictures: {total_pictures}")
        print(f"✅ New Components Added: {len(components)}")
        print()
        print("🎉 Sample variant data added successfully!")
        print("🌐 Application available at: http://localhost:6002")
        print("🔍 Look for components starting with 'DEMO-' to see the new variants!")

if __name__ == "__main__":
    main()