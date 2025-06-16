#!/usr/bin/env python3
"""
CRE8 Library Excel File Analyzer
This script analyzes the CRE8_library.xlsx file and provides detailed insights.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def analyze_excel_file(file_path):
    """
    Analyze the CRE8_library.xlsx file and provide comprehensive insights.
    """
    print("=" * 60)
    print("CRE8 LIBRARY EXCEL FILE ANALYSIS")
    print("=" * 60)
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"❌ Error: File '{file_path}' not found!")
        return
    
    try:
        # Read the Excel file
        print(f"📖 Reading Excel file: {file_path}")
        
        # Get all sheet names first
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"\n📋 Found {len(sheet_names)} sheet(s): {sheet_names}")
        
        # Analyze each sheet
        for sheet_name in sheet_names:
            print(f"\n{'='*50}")
            print(f"SHEET: {sheet_name}")
            print(f"{'='*50}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Basic information
            print(f"\n📊 Basic Information:")
            print(f"   • Rows: {len(df)}")
            print(f"   • Columns: {len(df.columns)}")
            print(f"   • Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            
            # Column information
            print(f"\n📝 Column Information:")
            for i, col in enumerate(df.columns, 1):
                col_type = df[col].dtype
                non_null_count = df[col].count()
                null_count = df[col].isnull().sum()
                unique_count = df[col].nunique()
                
                print(f"   {i:2d}. {col}")
                print(f"       Type: {col_type}")
                print(f"       Non-null: {non_null_count}/{len(df)} ({non_null_count/len(df)*100:.1f}%)")
                print(f"       Null: {null_count} ({null_count/len(df)*100:.1f}%)")
                print(f"       Unique values: {unique_count}")
                
                # Show sample values for non-numeric columns
                if col_type == 'object' and unique_count <= 10:
                    unique_vals = df[col].dropna().unique()
                    print(f"       Sample values: {list(unique_vals)}")
                elif col_type in ['int64', 'float64']:
                    if not df[col].isnull().all():
                        print(f"       Min: {df[col].min()}, Max: {df[col].max()}, Mean: {df[col].mean():.2f}")
                print()
            
            # Data quality check
            print(f"🔍 Data Quality Analysis:")
            total_cells = len(df) * len(df.columns)
            null_cells = df.isnull().sum().sum()
            print(f"   • Total cells: {total_cells}")
            print(f"   • Null cells: {null_cells} ({null_cells/total_cells*100:.1f}%)")
            print(f"   • Data completeness: {(total_cells-null_cells)/total_cells*100:.1f}%")
            
            # Duplicate analysis
            duplicates = df.duplicated().sum()
            print(f"   • Duplicate rows: {duplicates} ({duplicates/len(df)*100:.1f}%)")
            
            # Show first few rows
            print(f"\n👀 First 5 rows:")
            print(df.head().to_string())
            
            # Show last few rows
            print(f"\n👀 Last 5 rows:")
            print(df.tail().to_string())
            
            # Statistical summary for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                print(f"\n📈 Statistical Summary (Numeric Columns):")
                print(df[numeric_cols].describe().to_string())
            
            # Value counts for categorical columns (if not too many unique values)
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if df[col].nunique() <= 20:  # Only show if reasonable number of categories
                    print(f"\n📊 Value Counts for '{col}':")
                    value_counts = df[col].value_counts()
                    print(value_counts.to_string())
        
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the analysis."""
    file_path = "CRE8_library.xlsx"
    analyze_excel_file(file_path)

if __name__ == "__main__":
    main() 