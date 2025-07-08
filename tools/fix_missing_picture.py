#!/usr/bin/env python3
"""
Fix missing picture file issue for component 208
This script will either restore the missing file or clean up the database record
"""

import requests
import sys
import os
sys.path.append('/mnt/c/Users/Administrator/DataspellProjects/webapp_components')

from app import create_app
from app.models import Picture, db

def check_webdav_file_exists(url):
    """Check if a file exists on WebDAV"""
    try:
        response = requests.head(url)
        return response.status_code == 200
    except:
        return False

def fix_missing_pictures():
    """Fix picture records that don't have corresponding files"""
    app = create_app()
    
    with app.app_context():
        # Find all pictures for component 208
        pictures = db.session.query(Picture).join(Picture.component_variant).filter(
            Picture.component_variant.has(component_id=208)
        ).all()
        
        print(f"Found {len(pictures)} pictures for component 208")
        
        for picture in pictures:
            print(f"\nChecking picture {picture.id}: {picture.picture_name}")
            print(f"URL: {picture.url}")
            
            # Check if file exists on WebDAV
            if check_webdav_file_exists(picture.url):
                print(f"✅ File exists: {picture.picture_name}")
            else:
                print(f"❌ File missing: {picture.picture_name}")
                
                # Option 1: Delete the database record
                print(f"Removing database record for missing file: {picture.picture_name}")
                db.session.delete(picture)
                
        # Commit changes
        try:
            db.session.commit()
            print("\n✅ Database cleanup completed successfully")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during cleanup: {e}")

if __name__ == "__main__":
    fix_missing_pictures()