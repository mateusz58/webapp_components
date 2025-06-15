"""Response utilities for consistent API responses."""

from flask import jsonify, make_response
from typing import Any, Dict, Optional, Union
import traceback


class ApiResponse:
    """Standardized API response helper."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """Return a successful response."""
        response_data = {
            "success": True,
            "message": message,
            "data": data
        }
        return jsonify(response_data), status_code
    
    @staticmethod
    def error(message: str = "An error occurred", 
              errors: Optional[Dict] = None, 
              status_code: int = 400,
              include_traceback: bool = False) -> tuple:
        """Return an error response."""
        response_data = {
            "success": False,
            "message": message,
            "errors": errors or {}
        }
        
        if include_traceback:
            response_data["traceback"] = traceback.format_exc()
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def validation_error(errors: Dict, message: str = "Validation failed") -> tuple:
        """Return a validation error response."""
        return ApiResponse.error(message=message, errors=errors, status_code=422)
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> tuple:
        """Return a not found response."""
        return ApiResponse.error(message=message, status_code=404)
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> tuple:
        """Return an unauthorized response."""
        return ApiResponse.error(message=message, status_code=401)
    
    @staticmethod
    def forbidden(message: str = "Forbidden") -> tuple:
        """Return a forbidden response."""
        return ApiResponse.error(message=message, status_code=403)
    
    @staticmethod
    def server_error(message: str = "Internal server error") -> tuple:
        """Return a server error response."""
        return ApiResponse.error(message=message, status_code=500, include_traceback=True)


class WebResponse:
    """Helper for web responses (redirects, templates)."""
    
    @staticmethod
    def flash_and_redirect(message: str, category: str, endpoint: str, **kwargs):
        """Flash a message and redirect."""
        from flask import flash, redirect, url_for
        flash(message, category)
        return redirect(url_for(endpoint, **kwargs))
    
    @staticmethod
    def success_redirect(message: str, endpoint: str, **kwargs):
        """Flash success message and redirect."""
        return WebResponse.flash_and_redirect(message, 'success', endpoint, **kwargs)
    
    @staticmethod
    def error_redirect(message: str, endpoint: str, **kwargs):
        """Flash error message and redirect."""
        return WebResponse.flash_and_redirect(message, 'error', endpoint, **kwargs)


def handle_file_upload_response(success: bool, message: str, redirect_endpoint: str = None, **kwargs):
    """Handle file upload response for both API and web requests."""
    from flask import request
    
    # Check if it's an API request (JSON or AJAX)
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if success:
            return ApiResponse.success(message=message)
        else:
            return ApiResponse.error(message=message)
    else:
        # Web request
        if success:
            return WebResponse.success_redirect(message, redirect_endpoint, **kwargs)
        else:
            return WebResponse.error_redirect(message, redirect_endpoint, **kwargs)


def paginated_response(query, page: int, per_page: int, endpoint: str, **kwargs):
    """Create a paginated response."""
    from flask import url_for
    
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Build pagination URLs
    next_url = url_for(endpoint, page=pagination.next_num, per_page=per_page, **kwargs) \
        if pagination.has_next else None
    prev_url = url_for(endpoint, page=pagination.prev_num, per_page=per_page, **kwargs) \
        if pagination.has_prev else None
    
    return {
        'items': pagination.items,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_url': next_url,
            'prev_url': prev_url
        }
    }