from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from app import db
from app.models import Component, ComponentType, Supplier, Category, Color, Brand, Picture
from app.utils_legacy import process_csv_file
import os
import io
import csv
from datetime import datetime

utility_web = Blueprint('utility_web', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@utility_web.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Handle CSV file upload and processing
    """
    if request.method == 'POST':
        try:
            # Check if file is present
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            
            # Check if file is selected
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Check file extension
            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
                return redirect(request.url)
            
            # Process the file
            try:
                results = process_csv_file(file)
                
                if results['success']:
                    flash(f"Successfully imported {results['imported']} components. "
                          f"Skipped {results['skipped']} duplicates. "
                          f"Failed {results['failed']} components.", 'success')
                    
                    if results['errors']:
                        for error in results['errors'][:10]:  # Show first 10 errors
                            flash(error, 'warning')
                        if len(results['errors']) > 10:
                            flash(f"... and {len(results['errors']) - 10} more errors", 'warning')
                else:
                    flash('Failed to process file. Please check the format.', 'error')
                    
            except Exception as e:
                current_app.logger.error(f"CSV processing error: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
            
            return redirect(url_for('component_web.index'))
            
        except RequestEntityTooLarge:
            flash(f'File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB.', 'error')
            return redirect(request.url)
        except Exception as e:
            current_app.logger.error(f"Upload error: {str(e)}")
            flash(f'Upload error: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('upload.html')


@utility_web.route('/download/csv-template')
def download_csv_template():
    """
    Download a CSV template for bulk component upload
    """
    try:
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Define template headers
        headers = [
            'product_number',
            'description',
            'supplier_code',
            'category_name',
            'component_type',
            'brand_names',  # Comma-separated list
            'keywords',     # Comma-separated list
            'proto_status',
            'sms_status',
            'pps_status'
        ]
        
        # Add sample data
        sample_data = [
            headers,  # Header row
            ['PROD001', 'Sample Product Description', 'SUP001', 'Electronics', 'Device', 'Brand1,Brand2', 'keyword1,keyword2', 'pending', 'pending', 'pending'],
            ['PROD002', 'Another Product', 'SUP002', 'Accessories', 'Cable', 'Brand3', 'cable,accessory', 'ok', 'ok', 'pending'],
            ['', '', '', '', '', '', '', '', '', ''],  # Empty row for user to fill
        ]
        
        # Write data
        for row in sample_data:
            writer.writerow(row)
        
        # Add instructions as comments
        instructions = [
            '',
            '# INSTRUCTIONS:',
            '# 1. product_number: Required - Unique product identifier',
            '# 2. description: Optional - Product description',
            '# 3. supplier_code: Optional - Must match existing supplier code in system',
            '# 4. category_name: Optional - Must match existing category in system',
            '# 5. component_type: Required - Must match existing component type in system',
            '# 6. brand_names: Optional - Comma-separated list of brand names',
            '# 7. keywords: Optional - Comma-separated list of keywords',
            '# 8. proto_status: Optional - Values: pending, ok, not_ok (default: pending)',
            '# 9. sms_status: Optional - Values: pending, ok, not_ok (default: pending)',
            '# 10. pps_status: Optional - Values: pending, ok, not_ok (default: pending)',
            '',
            '# NOTES:',
            '# - Remove these instruction lines before uploading',
            '# - Ensure supplier codes and category names match existing records',
            '# - Leave fields blank if not applicable',
            '# - Maximum file size: 16MB'
        ]
        
        for instruction in instructions:
            writer.writerow([instruction])
        
        # Create response
        output.seek(0)
        response = current_app.response_class(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=component_upload_template_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Template download error: {str(e)}")
        flash('Error generating template file.', 'error')
        return redirect(url_for('component_web.index'))