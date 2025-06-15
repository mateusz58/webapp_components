# Database Index Creation Script
# Run this to add missing indexes for better performance

from app import create_app, db
from sqlalchemy import text

def create_performance_indexes():
    """Create indexes to improve query performance"""
    
    indexes_to_create = [
        # Foreign key indexes
        "CREATE INDEX IF NOT EXISTS idx_component_supplier_id ON component_app.component(supplier_id);",
        "CREATE INDEX IF NOT EXISTS idx_component_category_id ON component_app.component(category_id);", 
        "CREATE INDEX IF NOT EXISTS idx_component_component_type_id ON component_app.component(component_type_id);",
        "CREATE INDEX IF NOT EXISTS idx_component_brand_component_id ON component_app.component_brand(component_id);",
        "CREATE INDEX IF NOT EXISTS idx_component_brand_brand_id ON component_app.component_brand(brand_id);",
        
        # Search indexes
        "CREATE INDEX IF NOT EXISTS idx_component_product_number ON component_app.component(product_number);",
        "CREATE INDEX IF NOT EXISTS idx_component_description_gin ON component_app.component USING gin(to_tsvector('english', description));",
        "CREATE INDEX IF NOT EXISTS idx_supplier_code ON component_app.supplier(supplier_code);",
        "CREATE INDEX IF NOT EXISTS idx_brand_name ON component_app.brand(name);",
        
        # Status indexes for filtering
        "CREATE INDEX IF NOT EXISTS idx_component_status ON component_app.component(proto_status, sms_status, pps_status);",
        "CREATE INDEX IF NOT EXISTS idx_component_created_at ON component_app.component(created_at DESC);",
        
        # Picture relationship indexes  
        "CREATE INDEX IF NOT EXISTS idx_picture_component_id ON component_app.picture(component_id);",
        "CREATE INDEX IF NOT EXISTS idx_picture_variant_id ON component_app.picture(variant_id);",
        "CREATE INDEX IF NOT EXISTS idx_picture_order ON component_app.picture(picture_order);",
        
        # Variant indexes
        "CREATE INDEX IF NOT EXISTS idx_variant_component_id ON component_app.component_variant(component_id);",
        "CREATE INDEX IF NOT EXISTS idx_variant_active ON component_app.component_variant(is_active);",
    ]
    
    app = create_app()
    with app.app_context():
        for index_sql in indexes_to_create:
            try:
                db.session.execute(text(index_sql))
                print(f"✓ Created: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"✗ Failed: {index_sql} - {e}")
        
        db.session.commit()
        print("Index creation completed!")

if __name__ == "__main__":
    create_performance_indexes()