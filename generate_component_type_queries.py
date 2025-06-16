#!/usr/bin/env python3
"""
Generate Component Type SQL Queries
This script reads CRE8_library.xlsx and generates SQL INSERT statements for component_type table.
"""

import pandas as pd
from pathlib import Path

def generate_component_type_queries():
    """
    Generate SQL INSERT statements for component_type table from CRE8_library.xlsx
    """
    print("=" * 60)
    print("GENERATING COMPONENT TYPE SQL QUERIES")
    print("=" * 60)
    
    excel_file = "CRE8_library.xlsx"
    if not Path(excel_file).exists():
        print(f"❌ Error: File '{excel_file}' not found!")
        return
    
    try:
        # Read the main sheet
        cre8_main = pd.read_excel(excel_file, sheet_name='CRE8 Library')
        
        # Extract component types (all columns except 'Library')
        component_types = [col for col in cre8_main.columns if col != 'Library']
        
        print(f"📋 Found {len(component_types)} component types in Excel file")
        print(f"Component types: {component_types}")
        
        # Generate SQL file
        sql_file = "insert_component_types_generated.sql"
        
        with open(sql_file, 'w') as f:
            f.write("-- Auto-generated SQL script for component_type table\n")
            f.write("-- Generated from CRE8_library.xlsx\n\n")
            
            f.write("-- Check existing component types\n")
            f.write("SELECT 'Existing component types:' as info;\n")
            f.write("SELECT id, name FROM component_type ORDER BY name;\n\n")
            
            f.write("-- Insert component types from CRE8_library.xlsx\n")
            f.write("-- Using ON CONFLICT to avoid duplicates\n\n")
            
            for component_type in component_types:
                f.write(f"INSERT INTO component_type (name) VALUES\n")
                f.write(f"    ('{component_type}')\n")
                f.write(f"ON CONFLICT (name) DO NOTHING;\n\n")
            
            f.write("-- Verify the insertions\n")
            f.write("SELECT 'Component types after insertion:' as info;\n")
            f.write("SELECT id, name FROM component_type ORDER BY name;\n\n")
            
            f.write("-- Count total component types\n")
            f.write("SELECT 'Total component types:' as info, COUNT(*) as count FROM component_type;\n")
        
        print(f"✅ Generated SQL file: {sql_file}")
        
        # Also generate a single INSERT statement for bulk insertion
        bulk_sql_file = "insert_component_types_bulk.sql"
        
        with open(bulk_sql_file, 'w') as f:
            f.write("-- Bulk INSERT statement for component_type table\n")
            f.write("-- Generated from CRE8_library.xlsx\n\n")
            
            f.write("-- Check existing component types\n")
            f.write("SELECT 'Existing component types:' as info;\n")
            f.write("SELECT id, name FROM component_type ORDER BY name;\n\n")
            
            f.write("-- Bulk insert component types\n")
            f.write("INSERT INTO component_type (name) VALUES\n")
            
            values = []
            for i, component_type in enumerate(component_types):
                if i == len(component_types) - 1:
                    values.append(f"    ('{component_type}')")
                else:
                    values.append(f"    ('{component_type}'),")
            
            f.write('\n'.join(values))
            f.write("\nON CONFLICT (name) DO NOTHING;\n\n")
            
            f.write("-- Verify the insertions\n")
            f.write("SELECT 'Component types after insertion:' as info;\n")
            f.write("SELECT id, name FROM component_type ORDER BY name;\n\n")
            
            f.write("-- Count total component types\n")
            f.write("SELECT 'Total component types:' as info, COUNT(*) as count FROM component_type;\n")
        
        print(f"✅ Generated bulk SQL file: {bulk_sql_file}")
        
        # Display the generated SQL
        print(f"\n📄 Generated SQL (first few statements):")
        print("-" * 40)
        with open(sql_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20]):  # Show first 20 lines
                print(line.rstrip())
            if len(lines) > 20:
                print("... (truncated)")
        
        print(f"\n{'='*60}")
        print("GENERATION COMPLETE")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error generating queries: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the generation."""
    generate_component_type_queries()

if __name__ == "__main__":
    main() 