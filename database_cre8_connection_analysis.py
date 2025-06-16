#!/usr/bin/env python3
"""
Database-CRE8 Library Connection Analysis
This script analyzes the connection between CRE8_library.xlsx and the database schema.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def analyze_database_connection():
    """
    Analyze the connection between CRE8_library.xlsx and the database schema.
    """
    print("=" * 80)
    print("DATABASE - CRE8 LIBRARY CONNECTION ANALYSIS")
    print("=" * 80)
    
    # Database schema mapping
    db_tables = {
        'keyword': 'Keywords for components',
        'component_type': 'Types of components (fabrics, shapes, etc.)',
        'gender': 'Gender categories',
        'style': 'Style categories', 
        'brand': 'Brand information',
        'subbrand': 'Sub-brand information',
        'supplier': 'Supplier information',
        'category': 'Product categories',
        'type_category': 'Relationship between component types and categories',
        'color': 'Color information',
        'material': 'Material information',
        'component': 'Main component table',
        'keyword_component': 'Many-to-many relationship between keywords and components',
        'component_variant': 'Component variants (by color)',
        'component_brand': 'Many-to-many relationship between components and brands',
        'picture': 'Images for components and variants'
    }
    
    print("\n📊 DATABASE SCHEMA OVERVIEW:")
    print("-" * 50)
    for table, description in db_tables.items():
        print(f"   • {table}: {description}")
    
    # Analyze CRE8 Excel file
    excel_file = "CRE8_library.xlsx"
    if not Path(excel_file).exists():
        print(f"\n❌ Error: File '{excel_file}' not found!")
        return
    
    try:
        # Read Excel sheets
        excel_data = pd.ExcelFile(excel_file)
        cre8_main = pd.read_excel(excel_file, sheet_name='CRE8 Library')
        fabric_lib = pd.read_excel(excel_file, sheet_name='fabric library')
        shape_lib = pd.read_excel(excel_file, sheet_name='shape library')
        
        print(f"\n🔗 MAPPING ANALYSIS:")
        print("=" * 50)
        
        # 1. Component Type Mapping
        print(f"\n1️⃣ COMPONENT TYPE MAPPING:")
        print("-" * 30)
        excel_components = [col for col in cre8_main.columns if col not in ['Library']]
        print(f"   Excel Components: {excel_components}")
        print(f"   → Maps to: component_type table")
        print(f"   → Suggested component_type entries:")
        for comp in excel_components:
            print(f"      - {comp}")
        
        # 2. Category Mapping
        print(f"\n2️⃣ CATEGORY MAPPING:")
        print("-" * 30)
        print(f"   Excel Categories: Category, Gender, Style")
        print(f"   → Maps to: category, gender, style tables")
        print(f"   → From fabric library: 'jackets' → category table")
        print(f"   → From shape library: 'jackets/coats' → category table")
        
        # 3. Brand Mapping
        print(f"\n3️⃣ BRAND MAPPING:")
        print("-" * 30)
        print(f"   Excel Brand References: 'brand', 'subbrand'")
        print(f"   → Maps to: brand, subbrand tables")
        print(f"   → From shape library: 'MAR, MMC, UBL' → brand/subbrand entries")
        
        # 4. Material Mapping
        print(f"\n4️⃣ MATERIAL MAPPING:")
        print("-" * 30)
        print(f"   Excel Material References: 'material'")
        print(f"   → Maps to: material table")
        print(f"   → From fabric library: 'shiny polyester 50D' → material entry")
        
        # 5. Keyword Mapping
        print(f"\n5️⃣ KEYWORD MAPPING:")
        print("-" * 30)
        print(f"   Excel Keyword References: 'keywords'")
        print(f"   → Maps to: keyword table")
        print(f"   → From shape library: 'arctic, winterjacket, parka, casual, cold weather'")
        print(f"   → These would be split into individual keyword entries")
        
        # 6. Component Data Mapping
        print(f"\n6️⃣ COMPONENT DATA MAPPING:")
        print("-" * 30)
        
        # Fabric component example
        if not fabric_lib.empty:
            fabric_data = fabric_lib.dropna()
            if not fabric_data.empty:
                print(f"   Fabric Component Example:")
                print(f"   → product_number: F-WL001")
                print(f"   → description: shiny polyester 50D")
                print(f"   → component_type: fabrics")
                print(f"   → category: jackets")
                print(f"   → gender: all")
        
        # Shape component example
        if not shape_lib.empty:
            shape_data = shape_lib.dropna()
            if not shape_data.empty:
                print(f"\n   Shape Component Example:")
                print(f"   → product_number: S-WL0001")
                print(f"   → description: parka with pockets and hood")
                print(f"   → component_type: shapes")
                print(f"   → category: jackets/coats")
                print(f"   → subcategory: ladies parka")
                print(f"   → gender: ladies")
                print(f"   → keywords: arctic, winterjacket, parka, casual, cold weather")
        
        # 7. Picture Mapping
        print(f"\n7️⃣ PICTURE MAPPING:")
        print("-" * 30)
        print(f"   Excel Picture References: 'picture 1', 'picture 2', etc.")
        print(f"   → Maps to: picture table")
        print(f"   → picture_order: 1, 2, 3, 4...")
        print(f"   → url: Would need to be populated with actual image URLs")
        
        # 8. Data Migration Strategy
        print(f"\n8️⃣ DATA MIGRATION STRATEGY:")
        print("-" * 30)
        print(f"   Step 1: Populate lookup tables")
        print(f"      - component_type: Add all Excel component types")
        print(f"      - category: Add categories from Excel")
        print(f"      - gender: Add gender values")
        print(f"      - style: Add style values")
        print(f"      - brand: Add brand entries")
        print(f"      - material: Add material entries")
        
        print(f"\n   Step 2: Create components")
        print(f"      - Use fabric codes (F-WL001) as product_number")
        print(f"      - Use shape codes (S-WL0001) as product_number")
        print(f"      - Map descriptions and properties")
        
        print(f"\n   Step 3: Create relationships")
        print(f"      - component_brand: Link components to brands")
        print(f"      - keyword_component: Link keywords to components")
        print(f"      - component_variant: Create color variants")
        print(f"      - picture: Add image references")
        
        # 9. Missing Data Analysis
        print(f"\n9️⃣ MISSING DATA ANALYSIS:")
        print("-" * 30)
        print(f"   Database requires but Excel lacks:")
        print(f"      - supplier_id: No supplier information in Excel")
        print(f"      - color_id: No color information in Excel")
        print(f"      - proto_status, sms_status, pps_status: No status tracking")
        print(f"      - properties (JSONB): Could store additional Excel data")
        
        # 10. Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        print("-" * 30)
        print(f"   1. Create data migration script to populate database from Excel")
        print(f"   2. Add missing fields to Excel template (supplier, color, status)")
        print(f"   3. Implement proper image URL management")
        print(f"   4. Add data validation to ensure Excel data quality")
        print(f"   5. Create component code generation system")
        print(f"   6. Implement status tracking workflow")
        
        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error analyzing connection: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the analysis."""
    analyze_database_connection()

if __name__ == "__main__":
    main() 