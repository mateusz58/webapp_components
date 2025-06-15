"""File handling utilities."""

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import io
from typing import Optional, Tuple


# File configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
THUMBNAIL_SIZE = (300, 300)


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    if not filename:
        return None
    
    # Secure the filename first
    filename = secure_filename(filename)
    
    # Generate unique filename with UUID
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}_{name}{ext}"
    
    return unique_filename


def optimize_image(image_file, max_size: Tuple[int, int] = (1920, 1920), quality: int = 85) -> Optional[io.BytesIO]:
    """Optimize image for web display."""
    try:
        image = Image.open(image_file)

        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Resize if larger than max_size
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)

        return output
    except Exception as e:
        current_app.logger.error(f"Image optimization error: {str(e)}")
        return None


def save_uploaded_file(file, folder: str = 'uploads', optimize_images: bool = True) -> Optional[str]:
    """Save uploaded file and return the relative URL."""
    if not file or not allowed_file(file.filename):
        return None

    try:
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        if not unique_filename:
            return None

        # Create upload directory if it doesn't exist
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)

        # Full file path
        file_path = os.path.join(upload_path, unique_filename)

        # Optimize images if requested and file is an image
        if optimize_images and any(ext in file.filename.lower() for ext in ['jpg', 'jpeg', 'png']):
            optimized = optimize_image(file)
            if optimized:
                with open(file_path, 'wb') as f:
                    f.write(optimized.getvalue())
            else:
                # Fall back to saving original file
                file.save(file_path)
        else:
            # Save file directly
            file.save(file_path)

        # Return relative URL for web access
        return f"/static/uploads/{folder}/{unique_filename}"

    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return None


def delete_file(file_url: str) -> bool:
    """Delete a file given its URL."""
    try:
        if not file_url or not file_url.startswith('/static/uploads/'):
            return False
        
        # Convert URL to file path
        relative_path = file_url.replace('/static/uploads/', '')
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        return False


def create_thumbnail(image_path: str, thumbnail_size: Tuple[int, int] = THUMBNAIL_SIZE) -> Optional[str]:
    """Create a thumbnail for an image."""
    try:
        if not os.path.exists(image_path):
            return None
        
        # Generate thumbnail filename
        name, ext = os.path.splitext(image_path)
        thumbnail_path = f"{name}_thumb{ext}"
        
        # Create thumbnail
        with Image.open(image_path) as image:
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            image.save(thumbnail_path, quality=85, optimize=True)
        
        return thumbnail_path
    except Exception as e:
        current_app.logger.error(f"Thumbnail creation error: {str(e)}")
        return None


def validate_file_size(file, max_size: int = MAX_CONTENT_LENGTH) -> bool:
    """Validate file size."""
    try:
        # Seek to end to get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        return file_size <= max_size
    except:
        return False


def get_file_info(file_path: str) -> dict:
    """Get file information."""
    try:
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        current_app.logger.error(f"Error getting file info: {str(e)}")
        return {}