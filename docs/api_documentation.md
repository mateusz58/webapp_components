# API Documentation - Component Management System

**Last Updated**: July 7, 2025  
**API Version**: 2.0 - **MVC with Service Layer Architecture**  
**Base URL**: `http://localhost:6002/api`

## Overview

The Component Management System provides a RESTful API with proper MVC architecture and service layer separation. All business logic is centralized in service classes, ensuring consistency between API endpoints and web routes.

## 🏗️ Architecture Overview

### **MVC + Service Layer Pattern**
```
Frontend (Views) → Controllers (API/Web) → Services (Business Logic) → Models (Data)
```

- **Controllers** (`app/api/`, `app/web/`): Request/response handling only
- **Services** (`app/services/`): Business logic, validation, transaction management
- **Models** (`app/models.py`): Database entities and relationships only
- **Views** (`app/templates/`, `app/static/`): UI presentation only

### **Service Layer Benefits**
- **Centralized Business Logic**: Single source of truth for all operations
- **Code Reusability**: Same logic used by API and web routes
- **Transaction Safety**: Atomic operations with proper rollback
- **Testability**: Service layer can be unit tested independently

## Authentication & Security

- **CSRF Protection**: Production endpoints require CSRF token (`X-CSRFToken` header)
- **Content-Type**: Use `application/json` for API requests, `multipart/form-data` for file uploads
- **Error Handling**: Consistent JSON responses with proper HTTP status codes
- **Validation**: Service layer validates all business rules before database operations

## ✅ Core API Endpoints (FULLY IMPLEMENTED)

### Current Implementation Status

**✅ COMPLETE CRUD OPERATIONS:**
- Component Creation (`POST /component/create`) - ✅ With service layer
- Component Update (`PUT /component/<id>`) - ✅ **NEW: Service layer implementation**
- Component Data Loading (`GET /components/<id>/edit-data`) - ✅ With service layer
- Component Search & Filtering (`GET /components/search`)
- Variant Management (`GET /components/<id>/variants`)
- Brand Management (`GET/POST/DELETE /components/<id>/brands`)
- Bulk Operations (`POST /components/bulk-delete`)
- Export Functionality (`GET /components/<id>/export`)

**✅ ARCHITECTURE CONSISTENCY ACHIEVED:**
All endpoints now follow proper MVC pattern with service layer separation.

## Component Endpoints

### 🟢 POST /component/create
**Purpose**: Create new component with variants and pictures in single atomic operation

**Request**: `multipart/form-data`
```json
{
  "product_number": "string (required)",
  "description": "string",
  "component_type_id": "integer (required)",
  "supplier_id": "integer (optional)",
  "brand_ids[]": ["integer", "integer"],
  "category_ids[]": ["integer", "integer"],
  "keywords[]": ["string", "string"],
  "variant_color_1": "integer",
  "variant_custom_color_1": "string",
  "variant_images_1[]": ["file", "file"],
  "variant_color_2": "integer",
  "variant_images_2[]": ["file"]
}
```

**Response**: `application/json`
```json
{
  "success": true,
  "component_id": 123,
  "redirect_url": "/component/creation-loading/123",
  "message": "Component created successfully"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Product number already exists for supplier XYZ",
  "field": "product_number"
}
```

**Business Logic**:
1. Creates component with basic properties
2. Processes dynamic properties based on component type
3. Creates brand/category/keyword associations
4. Creates color variants with auto-generated SKUs
5. Uploads pictures with database-generated names
6. Sets session status for loading page workflow
7. Starts background verification thread

**File Handling**:
- Pictures stored in WebDAV at `/components/`
- Auto-generated names: `{supplier}_{product}_{color}_{order}.jpg`
- Atomic operations: database first, then files with cleanup on failure

### 🟢 PUT /component/<id> - **FULLY IMPLEMENTED WITH SERVICE LAYER**
**Purpose**: Update existing component via service layer architecture

**Request**: `application/json`
```json
PUT /api/component/123
Content-Type: application/json

{
  "product_number": "string",
  "description": "string",
  "component_type_id": "integer",
  "supplier_id": "integer",
  "brand_ids": ["integer"],
  "category_ids": ["integer"],
  "keywords": ["string"],
  "properties": {"key": "value"}
}
```

**Response**: `application/json`
```json
{
  "success": true,
  "component_id": 123,
  "message": "Component updated successfully",
  "timestamp": "2025-07-07T10:30:00.000Z",
  "changes": {
    "description": {"old": "Old description", "new": "New description"},
    "properties": {"old": {}, "new": {"material": "cotton"}},
    "keywords_added": ["summer", "casual"],
    "keywords_removed": ["winter"],
    "brands_added": [{"id": 5, "name": "Nike"}],
    "brands_removed": [{"id": 3, "name": "Adidas"}]
  }
}
```

**Service Layer Features**:
- **Centralized Business Logic**: All update operations handled by `ComponentService`
- **Atomic Transactions**: Database operations with proper rollback on failure
- **Change Tracking**: Detailed before/after value comparisons
- **Association Management**: Unified handling of brands, categories, keywords
- **Validation**: Business rule validation before database operations
- **Dual Data Support**: Handles both JSON and form data sources

**Error Response**:
```json
{
  "success": false,
  "error": "Component 123 not found",
  "code": "VALIDATION_ERROR",
  "timestamp": "2025-07-07T10:30:00.000Z"
}
```

### 🟢 GET /components/search
**Purpose**: Search and filter components with pagination

**Query Parameters**:
- `q`: Search term (product number, description)
- `supplier_id`: Filter by supplier
- `component_type_id`: Filter by component type
- `brand_id`: Filter by brand
- `category_id`: Filter by category
- `status`: Filter by approval status (pending, approved, rejected)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 12, max: 100)

**Response**:
```json
{
  "success": true,
  "components": [
    {
      "id": 123,
      "product_number": "ABC123",
      "description": "Sample component",
      "supplier": {"id": 1, "supplier_code": "SUP001"},
      "component_type": {"id": 2, "name": "Button"},
      "status": "approved",
      "created_at": "2025-07-07T10:00:00Z",
      "variant_count": 3,
      "picture_count": 5
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 12,
    "total": 156,
    "pages": 13,
    "has_next": true,
    "has_prev": false
  }
}
```

### 🟢 GET /components/<id>/edit-data
**Purpose**: Load complete component data for editing forms via service layer

**Response**: `application/json`
```json
{
  "success": true,
  "component": {
    "id": 123,
    "product_number": "ABC123",
    "description": "Component description",
    "component_type": {"id": 2, "name": "Button"},
    "supplier": {"id": 1, "supplier_code": "SUP001"},
    "properties": {"material": "cotton", "size": "12mm"},
    "brands": [{"id": 1, "name": "Nike"}],
    "categories": [{"id": 1, "name": "Apparel"}],
    "keywords": [{"id": 1, "name": "summer"}],
    "variants": [
      {
        "id": 456,
        "color": {"id": 1, "name": "Red"},
        "variant_sku": "sup001_abc123_red",
        "is_active": true,
        "pictures": [
          {
            "id": 789,
            "picture_name": "sup001_abc123_red_1",
            "url": "http://31.182.67.115/webdav/components/sup001_abc123_red_1.jpg",
            "picture_order": 1
          }
        ]
      }
    ],
    "proto_status": "ok",
    "sms_status": "pending",
    "pps_status": "pending"
  },
  "timestamp": "2025-07-07T10:30:00.000Z"
}
```

### 🟢 GET /components/<id>/variants
**Purpose**: Get component variants (used for auto-refresh after creation)

**Response**:
```json
{
  "success": true,
  "variants": [
    {
      "id": 456,
      "color_name": "Red",
      "variant_sku": "sup001_abc123_red",
      "is_active": true,
      "pictures": [
        {
          "url": "http://31.182.67.115/webdav/components/sup001_abc123_red_1.jpg",
          "alt_text": "ABC123 - Image 1"
        }
      ]
    }
  ]
}
```

## Brand Management Endpoints

### 🟢 GET/POST/DELETE /components/<id>/brands
**Purpose**: Manage component-brand associations

**GET** - List current brands:
```json
{
  "brands": [
    {"id": 1, "name": "Nike", "associated_at": "2025-07-07T10:00:00Z"}
  ]
}
```

**POST** - Add brand association:
```json
Request: {"brand_id": 2}
Response: {"success": true, "message": "Brand associated successfully"}
```

**DELETE** - Remove brand association:
```json
Request: {"brand_id": 1}
Response: {"success": true, "message": "Brand association removed"}
```

## Bulk Operations

### 🟢 POST /components/bulk-delete
**Purpose**: Delete multiple components

**Request**:
```json
{
  "component_ids": [123, 124, 125]
}
```

**Response**:
```json
{
  "success": true,
  "deleted_count": 3,
  "failed": [],
  "message": "3 components deleted successfully"
}
```

## Export Endpoints

### 🟢 GET /components/<id>/export
**Purpose**: Export single component data

**Response**: CSV file download

### 🟢 GET /components/export
**Purpose**: Export multiple components based on search criteria

**Query Parameters**: Same as search endpoint
**Response**: CSV file download with filtered results

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "field": "field_name",
  "details": {
    "additional": "context"
  }
}
```

### HTTP Status Codes
- `200 OK`: Successful GET requests
- `201 Created`: Successful POST requests (resource created)
- `400 Bad Request`: Validation errors, missing required fields
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: CSRF token missing/invalid
- `404 Not Found`: Resource not found
- `409 Conflict`: Duplicate data (e.g., product number exists)
- `413 Payload Too Large`: File upload exceeds 16MB limit
- `422 Unprocessable Entity`: Business logic validation errors
- `500 Internal Server Error`: Server errors

### Common Error Codes
- `VALIDATION_ERROR`: Field validation failed
- `DUPLICATE_PRODUCT_NUMBER`: Product number already exists
- `INVALID_FILE_TYPE`: Uploaded file type not allowed
- `FILE_TOO_LARGE`: File exceeds size limit
- `WEBDAV_ERROR`: File storage operation failed
- `DATABASE_ERROR`: Database operation failed

## File Upload Specifications

### Supported File Types
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`
- **Max Size**: 16MB per file
- **Storage**: WebDAV server at `http://31.182.67.115/webdav/components`

### Naming Convention
**Automatic Generation**: All picture names are auto-generated by the system
- **With Supplier**: `{supplier_code}_{product_number}_{color_name}_{order}.jpg`
- **Without Supplier**: `{product_number}_{color_name}_{order}.jpg`
- **Component Pictures**: Uses `main` instead of color name

**Examples**:
- `nike_shirt001_red_1.jpg`
- `shirt001_blue_2.jpg`
- `nike_shirt001_main_1.jpg`

## Database Integration

### Auto-Generated Fields
**Never manually set these fields** - handled by database triggers:
- `component_variant.variant_sku`
- `picture.picture_name`

### Relationships
- **Component → Variants**: One-to-many
- **Component → Brands**: Many-to-many via `component_brand`
- **Component → Categories**: Many-to-many via `component_category`
- **Component → Keywords**: Many-to-many via `keyword_component`
- **Variant → Pictures**: One-to-many
- **Component → Pictures**: One-to-many (component-level pictures)

### Transaction Management
All API endpoints use atomic transactions:
```python
try:
    # Database operations
    db.session.commit()
    # File operations
    save_files()
except Exception:
    db.session.rollback()
    cleanup_files()
    raise
```

## Performance Considerations

### Query Optimization
- Use `selectinload()` for collections
- Use `joinedload()` for single relationships
- Implement pagination for large datasets

### Concurrent Operations
- Picture verification uses ThreadPoolExecutor (10 concurrent requests)
- Background verification for component creation
- Non-blocking user experience

### Caching Strategy
- Component data cached during loading workflow
- Session-based status tracking for long operations

## API Versioning

**Current Version**: v1 (implicit in all endpoints)
**Future Versioning**: Will use URL versioning (`/api/v2/...`) when breaking changes required

## Development Guidelines

### Adding New Endpoints
1. **TDD**: Write failing tests first
2. **SOLID**: Single responsibility per endpoint
3. **DRY**: Use shared utilities (`association_handlers.py`)
4. **Consistency**: Follow existing patterns
5. **Documentation**: Update this file

### Testing Requirements
- Unit tests for business logic
- Integration tests for database operations
- End-to-end tests for complete workflows
- Selenium tests for UI integration

## ✅ ARCHITECTURE CONSISTENCY ACHIEVED

### 🎉 SERVICE LAYER IMPLEMENTATION COMPLETE
**Solution**: Implemented comprehensive service layer architecture with centralized business logic
**Impact**: Complete transformation from scattered logic to proper MVC architecture

**✅ RESOLVED ARCHITECTURE ISSUES**:
- ✅ **Component Update Endpoint**: `PUT /api/component/<id>` fully implemented with service layer
- ✅ **Centralized Business Logic**: `ComponentService` class handles all component operations
- ✅ **Consistent Architecture**: Both creation and editing now use same service layer pattern
- ✅ **Dual Data Support**: Association handlers work with both JSON (API) and form data (web routes)
- ✅ **Transaction Safety**: Atomic operations with proper rollback handling

**Current Architecture Status**:
- **Component Creation**: Web route + API endpoint with service layer ✅
- **Component Editing**: Web route + API endpoint with service layer ✅

**Service Layer Benefits Achieved**:
- **Code Deduplication**: Single source of truth for component operations
- **Maintainability**: Business logic centralized in service classes
- **Testability**: Service layer can be unit tested independently
- **Consistency**: Same behavior across API and web routes
- **Error Handling**: Unified error handling and validation

The Component Management System now follows proper MVC architecture with service layer separation, ensuring scalable and maintainable code.