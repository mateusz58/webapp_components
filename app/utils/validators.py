"""Validation utilities."""

import re
from typing import List, Dict, Any, Optional
from werkzeug.datastructures import FileStorage


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class Validator:
    """Base validator class."""
    
    def __init__(self, required: bool = False, message: str = None):
        self.required = required
        self.message = message
    
    def validate(self, value: Any, field_name: str = None) -> Any:
        """Override this method in subclasses."""
        if self.required and (value is None or value == ''):
            raise ValidationError(
                self.message or f"{field_name or 'Field'} is required",
                field_name
            )
        return value


class StringValidator(Validator):
    """String validation."""
    
    def __init__(self, min_length: int = None, max_length: int = None, 
                 pattern: str = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
    
    def validate(self, value: Any, field_name: str = None) -> str:
        value = super().validate(value, field_name)
        
        if value is None or value == '':
            return value
        
        if not isinstance(value, str):
            value = str(value)
        
        if self.min_length and len(value) < self.min_length:
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be at least {self.min_length} characters",
                field_name
            )
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be no more than {self.max_length} characters",
                field_name
            )
        
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                self.message or f"{field_name or 'Field'} has invalid format",
                field_name
            )
        
        return value.strip()


class EmailValidator(StringValidator):
    """Email validation."""
    
    def __init__(self, **kwargs):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        kwargs.setdefault('pattern', email_pattern)
        kwargs.setdefault('message', 'Invalid email address')
        super().__init__(**kwargs)


class IntegerValidator(Validator):
    """Integer validation."""
    
    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any, field_name: str = None) -> Optional[int]:
        value = super().validate(value, field_name)
        
        if value is None or value == '':
            return None
        
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be an integer",
                field_name
            )
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be at least {self.min_value}",
                field_name
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be no more than {self.max_value}",
                field_name
            )
        
        return value


class FileValidator(Validator):
    """File validation."""
    
    def __init__(self, allowed_extensions: List[str] = None, 
                 max_size: int = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.max_size = max_size
    
    def validate(self, value: Any, field_name: str = None) -> Optional[FileStorage]:
        value = super().validate(value, field_name)
        
        if value is None:
            return None
        
        if not isinstance(value, FileStorage):
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be a file",
                field_name
            )
        
        if not value.filename:
            if self.required:
                raise ValidationError(
                    self.message or f"{field_name or 'Field'} is required",
                    field_name
                )
            return None
        
        # Check file extension
        if self.allowed_extensions:
            file_ext = value.filename.rsplit('.', 1)[-1].lower()
            if file_ext not in self.allowed_extensions:
                raise ValidationError(
                    self.message or f"File must have one of these extensions: {', '.join(self.allowed_extensions)}",
                    field_name
                )
        
        # Check file size
        if self.max_size:
            # Get file size
            value.seek(0, 2)  # Seek to end
            file_size = value.tell()
            value.seek(0)  # Reset to beginning
            
            if file_size > self.max_size:
                raise ValidationError(
                    self.message or f"File size must be less than {self.max_size / (1024*1024):.1f}MB",
                    field_name
                )
        
        return value


class ChoiceValidator(Validator):
    """Choice validation."""
    
    def __init__(self, choices: List[Any], **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
    
    def validate(self, value: Any, field_name: str = None) -> Any:
        value = super().validate(value, field_name)
        
        if value is None or value == '':
            return value
        
        if value not in self.choices:
            raise ValidationError(
                self.message or f"{field_name or 'Field'} must be one of: {', '.join(map(str, self.choices))}",
                field_name
            )
        
        return value


def validate_data(data: Dict[str, Any], validators: Dict[str, Validator]) -> Dict[str, Any]:
    """
    Validate a dictionary of data against validators.
    Returns validated data or raises ValidationError.
    """
    validated_data = {}
    errors = {}
    
    for field_name, validator in validators.items():
        try:
            value = data.get(field_name)
            validated_data[field_name] = validator.validate(value, field_name)
        except ValidationError as e:
            errors[field_name] = e.message
    
    if errors:
        raise ValidationError("Validation failed", errors)
    
    return validated_data


# Common validators
supplier_code_validator = StringValidator(
    required=True,
    min_length=3,
    max_length=10,
    pattern=r'^[A-Z0-9]+$',
    message="Supplier code must be 3-10 uppercase letters/numbers"
)

email_validator = EmailValidator()

product_number_validator = StringValidator(
    required=True,
    min_length=1,
    max_length=50,
    message="Product number is required and must be 1-50 characters"
)

description_validator = StringValidator(
    max_length=1000,
    message="Description must be no more than 1000 characters"
)

id_validator = IntegerValidator(
    required=True,
    min_value=1,
    message="Valid ID is required"
)

image_file_validator = FileValidator(
    allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
    max_size=16 * 1024 * 1024,  # 16MB
    message="Image must be PNG, JPG, JPEG, GIF, or WebP and less than 16MB"
)