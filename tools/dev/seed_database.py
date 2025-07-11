#!/usr/bin/env python3
"""
Database Seeding Tool for Development Environment
Seeds the database with sample data for testing and development
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app, db
from app.models import (
    Component, ComponentType, Supplier, Color, Brand, 
    Category, Material, ComponentVariant, Picture
)

def seed_reference_data():
    """Seed reference data tables"""
    print("🌱 Seeding reference data...")
    
    # Component Types
    types = [
        ComponentType(name='Shirt'),
        ComponentType(name='Pants'), 
        ComponentType(name='Hat'),
        ComponentType(name='Bag'),
        ComponentType(name='Accessory')
    ]
    for t in types:
        db.session.add(t)
    
    # Suppliers
    suppliers = [
        Supplier(supplier_code='NIKE'),
        Supplier(supplier_code='ADIDAS'),
        Supplier(supplier_code='PUMA'),
        Supplier(supplier_code='UNDER_ARMOUR')
    ]
    for s in suppliers:
        db.session.add(s)
    
    # Colors
    colors = [
        Color(name='Red'),
        Color(name='Blue'),
        Color(name='Green'),
        Color(name='Black'),
        Color(name='White'),
        Color(name='Yellow'),
        Color(name='Purple'),
        Color(name='Orange')
    ]
    for c in colors:
        db.session.add(c)
    
    # Brands
    brands = [
        Brand(name='Nike'),
        Brand(name='Adidas'),
        Brand(name='Puma'),
        Brand(name='Under Armour'),
        Brand(name='Generic')
    ]
    for b in brands:
        db.session.add(b)
    
    # Categories
    categories = [
        Category(name='Sportswear'),
        Category(name='Casual'),
        Category(name='Formal'),
        Category(name='Outdoor'),
        Category(name='Accessories')
    ]
    for c in categories:
        db.session.add(c)
    
    # Materials
    materials = [
        Material(name='Cotton'),
        Material(name='Polyester'),
        Material(name='Nylon'),
        Material(name='Leather'),
        Material(name='Canvas')
    ]
    for m in materials:
        db.session.add(m)
    
    db.session.commit()
    print("✅ Reference data seeded successfully")

def seed_sample_components():
    """Seed sample components with variants"""
    print("🌱 Seeding sample components...")
    
    # Get reference data
    shirt_type = ComponentType.query.filter_by(name='Shirt').first()
    nike_supplier = Supplier.query.filter_by(supplier_code='NIKE').first()
    sportswear_category = Category.query.filter_by(name='Sportswear').first()
    nike_brand = Brand.query.filter_by(name='Nike').first()
    
    red_color = Color.query.filter_by(name='Red').first()
    blue_color = Color.query.filter_by(name='Blue').first()
    
    # Sample components
    components = [
        {
            'product_number': 'SHIRT-001',
            'description': 'Premium Athletic Shirt',
            'component_type_id': shirt_type.id,
            'supplier_id': nike_supplier.id,
            'category_id': sportswear_category.id,
            'properties': {'material': 'polyester', 'size_range': 'S-XXL'},
            'variants': [red_color.id, blue_color.id]
        },
        {
            'product_number': 'SHIRT-002', 
            'description': 'Basic Training Shirt',
            'component_type_id': shirt_type.id,
            'supplier_id': nike_supplier.id,
            'category_id': sportswear_category.id,
            'properties': {'material': 'cotton', 'size_range': 'M-XL'},
            'variants': [red_color.id]
        }
    ]
    
    for comp_data in components:
        # Create component
        variants_data = comp_data.pop('variants')
        component = Component(**comp_data)
        db.session.add(component)
        db.session.flush()
        
        # Add brand association
        component.brands.append(nike_brand)
        
        # Create variants
        for color_id in variants_data:
            variant = ComponentVariant(
                component_id=component.id,
                color_id=color_id
            )
            db.session.add(variant)
    
    db.session.commit()
    print("✅ Sample components seeded successfully")

def main():
    """Main seeding function"""
    print("🚀 Component Management System - Database Seeder")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if data already exists
            if Component.query.count() > 0:
                print("⚠️  Database already contains components")
                response = input("Continue and add more data? (y/N): ")
                if response.lower() != 'y':
                    print("🛑 Seeding cancelled")
                    return
            
            seed_reference_data()
            seed_sample_components()
            
            print("\n✅ Database seeding completed successfully!")
            print(f"📊 Components created: {Component.query.count()}")
            print(f"📊 Variants created: {ComponentVariant.query.count()}")
            print(f"📊 Colors available: {Color.query.count()}")
            print(f"📊 Suppliers available: {Supplier.query.count()}")
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            db.session.rollback()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())