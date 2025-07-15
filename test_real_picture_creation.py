#!/usr/bin/env python3
"""
Test script to create real components with real JPEG pictures in the system
This demonstrates full integration with database and WebDAV
"""

import sys
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Component, ComponentVariant, Picture, Color, Supplier, ComponentType
from app.services.component_service import ComponentService
from app.services.webdav_storage_service import WebDAVStorageService, WebDAVStorageConfig


def create_test_jpeg(text, color='lightblue', size=(600, 400)):
    """Create a test JPEG image with text"""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw title
    draw.text((20, 20), text, fill='black', font=font)
    draw.text((20, 60), f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}", fill='black', font=font)
    draw.text((20, 100), "INTEGRATION TEST", fill='red', font=font)
    
    # Add border
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline='navy', width=3)
    
    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    return img_bytes.getvalue()


def main():
    print("🚀 Creating Real Components with Real Pictures")
    print("=" * 60)
    
    # Create app context
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # Initialize services
        component_service = ComponentService()
        webdav_config = WebDAVStorageConfig(
            base_url='http://31.182.67.115/webdav/components',
            timeout=30,
            verify_ssl=False,
            max_retries=3
        )
        webdav_service = WebDAVStorageService(webdav_config)
        
        # Create test data
        timestamp = int(time.time())
        
        # Ensure we have a supplier
        supplier = Supplier.query.filter_by(supplier_code='REALTEST').first()
        if not supplier:
            supplier = Supplier(supplier_code='REALTEST', address='Test Integration Address')
            db.session.add(supplier)
            db.session.flush()
        
        # Ensure we have a component type
        comp_type = ComponentType.query.filter_by(name='Shirt').first()
        if not comp_type:
            comp_type = ComponentType(name='Shirt')
            db.session.add(comp_type)
            db.session.flush()
        
        # Ensure we have colors
        red_color = Color.query.filter_by(name='Red').first()
        if not red_color:
            red_color = Color(name='Red')
            db.session.add(red_color)
        
        blue_color = Color.query.filter_by(name='Blue').first()
        if not blue_color:
            blue_color = Color(name='Blue')
            db.session.add(blue_color)
        
        db.session.flush()
        
        print(f"✅ Test data ready: Supplier={supplier.supplier_code}, Type={comp_type.name}")
        
        # Create component with variants and pictures
        print("\n📦 Creating component with variants and real pictures...")
        
        component_data = {
            'product_number': f'REALTEST-{timestamp}',
            'description': 'Real integration test component with actual JPEG pictures',
            'supplier_id': supplier.id,
            'component_type_id': comp_type.id,
            'properties': {
                'test_type': 'full_integration',
                'has_real_pictures': True,
                'timestamp': timestamp
            },
            'variants': [
                {
                    'color_id': red_color.id,
                    'description': 'Red variant with real picture'
                },
                {
                    'color_id': blue_color.id,
                    'description': 'Blue variant with real picture'
                }
            ]
        }
        
        # Create component
        result = component_service.create_component(component_data)
        
        if result['success']:
            component_id = result['component']['id']
            print(f"✅ Component created: ID={component_id}, Product={result['component']['product_number']}")
            
            # Upload pictures for component and variants
            component = Component.query.get(component_id)
            
            # 1. Upload main component picture
            print("\n📸 Uploading main component picture...")
            main_pic_data = create_test_jpeg(
                f"Main Component Picture - {component.product_number}",
                color='lightgray'
            )
            
            # Import picture name generator
            from app.utils.file_handling import generate_picture_name
            
            # Generate picture name before creating record
            main_pic_name = generate_picture_name(component, None, 1)
            
            main_pic = Picture(
                component_id=component.id,
                variant_id=None,
                picture_name=main_pic_name,  # Set the generated name
                url='/temp',
                picture_order=1
            )
            db.session.add(main_pic)
            db.session.flush()
            
            # Upload to WebDAV
            main_filename = f"{main_pic.picture_name}.jpg"
            upload_result = webdav_service.upload_file(
                BytesIO(main_pic_data),
                main_filename,
                'image/jpeg'
            )
            
            if upload_result.success:
                main_pic.url = upload_result.file_info.url
                db.session.flush()
                print(f"✅ Main picture uploaded: {main_filename}")
            
            # 2. Upload variant pictures
            for variant in component.variants:
                color_name = variant.color.name
                print(f"\n📸 Uploading {color_name} variant pictures...")
                
                # Create 2 pictures per variant
                for i in range(1, 3):
                    pic_data = create_test_jpeg(
                        f"{color_name} Variant - Picture {i} - {component.product_number}",
                        color='lightcoral' if color_name == 'Red' else 'lightsteelblue'
                    )
                    
                    # Generate picture name for variant
                    variant_pic_name = generate_picture_name(component, variant, i)
                    
                    variant_pic = Picture(
                        component_id=component.id,
                        variant_id=variant.id,
                        picture_name=variant_pic_name,  # Set the generated name
                        url='/temp',
                        picture_order=i
                    )
                    db.session.add(variant_pic)
                    db.session.flush()
                    
                    # Upload to WebDAV
                    variant_filename = f"{variant_pic.picture_name}.jpg"
                    upload_result = webdav_service.upload_file(
                        BytesIO(pic_data),
                        variant_filename,
                        'image/jpeg'
                    )
                    
                    if upload_result.success:
                        variant_pic.url = upload_result.file_info.url
                        db.session.flush()
                        print(f"  ✅ {color_name} picture {i} uploaded: {variant_filename}")
            
            db.session.commit()
            
            # Summary
            print("\n📊 Summary:")
            print(f"  Component ID: {component.id}")
            print(f"  Product Number: {component.product_number}")
            print(f"  Supplier: {component.supplier.supplier_code}")
            print(f"  Variants: {len(component.variants)}")
            print(f"  Total Pictures: {len(component.pictures)}")
            print("\n🎯 Pictures created:")
            for pic in component.pictures:
                print(f"  - {pic.picture_name}.jpg (Variant: {pic.variant.color.name if pic.variant else 'Main'})")
            
            print("\n✨ Success! Real component with real JPEG pictures created!")
            print(f"🌐 Check WebDAV at: http://31.182.67.115/webdav/components/")
            
        else:
            print(f"❌ Failed to create component: {result.get('error', 'Unknown error')}")


if __name__ == '__main__':
    main()