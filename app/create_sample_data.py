#!/usr/bin/env python3
"""
Sample Data Creation Script for Component Variants Testing
This script truncates all tables and creates comprehensive sample data
with component variants and internet image URLs for testing.
"""

from app import create_app, db
from app.models import (
    Component, ComponentVariant, ComponentType, Supplier, Category, 
    Color, Material, Brand, Subbrand, ComponentBrand, Keyword, Picture
)
from datetime import datetime, timedelta
import random

def truncate_all_tables():
    """Truncate all tables in the component_app schema with CASCADE"""
    print("🗑️  Truncating all tables...")
    
    try:
        # Use a single TRUNCATE statement with CASCADE for all tables
        # This should handle foreign key dependencies automatically
        print("   🔹 Truncating all tables with CASCADE...")
        
        db.session.execute("""
            TRUNCATE TABLE 
                component_app.picture,
                component_app.component_variant,
                component_app.keyword_component,
                component_app.component_brand,
                component_app.component,
                component_app.subbrand,
                component_app.brand,
                component_app.keyword,
                component_app.color,
                component_app.material,
                component_app.category,
                component_app.component_type,
                component_app.supplier,
                component_app.type_category,
                component_app.style,
                component_app.gender
            CASCADE;
        """)
        
        db.session.commit()
        print("✅ All tables truncated successfully!")
        
    except Exception as e:
        print(f"❌ Error truncating tables: {e}")
        db.session.rollback()
        raise

def create_basic_data():
    """Create basic reference data"""
    print("📊 Creating basic reference data...")
    
    # Suppliers
    suppliers_data = [
        "ACME Corp", "TechParts Ltd", "GlobalSupply Inc", "FastComponents", 
        "ProParts Co", "EliteSuppliers", "MegaParts International", "PrimeTech"
    ]
    
    suppliers = []
    for i, name in enumerate(suppliers_data, 1):
        supplier = Supplier(
            supplier_code=f"SUP{i:03d}",
            address=f"{random.randint(100, 9999)} {random.choice(['Main St', 'Tech Ave', 'Industry Blvd', 'Commerce Dr'])}, Tech City"
        )
        suppliers.append(supplier)
        db.session.add(supplier)
    
    # Component Types
    component_types_data = [
        "Smartphone", "Laptop", "Tablet", "Smartwatch", "Headphones", 
        "Speaker", "Camera", "Gaming Console", "Keyboard", "Mouse",
        "Monitor", "Charger", "Case", "Screen Protector", "Cable"
    ]
    
    component_types = []
    for name in component_types_data:
        ct = ComponentType(name=name)
        component_types.append(ct)
        db.session.add(ct)
    
    # Categories
    categories_data = [
        "Electronics", "Accessories", "Gaming", "Audio", "Mobile", 
        "Computing", "Photography", "Wearables", "Storage", "Networking",
        "Smart Home", "Automotive", "Sports Tech", "Office Equipment"
    ]
    
    categories = []
    for name in categories_data:
        category = Category(name=name)
        categories.append(category)
        db.session.add(category)
    
    # Colors (important for variants)
    colors_data = [
        "Black", "White", "Silver", "Gold", "Rose Gold", "Space Gray",
        "Blue", "Red", "Green", "Purple", "Pink", "Orange", "Yellow",
        "Midnight Blue", "Pacific Blue", "Forest Green", "Product Red",
        "Coral", "Mint Green", "Lavender", "Sunset Orange", "Electric Blue",
        "Crimson", "Sage Green", "Burgundy", "Teal", "Magenta", "Titanium",
        "Ceramic White", "Matte Black", "Glossy White", "Deep Purple"
    ]
    
    colors = []
    for name in colors_data:
        color = Color(name=name)
        colors.append(color)
        db.session.add(color)
    
    # Materials
    materials_data = [
        "Aluminum", "Plastic", "Glass", "Carbon Fiber", "Stainless Steel",
        "Titanium", "Ceramic", "Leather", "Fabric", "Silicone", "Wood"
    ]
    
    materials = []
    for name in materials_data:
        material = Material(name=name)
        materials.append(material)
        db.session.add(material)
    
    # Brands
    brands_data = [
        "Apple", "Samsung", "Google", "Sony", "Microsoft", "LG", "Dell",
        "HP", "Lenovo", "ASUS", "Acer", "Huawei", "OnePlus", "Xiaomi",
        "Oppo", "Vivo", "Nothing", "Realme", "Motorola", "Nokia"
    ]
    
    brands = []
    for name in brands_data:
        brand = Brand(name=name)
        brands.append(brand)
        db.session.add(brand)
    
    # Keywords
    keywords_data = [
        "wireless", "bluetooth", "fast-charging", "waterproof", "5G", "AI",
        "gaming", "professional", "portable", "premium", "budget", "eco-friendly",
        "durable", "lightweight", "high-resolution", "noise-cancelling",
        "fingerprint", "face-recognition", "wireless-charging", "ultra-wide"
    ]
    
    keywords = []
    for name in keywords_data:
        keyword = Keyword(name=name)
        keywords.append(keyword)
        db.session.add(keyword)
    
    db.session.commit()
    print("✅ Basic reference data created!")
    
    return {
        'suppliers': suppliers,
        'component_types': component_types,
        'categories': categories,
        'colors': colors,
        'materials': materials,
        'brands': brands,
        'keywords': keywords
    }

def create_components_with_variants(data):
    """Create components with multiple variants and realistic data"""
    print("📱 Creating components with variants...")
    
    # Component definitions with variants
    component_definitions = [
        {
            'product_number': 'IPH15PRO',
            'description': 'iPhone 15 Pro - Latest flagship smartphone with titanium design and advanced camera system',
            'component_type': 'Smartphone',
            'category': 'Mobile',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['5G', 'AI', 'premium', 'wireless-charging', 'face-recognition'],
            'variants': [
                {
                    'color': 'Titanium',
                    'images': [
                        'https://images.unsplash.com/photo-1592286948276-c80eca29dd72?w=300',
                        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300'
                    ]
                },
                {
                    'color': 'Space Gray',
                    'images': [
                        'https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=300',
                        'https://images.unsplash.com/photo-1556656793-08538906a9f8?w=300'
                    ]
                },
                {
                    'color': 'Gold',
                    'images': [
                        'https://images.unsplash.com/photo-1580910051074-3eb694886505?w=300'
                    ]
                },
                {
                    'color': 'Silver',
                    'images': [
                        'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'SGS24ULTRA',
            'description': 'Samsung Galaxy S24 Ultra - Premium Android phone with S Pen and professional camera',
            'component_type': 'Smartphone',
            'category': 'Mobile',
            'supplier': 'SUP002',
            'brands': ['Samsung'],
            'keywords': ['5G', 'AI', 'gaming', 'premium', 'fast-charging'],
            'variants': [
                {
                    'color': 'Black',
                    'images': [
                        'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=300'
                    ]
                },
                {
                    'color': 'Purple',
                    'images': [
                        'https://images.unsplash.com/photo-1567581935884-3349723552ca?w=300'
                    ]
                },
                {
                    'color': 'Green',
                    'images': [
                        'https://images.unsplash.com/photo-1596727147705-61a532a659bd?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'AIRPODSPRO3',
            'description': 'AirPods Pro 3rd Generation - Advanced noise cancellation and spatial audio',
            'component_type': 'Headphones',
            'category': 'Audio',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['wireless', 'bluetooth', 'noise-cancelling', 'premium'],
            'variants': [
                {
                    'color': 'White',
                    'images': [
                        'https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=300',
                        'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'MBA15M3',
            'description': 'MacBook Air 15-inch with M3 chip - Ultra-thin laptop with incredible performance',
            'component_type': 'Laptop',
            'category': 'Computing',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['portable', 'premium', 'AI', 'lightweight'],
            'variants': [
                {
                    'color': 'Silver',
                    'images': [
                        'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=300'
                    ]
                },
                {
                    'color': 'Space Gray',
                    'images': [
                        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=300'
                    ]
                },
                {
                    'color': 'Midnight Blue',
                    'images': [
                        'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'IPADPRO13',
            'description': 'iPad Pro 13-inch - Professional tablet with M4 chip and Liquid Retina display',
            'component_type': 'Tablet',
            'category': 'Mobile',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['professional', 'high-resolution', 'portable', 'premium'],
            'variants': [
                {
                    'color': 'Silver',
                    'images': [
                        'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=300'
                    ]
                },
                {
                    'color': 'Space Gray',
                    'images': [
                        'https://images.unsplash.com/photo-1561154464-82e9adf32764?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'AWULTRA2',
            'description': 'Apple Watch Ultra 2 - Rugged smartwatch for extreme sports and adventures',
            'component_type': 'Smartwatch',
            'category': 'Wearables',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['waterproof', 'durable', 'fitness', 'premium'],
            'variants': [
                {
                    'color': 'Titanium',
                    'images': [
                        'https://images.unsplash.com/photo-1434493907317-a46b5bbe7834?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'SONYXM5',
            'description': 'Sony WH-1000XM5 - Industry-leading noise canceling wireless headphones',
            'component_type': 'Headphones',
            'category': 'Audio',
            'supplier': 'SUP004',
            'brands': ['Sony'],
            'keywords': ['wireless', 'bluetooth', 'noise-cancelling', 'premium'],
            'variants': [
                {
                    'color': 'Black',
                    'images': [
                        'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300'
                    ]
                },
                {
                    'color': 'Silver',
                    'images': [
                        'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'PIXEL8PRO',
            'description': 'Google Pixel 8 Pro - AI-powered photography and pure Android experience',
            'component_type': 'Smartphone',
            'category': 'Mobile',
            'supplier': 'SUP003',
            'brands': ['Google'],
            'keywords': ['5G', 'AI', 'photography', 'premium'],
            'variants': [
                {
                    'color': 'Obsidian',
                    'images': [
                        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300'
                    ]
                },
                {
                    'color': 'Porcelain',
                    'images': [
                        'https://images.unsplash.com/photo-1512054502232-10a0a035d6d0?w=300'
                    ]
                },
                {
                    'color': 'Bay',
                    'images': [
                        'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'IPHCASE15',
            'description': 'iPhone 15 Silicone Case - Premium protection with perfect fit',
            'component_type': 'Case',
            'category': 'Accessories',
            'supplier': 'SUP001',
            'brands': ['Apple'],
            'keywords': ['durable', 'lightweight', 'premium'],
            'variants': [
                {
                    'color': 'Black',
                    'images': [
                        'https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=300'
                    ]
                },
                {
                    'color': 'Pink',
                    'images': [
                        'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=300'
                    ]
                },
                {
                    'color': 'Blue',
                    'images': [
                        'https://images.unsplash.com/photo-1606394704977-68abaa0eb281?w=300'
                    ]
                },
                {
                    'color': 'Green',
                    'images': [
                        'https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=300'
                    ]
                },
                {
                    'color': 'Purple',
                    'images': [
                        'https://images.unsplash.com/photo-1588508065123-287b28e013da?w=300'
                    ]
                },
                {
                    'color': 'Orange',
                    'images': [
                        'https://images.unsplash.com/photo-1592179900427-8c3eea0f1fa6?w=300'
                    ]
                }
            ]
        },
        {
            'product_number': 'USBC60W',
            'description': 'USB-C 60W Fast Charger - Universal charging solution for laptops and phones',
            'component_type': 'Charger',
            'category': 'Accessories',
            'supplier': 'SUP005',
            'brands': ['Apple', 'Samsung'],
            'keywords': ['fast-charging', 'universal', 'portable'],
            'variants': [
                {
                    'color': 'White',
                    'images': [
                        'https://images.unsplash.com/photo-1609592806787-6117c0b4b3e7?w=300'
                    ]
                },
                {
                    'color': 'Black',
                    'images': [
                        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=300'
                    ]
                }
            ]
        }
    ]
    
    # Helper function to find objects by name
    def find_by_name(objects, name):
        return next((obj for obj in objects if obj.name == name), None)
    
    def find_supplier_by_code(suppliers, code):
        return next((sup for sup in suppliers if sup.supplier_code == code), None)
    
    components = []
    
    for comp_def in component_definitions:
        # Find related objects
        component_type = find_by_name(data['component_types'], comp_def['component_type'])
        category = find_by_name(data['categories'], comp_def['category'])
        supplier = find_supplier_by_code(data['suppliers'], comp_def['supplier'])
        
        if not all([component_type, category, supplier]):
            print(f"❌ Missing required data for {comp_def['product_number']}")
            continue
        
        # Create component
        component = Component(
            product_number=comp_def['product_number'],
            description=comp_def['description'],
            component_type_id=component_type.id,
            category_id=category.id,
            supplier_id=supplier.id,
            proto_status=random.choice(['pending', 'ok', 'not_ok']),
            sms_status=random.choice(['pending', 'ok', 'not_ok']),
            pps_status=random.choice(['pending', 'ok', 'not_ok']),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        
        # Set some properties
        component.properties = {
            'material': {
                'value': random.choice([m.name for m in data['materials']]),
                'type': 'text',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            },
            'weight': {
                'value': f"{random.randint(50, 2000)}g",
                'type': 'text',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        db.session.add(component)
        db.session.flush()  # Get the ID
        
        # Add brands
        for brand_name in comp_def['brands']:
            brand = find_by_name(data['brands'], brand_name)
            if brand:
                component_brand = ComponentBrand(
                    component_id=component.id,
                    brand_id=brand.id
                )
                db.session.add(component_brand)
        
        # Add keywords
        for keyword_name in comp_def['keywords']:
            keyword = find_by_name(data['keywords'], keyword_name)
            if keyword:
                component.keywords.append(keyword)
        
        # Create variants
        for variant_def in comp_def['variants']:
            color = find_by_name(data['colors'], variant_def['color'])
            if not color:
                print(f"❌ Color '{variant_def['color']}' not found for {comp_def['product_number']}")
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
        
        # Add main component pictures (non-variant specific)
        if comp_def['variants']:
            main_image = comp_def['variants'][0]['images'][0]  # Use first variant's first image as main
            main_picture = Picture(
                component_id=component.id,
                picture_name=f"{comp_def['product_number']}_main.jpg",
                url=main_image,
                picture_order=1,
                is_primary=True,
                alt_text=f"{comp_def['product_number']} main product image"
            )
            db.session.add(main_picture)
        
        components.append(component)
        print(f"   ✅ Created {comp_def['product_number']} with {len(comp_def['variants'])} variants")
    
    db.session.commit()
    print(f"✅ Created {len(components)} components with variants!")
    
    return components

def main():
    """Main function to create sample data"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting sample data creation...")
        print("=" * 50)
        
        # Step 1: Truncate all tables
        truncate_all_tables()
        print()
        
        # Step 2: Create basic reference data
        basic_data = create_basic_data()
        print()
        
        # Step 3: Create components with variants
        components = create_components_with_variants(basic_data)
        print()
        
        # Summary
        print("📊 SUMMARY:")
        print("=" * 50)
        print(f"✅ Suppliers: {len(basic_data['suppliers'])}")
        print(f"✅ Component Types: {len(basic_data['component_types'])}")
        print(f"✅ Categories: {len(basic_data['categories'])}")
        print(f"✅ Colors: {len(basic_data['colors'])}")
        print(f"✅ Materials: {len(basic_data['materials'])}")
        print(f"✅ Brands: {len(basic_data['brands'])}")
        print(f"✅ Keywords: {len(basic_data['keywords'])}")
        print(f"✅ Components: {len(components)}")
        
        # Count variants and pictures
        total_variants = db.session.query(ComponentVariant).count()
        total_pictures = db.session.query(Picture).count()
        
        print(f"✅ Component Variants: {total_variants}")
        print(f"✅ Pictures: {total_pictures}")
        print()
        print("🎉 Sample data creation completed successfully!")
        print("🌐 Application available at: http://localhost:6002")

if __name__ == "__main__":
    main()