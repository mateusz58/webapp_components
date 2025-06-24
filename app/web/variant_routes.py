from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from app import db
from app.models import Component, ComponentVariant, Color, Picture
from app.utils.file_handling import save_uploaded_file, allowed_file
from sqlalchemy import func
import os
import uuid
from werkzeug.utils import secure_filename

variant_web = Blueprint('variant_web', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# File handling functions are imported from app.utils.file_handling


@variant_web.route('/component/<int:id>/variant/new', methods=['GET', 'POST'])
def new_variant(id):
    """
    Create a new variant for a component
    """
    component = Component.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            color_id = request.form.get('color_id', type=int)
            variant_name = request.form.get('variant_name', '').strip()
            description = request.form.get('description', '').strip()
            is_active = request.form.get('is_active') == 'on'
            
            if not color_id:
                flash('Color selection is required.', 'error')
                return redirect(request.url)
            
            # Check if variant already exists for this color
            existing = ComponentVariant.query.filter_by(
                component_id=component.id,
                color_id=color_id
            ).first()
            
            if existing:
                flash('A variant with this color already exists for this component.', 'error')
                return redirect(request.url)
            
            # Create variant
            variant = ComponentVariant(
                component_id=component.id,
                color_id=color_id,
                variant_name=variant_name,
                description=description,
                is_active=is_active
            )
            
            db.session.add(variant)
            db.session.flush()  # Get variant ID
            
            # Handle picture uploads
            pictures = request.files.getlist('pictures')
            picture_order = 1
            
            for picture_file in pictures:
                if picture_file and allowed_file(picture_file.filename):
                    url = save_uploaded_file(picture_file)
                    if url:
                        # Get color name for alt text
                        color = Color.query.get(color_id)
                        color_name = color.name if color else 'Unknown'
                        
                        picture = Picture(
                            component_id=component.id,
                            variant_id=variant.id,
                            url=url,
                            picture_order=picture_order,
                            alt_text=f"{component.product_number} - {color_name} - Image {picture_order}"
                        )
                        db.session.add(picture)
                        picture_order += 1
            
            db.session.commit()
            flash('Variant created successfully!', 'success')
            return redirect(url_for('component_web.component_detail', id=component.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Variant creation error: {str(e)}")
            flash(f'Error creating variant: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    colors = Color.query.order_by(Color.name).all()
    
    # Filter out colors already used in variants
    existing_color_ids = [v.color_id for v in component.variants]
    available_colors = [c for c in colors if c.id not in existing_color_ids]
    
    return render_template('variant_form.html',
                         component=component,
                         colors=available_colors,
                         variant=None)


@variant_web.route('/component/<int:component_id>/variant/<int:variant_id>/edit', methods=['GET', 'POST'])
def edit_variant(component_id, variant_id):
    """
    Edit an existing variant
    """
    component = Component.query.get_or_404(component_id)
    variant = ComponentVariant.query.filter_by(
        id=variant_id,
        component_id=component_id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update variant fields
            variant.variant_name = request.form.get('variant_name', '').strip()
            variant.description = request.form.get('description', '').strip()
            variant.is_active = request.form.get('is_active') == 'on'
            
            # Note: We don't allow changing the color of an existing variant
            # as it could break SKU consistency
            
            # Handle new picture uploads
            new_pictures = request.files.getlist('new_pictures')
            
            # Get the highest existing picture order for this variant
            max_order = db.session.query(func.max(Picture.picture_order)).filter_by(
                variant_id=variant.id
            ).scalar() or 0
            
            picture_order = max_order + 1
            
            for picture_file in new_pictures:
                if picture_file and allowed_file(picture_file.filename):
                    url = save_uploaded_file(picture_file)
                    if url:
                        picture = Picture(
                            component_id=component.id,
                            variant_id=variant.id,
                            url=url,
                            picture_order=picture_order,
                            alt_text=f"{component.product_number} - {variant.color.name} - Image {picture_order}"
                        )
                        db.session.add(picture)
                        picture_order += 1
            
            db.session.commit()
            flash('Variant updated successfully!', 'success')
            return redirect(url_for('component_web.component_detail', id=component.id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Variant update error: {str(e)}")
            flash(f'Error updating variant: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    colors = Color.query.order_by(Color.name).all()
    
    return render_template('variant_form.html',
                         component=component,
                         colors=colors,
                         variant=variant)


@variant_web.route('/component/<int:component_id>/variant/<int:variant_id>/delete', methods=['POST'])
def delete_variant(component_id, variant_id):
    """
    Delete a variant
    """
    try:
        variant = ComponentVariant.query.filter_by(
            id=variant_id,
            component_id=component_id
        ).first_or_404()
        
        # Delete associated pictures from filesystem
        for picture in variant.pictures:
            if picture.url:
                file_path = os.path.join(current_app.static_folder, picture.url.lstrip('/'))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Delete variant (cascades will handle pictures)
        db.session.delete(variant)
        db.session.commit()
        
        flash('Variant deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Variant deletion error: {str(e)}")
        flash(f'Error deleting variant: {str(e)}', 'error')
    
    return redirect(url_for('component_web.component_detail', id=component_id))