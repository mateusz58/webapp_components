import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Supplier, Category, Color, Material, Component, Picture
from app.utils import process_csv_file
from sqlalchemy import or_, text
import uuid

main = Blueprint('main', __name__)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    """Home page with list of components."""
    try:
        # Get filter parameters
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        color_id = request.args.get('color_id', type=int)
        material_id = request.args.get('material_id', type=int)
        
        # Base query
        query = Component.query
        
        # Apply filters
        if search:
            query = query.filter(or_(
                Component.product_number.ilike(f'%{search}%'),
                Component.description.ilike(f'%{search}%')
            ))
        
        if category_id:
            query = query.filter(Component.category_id == category_id)
        
        if supplier_id:
            query = query.filter(Component.supplier_id == supplier_id)
        
        if color_id:
            query = query.filter(Component.color_id == color_id)
        
        if material_id:
            query = query.filter(Component.material_id == material_id)
        
        # Get paginated results
        page = request.args.get('page', 1, type=int)
        components = query.paginate(page=page, per_page=10, error_out=False)
        
        # Get filter options for dropdowns
        categories = Category.query.all()
        suppliers = Supplier.query.all()
        colors = Color.query.all()
        materials = Material.query.all()
        
        return render_template('index.html', 
                              components=components,
                              categories=categories,
                              suppliers=suppliers,
                              colors=colors,
                              materials=materials,
                              search=search)
    except Exception as e:
        # In case of database errors, show a simple connection page
        return render_template('connection_error.html', error=str(e))

@main.route('/test-connection')
def test_connection():
    """Test database connection"""
    try:
        # Test if we can connect to the database and query
        result = db.session.execute(text("SELECT 1 as test"))
        value = result.fetchone()[0]
        
        # Include schema-specific testing
        schema_info = {
            'success': True,
            'message': 'Successfully connected to the database',
            'value': value
        }
        
        # Try to check if the schema exists
        try:
            schema_check = db.session.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'component_app'"))
            if schema_check.fetchone():
                schema_info['schema_exists'] = True
                schema_info['schema_name'] = 'component_app'
            else:
                schema_info['schema_exists'] = False
        except Exception as e:
            schema_info['schema_check_error'] = str(e)
        
        return jsonify(schema_info)
    except Exception as e:
        error_info = {
            'success': False,
            'message': 'Database connection error',
            'error': str(e)
        }
        return jsonify(error_info), 500

@main.route('/component/<int:id>')
def component_detail(id):
    """Detail view for a component."""
    component = Component.query.get_or_404(id)
    return render_template('component_detail.html', component=component)

@main.route('/component/new', methods=['GET', 'POST'])
def new_component():
    """Create a new component."""
    if request.method == 'POST':
        # Get form data
        product_number = request.form.get('product_number')
        description = request.form.get('description')
        supplier_id = request.form.get('supplier_id')
        category_id = request.form.get('category_id')
        color_id = request.form.get('color_id')
        material_id = request.form.get('material_id')
        
        # Check if product_number already exists
        existing = Component.query.filter_by(product_number=product_number).first()
        if existing:
            flash('Product number already exists.', 'danger')
            # Get filter options for dropdowns
            categories = Category.query.all()
            suppliers = Supplier.query.all()
            colors = Color.query.all()
            materials = Material.query.all()
            return render_template('component_form.html', 
                                  categories=categories,
                                  suppliers=suppliers,
                                  colors=colors,
                                  materials=materials)
        
        # Create new component
        component = Component(
            product_number=product_number,
            description=description,
            supplier_id=supplier_id,
            category_id=category_id,
            color_id=color_id,
            material_id=material_id
        )
        
        db.session.add(component)
        db.session.commit()
        
        # Process picture uploads
        for i in range(1, 6):  # Up to 5 pictures
            picture_file = request.files.get(f'picture_{i}')
            picture_order = request.form.get(f'picture_{i}_order')
            
            if picture_file and picture_file.filename:
                # Generate unique filename
                filename = secure_filename(picture_file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Save file
                picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                picture_file.save(picture_path)
                
                # Create picture record
                picture = Picture(
                    component_id=component.id,
                    picture_name=filename,
                    url=f"/static/uploads/{unique_filename}",
                    picture_order=int(picture_order) if picture_order else i
                )
                db.session.add(picture)
        
        db.session.commit()
        flash('Component created successfully!', 'success')
        return redirect(url_for('main.component_detail', id=component.id))
    
    # GET request - show form
    categories = Category.query.all()
    suppliers = Supplier.query.all()
    colors = Color.query.all()
    materials = Material.query.all()
    
    return render_template('component_form.html', 
                          categories=categories,
                          suppliers=suppliers,
                          colors=colors,
                          materials=materials)

@main.route('/component/edit/<int:id>', methods=['GET', 'POST'])
def edit_component(id):
    """Edit an existing component."""
    component = Component.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get form data
        component.product_number = request.form.get('product_number')
        component.description = request.form.get('description')
        component.supplier_id = request.form.get('supplier_id')
        component.category_id = request.form.get('category_id')
        component.color_id = request.form.get('color_id')
        component.material_id = request.form.get('material_id')
        
        # Process pictures - first remove existing pictures
        Picture.query.filter_by(component_id=component.id).delete()
        
        # Then add new pictures
        for i in range(1, 6):  # Up to 5 pictures
            picture_file = request.files.get(f'picture_{i}')
            picture_order = request.form.get(f'picture_{i}_order')
            existing_url = request.form.get(f'existing_picture_{i}_url')
            existing_name = request.form.get(f'existing_picture_{i}_name')
            
            # Case 1: New file uploaded
            if picture_file and picture_file.filename:
                # Generate unique filename
                filename = secure_filename(picture_file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Save file
                picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                picture_file.save(picture_path)
                
                # Create picture record
                picture = Picture(
                    component_id=component.id,
                    picture_name=filename,
                    url=f"/static/uploads/{unique_filename}",
                    picture_order=int(picture_order) if picture_order else i
                )
                db.session.add(picture)
            
            # Case 2: Using existing picture
            elif existing_url and existing_name and picture_order:
                picture = Picture(
                    component_id=component.id,
                    picture_name=existing_name,
                    url=existing_url,
                    picture_order=int(picture_order)
                )
                db.session.add(picture)
        
        db.session.commit()
        flash('Component updated successfully!', 'success')
        return redirect(url_for('main.component_detail', id=component.id))
    
    # GET request - show form with existing data
    categories = Category.query.all()
    suppliers = Supplier.query.all()
    colors = Color.query.all()
    materials = Material.query.all()
    
    return render_template('component_edit_form.html', 
                          component=component,
                          categories=categories,
                          suppliers=suppliers,
                          colors=colors,
                          materials=materials)

@main.route('/component/delete/<int:id>', methods=['POST'])
def delete_component(id):
    """Delete a component."""
    component = Component.query.get_or_404(id)
    
    # Delete associated pictures first
    Picture.query.filter_by(component_id=component.id).delete()
    
    # Delete the component
    db.session.delete(component)
    db.session.commit()
    
    flash('Component deleted successfully!', 'success')
    return redirect(url_for('main.index'))

@main.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    """Upload and process a CSV file."""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Check if the file has an allowed extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            # Process the CSV file
            results = process_csv_file(temp_path)
            
            # Delete the temporary file
            os.remove(temp_path)
            
            # Show results
            if results['errors']:
                for error in results['errors']:
                    flash(error, 'danger')
            else:
                flash(f"CSV processed successfully! Created: {results['created']}, Updated: {results['updated']}", 'success')
            
            return redirect(url_for('main.index'))
        else:
            flash('File type not allowed. Please upload a CSV file.', 'danger')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('upload.html')

@main.route('/download/csv-template')
def download_csv_template():
    """Download a CSV template for bulk upload."""
    # This would typically generate a CSV file with headers
    # For simplicity, we'll just render a page with the template structure
    return render_template('csv_template.html')

@main.route('/suppliers')
def suppliers():
    """List all suppliers."""
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@main.route('/supplier/new', methods=['GET', 'POST'])
def new_supplier():
    """Create a new supplier."""
    if request.method == 'POST':
        supplier_code = request.form.get('supplier_code')
        address = request.form.get('address')
        
        # Check if supplier_code already exists
        existing = Supplier.query.filter_by(supplier_code=supplier_code).first()
        if existing:
            flash('Supplier code already exists.', 'danger')
            return render_template('supplier_form.html')
        
        supplier = Supplier(supplier_code=supplier_code, address=address)
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier created successfully!', 'success')
        return redirect(url_for('main.suppliers'))
    
    return render_template('supplier_form.html')

@main.route('/api/categories')
def api_categories():
    """API endpoint to get all categories."""
    categories = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

@main.route('/api/colors')
def api_colors():
    """API endpoint to get all colors."""
    colors = Color.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in colors])

@main.route('/api/materials')
def api_materials():
    """API endpoint to get all materials."""
    materials = Material.query.all()
    return jsonify([{'id': m.id, 'name': m.name} for m in materials])

@main.route('/api/suppliers')
def api_suppliers():
    """API endpoint to get all suppliers."""
    suppliers = Supplier.query.all()
    return jsonify([{'id': s.id, 'code': s.supplier_code, 'address': s.address} for s in suppliers])
