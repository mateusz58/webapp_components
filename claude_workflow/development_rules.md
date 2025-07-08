# Development Rules & Patterns

**Last Updated**: January 8, 2025 - Added Comprehensive Testing Framework and Requirements.txt Management

## 🚨 CRITICAL: MANDATORY TESTING REQUIREMENTS 🚨

### BEFORE ANY DEVELOPMENT WORK (ABSOLUTE REQUIREMENT)
**ALL TESTS MUST PASS BEFORE PROCEEDING WITH ANY TASK**

1. **Run Test Suite**: Execute `python tools/run_tests.py` before starting ANY development work
2. **Fix Failing Tests**: If any tests fail, STOP development and fix them first
3. **No Exceptions**: No new features, bug fixes, or refactoring until all tests pass
4. **After Changes**: Run full test suite again after making ANY changes
5. **Commit Only Green**: Only commit code when all tests are passing

### Test Organization Structure (MANDATORY)
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Fast isolated tests (< 1s each)
│   ├── test_validation_functions.py    # Input validation logic
│   ├── test_data_processing.py         # Data parsing and transformation
│   ├── test_utility_functions.py       # Helper functions (SKU, naming)
│   └── test_component_service.py       # Business logic (mocked dependencies)
├── integration/             # Database integration tests (< 5s each)
│   ├── test_component_crud.py          # Database operations
│   ├── test_picture_upload.py          # File + database integration
│   └── test_association_handling.py    # Many-to-many relationships
├── api/                     # API endpoint tests (< 3s each)
│   ├── test_component_api.py           # Component CRUD endpoints
│   ├── test_validation_endpoints.py    # Validation endpoints
│   └── test_error_handling.py          # API error responses
├── selenium/                # E2E UI tests (10-30s each)
│   ├── test_component_edit_form.py     # Complete form workflows
│   ├── test_picture_visibility.py      # UI visibility issues
│   └── test_ajax_interactions.py       # Real-time UI updates
├── services/                # Service layer tests (business logic)
├── utils/                   # Utility function tests
└── models/                  # Database model tests
```

### Test Type Definitions (CRITICAL)

#### Unit Tests (`tests/unit/`)
**Purpose**: Test individual functions and methods in isolation
- **Speed**: < 1 second each
- **Dependencies**: All external dependencies mocked (database, files, APIs)
- **Focus**: Logic validation, data transformation, calculations
- **Examples**: 
  - Validation functions (product number format, JSON parsing)
  - Data processing (SKU generation, string normalization) 
  - Helper utilities (response building, file info extraction)
  - Business logic with mocked database calls

#### Integration Tests (`tests/integration/`)
**Purpose**: Test interaction between components (database + code)
- **Speed**: < 5 seconds each
- **Dependencies**: Real database, mocked external services (WebDAV)
- **Focus**: Database operations, ORM relationships, transaction handling
- **Examples**:
  - Component CRUD with real database
  - Picture upload workflow with database triggers
  - Association management (brands, categories, keywords)
  - Database constraint validation

#### API Tests (`tests/api/`)
**Purpose**: Test HTTP endpoints end-to-end
- **Speed**: < 3 seconds each  
- **Dependencies**: Real Flask app, real database, mocked external services
- **Focus**: Request/response handling, status codes, JSON format
- **Examples**:
  - Component creation via POST /api/component/create
  - Component update via PUT /api/component/<id>
  - Validation endpoints (product number uniqueness)
  - Error handling (404, 400, 500 responses)

#### Selenium Tests (`tests/selenium/`)
**Purpose**: Test complete user workflows in browser
- **Speed**: 10-30 seconds each
- **Dependencies**: Real application, real browser, real database
- **Focus**: UI interactions, JavaScript functionality, visual validation
- **Examples**:
  - Complete component creation workflow
  - Picture upload and immediate visibility
  - Form validation and error display
  - AJAX real-time updates

### 🚨 CRITICAL TEST ORGANIZATION RULES 🚨
1. **❌ NEVER CREATE TEST FILES IN ROOT DIRECTORY ❌**
   - All test files MUST be in appropriate `tests/` subdirectories
   - Root directory is for application code only
   
2. **✅ PROPER TEST FILE NAMING**:
   - Format: `test_[feature]_[type].py`
   - Examples: `test_component_edit_api.py`, `test_picture_upload_integration.py`
   
3. **✅ COMPREHENSIVE DEBUG LOGGING**:
   - Every test MUST include extensive debug output
   - Use `print()` statements for test flow tracking
   - Log request/response data, status codes, errors
   
4. **✅ TEST CATEGORIZATION**:
   - **Fast Tests** (`unit/` + `integration/`): < 10 seconds total
   - **Medium Tests** (`api/`): < 30 seconds total  
   - **Slow Tests** (`selenium/`): < 5 minutes total

### Test Execution Commands (MANDATORY)
```bash
# BEFORE ANY DEVELOPMENT - Run all tests
python tools/run_tests.py

# Run specific test categories
python tools/run_tests.py --unit              # Unit tests only
python tools/run_tests.py --integration       # Integration tests only  
python tools/run_tests.py --api               # API tests only
python tools/run_tests.py --selenium          # UI tests only
python tools/run_tests.py --fast              # Unit + Integration (fastest)
python tools/run_tests.py --coverage          # With coverage report

# Development workflow
python tools/run_tests.py --fast              # Quick feedback during development
python tools/run_tests.py                     # Full test suite before commit
```

### Testing Rules (NON-NEGOTIABLE)
1. **NO TEMPORARY TESTS IN ROOT**: All tests must be in `tests/` folder with proper organization
2. **NO BROKEN TESTS**: Failing tests must be fixed immediately, not ignored
3. **NO DEVELOPMENT ON RED**: Do not write new code when tests are failing
4. **CLEAN TEST CODE**: Tests must be maintainable and well-organized
5. **TEST COVERAGE**: New features require corresponding tests
6. **ISOLATION**: Tests must not depend on each other or external state

### Test Failure Protocol (MANDATORY)
When tests fail:
1. **STOP ALL DEVELOPMENT WORK**
2. **Analyze the failure** - read the error messages carefully
3. **Fix the root cause** - don't just make tests pass artificially
4. **Run full test suite** - ensure fix doesn't break other tests
5. **Only then continue** with planned development work

## TDD (Test-Driven Development) Methodology

### TDD Workflow (MANDATORY)
All new features and bug fixes MUST follow Red-Green-Refactor cycle:

1. **RED**: Write failing test first
   - Write test that describes the desired behavior
   - Run test to confirm it fails (especially for race conditions)
   - Test should fail for the right reason
   - Use Selenium for UI race condition testing

2. **GREEN**: Write minimal code to pass
   - Implement simplest solution that makes test pass
   - Don't optimize yet - just make it work
   - Run test to confirm it passes
   - Validate with millisecond-precision Selenium tests

3. **REFACTOR**: Improve code quality
   - Clean up code while keeping tests green
   - Remove duplication, improve readability
   - Ensure all tests still pass
   - Add comprehensive console logging for debugging

### TDD Rules for This Project
- **No production code** without a failing test first
- **Tests must be isolated** - no dependencies between tests
- **Use descriptive test names** that explain behavior
- **Test one behavior per test** - keep tests focused
- **Mock external dependencies** (WebDAV, file system)

### Testing Framework Structure
```python
# Test file naming: test_<module>_<feature>.py
# Test class naming: Test<Feature><Behavior>
# Test method naming: test_<action>_<expected_result>

class TestComponentPictureVisibility:
    def test_create_variant_with_picture_shows_immediately(self):
        # Given: component exists
        # When: variant with picture is created
        # Then: picture is visible in component detail
```

### Testing Patterns for Flask Components

#### Unit Tests (Fast)
```python
# Test business logic in isolation
def test_generate_variant_sku_with_supplier():
    # Test SKU generation logic
    pass

def test_picture_name_generation():
    # Test picture naming logic
    pass
```

#### Integration Tests (Medium)
```python
# Test database operations
def test_component_variant_creation_updates_sku():
    # Test database triggers work correctly
    pass

def test_picture_save_with_rollback():
    # Test transaction rollback on file save failure
    pass
```

#### End-to-End Tests (Slow)
```python
# Test complete user workflows
def test_component_edit_picture_visibility_workflow():
    # Test complete picture upload and visibility
    pass
```

### Test Data Management
- Use **fixtures** for consistent test data
- **Clean up after tests** - restore database state
- **Use test-specific data** - avoid shared state
- **Mock WebDAV operations** for unit tests

### TDD for UI Race Conditions (PROVEN PATTERN)
1. **Write Selenium test** that detects timing issues with millisecond precision
2. **Implement multi-layer solutions** to pass all timing scenarios
3. **Refactor** with console logging and comprehensive fallbacks

Example Pattern for Loading Indicators:
- Layer 1: Immediate CSS (`body[data-attribute]`)
- Layer 2: JavaScript URL parameter detection
- Layer 3: Alpine.js component factory initialization
- Layer 4: API auto-refresh with exponential backoff

### Testing Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_component_pictures.py

# Run with coverage
pytest --cov=app

# Run only fast tests
pytest -m "not slow"
```

## MVC Architecture Implementation (MANDATORY)

### Proper MVC Pattern
**CRITICAL REQUIREMENT**: This project MUST follow strict Model-View-Controller architecture with Service Layer separation.

#### Model Layer (`app/models.py`)
- **Purpose**: Database entities and basic data operations only
- **Responsibilities**: SQLAlchemy models, relationships, simple property getters/setters
- **NO BUSINESS LOGIC**: Models should only contain data structure and basic validation
- **Database Relationships**: Properly defined foreign keys and relationships

```python
# Good: Model with data structure only
class Component(Base):
    __tablename__ = 'component'
    
    id = db.Column(db.Integer, primary_key=True)
    product_number = db.Column(db.String(50), nullable=False)
    
    # Relationships
    variants = db.relationship('ComponentVariant', backref='component')
    
    def get_property(self, key, default=None):
        # Simple property getter - acceptable in model
        return self.properties.get(key, default)

# Bad: Business logic in model
class Component(Base):
    def create_with_variants_and_pictures(self, data):
        # Complex business logic - BELONGS IN SERVICE LAYER
        pass
```

#### View Layer (`app/templates/`, `app/static/`)
- **Purpose**: User interface presentation only  
- **Templates**: Data display, form rendering, user interaction
- **JavaScript**: UI interactions, API calls, DOM manipulation
- **CSS**: Styling and visual presentation
- **NO BUSINESS LOGIC**: Views should only handle presentation

```html
<!-- Good: View with presentation only -->
<form id="componentForm">
    {{ csrf_token() }}
    <input name="product_number" value="{{ component.product_number }}">
    <button type="submit">Update Component</button>
</form>

<script>
// Good: View handles UI and calls service via API
async function submitForm() {
    const response = await fetch('/api/component/123', {
        method: 'PUT',
        body: formData
    });
    // Handle UI updates based on response
}
</script>
```

#### Controller Layer (`app/web/`, `app/api/`)
- **Purpose**: Request/response handling and routing only
- **Web Routes**: Render templates, handle navigation, simple redirects
- **API Routes**: Handle HTTP requests, delegate to service layer, return JSON
- **NO BUSINESS LOGIC**: Controllers should delegate all business logic to service layer

```python
# Good: Controller delegates to service
@component_api.route('/component/<int:component_id>', methods=['PUT'])
def update_component(component_id):
    try:
        data = request.get_json()
        
        # Delegate to service layer
        from app.services.component_service import ComponentService
        result = ComponentService.update_component(component_id, data)
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# Bad: Business logic in controller
@component_api.route('/component/<int:component_id>', methods=['PUT'])
def update_component(component_id):
    # Database operations, validation, association handling - BELONGS IN SERVICE
    component = Component.query.get_or_404(component_id)
    handle_brand_associations(component, data)
    db.session.commit()
```

#### Service Layer (`app/services/`) - **MANDATORY**
- **Purpose**: Business logic, data processing, orchestration
- **Responsibilities**: Component CRUD operations, validation, association management
- **Transaction Management**: Database commits, rollbacks, error handling
- **Cross-cutting Concerns**: Logging, error handling, data transformation

```python
# Good: Service layer with business logic
class ComponentService:
    @staticmethod
    def update_component(component_id, data):
        try:
            component = Component.query.get(component_id)
            if not component:
                raise ValueError(f'Component {component_id} not found')
            
            # Business logic
            changes = ComponentService._update_basic_fields(component, data)
            ComponentService._handle_associations(component, data, is_edit=True)
            
            # Validation
            ComponentService._validate_component(component)
            
            # Persistence
            db.session.commit()
            
            return {'success': True, 'changes': changes}
        except Exception as e:
            db.session.rollback()
            raise
```

### Architecture Rules

#### 1. Service Layer Requirements (NEW)
- **EVERY** complex operation must have a corresponding service class
- Services handle: CRUD operations, validation, business rules, transaction management
- Services are **stateless** - no instance variables for business data
- Services use **static methods** for operations or dependency injection pattern

#### 2. Controller Responsibilities
- **Web Controllers**: `render_template()`, `redirect()`, simple data passing only
- **API Controllers**: Request parsing, service delegation, JSON response formatting
- **Maximum 20 lines** per controller method (excluding error handling)
- **NO database operations** directly in controllers

#### 3. Model Responsibilities  
- **Data structure only**: Columns, relationships, constraints
- **Simple getters/setters**: Property access methods
- **NO business logic**: No complex operations, validations, or external calls
- **NO service calls**: Models should not call services or other models

#### 4. View Responsibilities
- **Templates**: Data display using passed context variables only
- **JavaScript**: UI interactions, API calls, DOM updates
- **NO business logic**: No data validation, processing, or complex calculations

### Dependency Flow (MANDATORY)
```
View Layer (Templates/JS) 
    ↓ (HTTP requests)
Controller Layer (Web/API routes)
    ↓ (method calls)
Service Layer (Business logic)
    ↓ (ORM calls)  
Model Layer (Database entities)
```

**NEVER REVERSE THE FLOW**: Models must not call services, services must not render templates, etc.

### Error Handling Architecture
- **Models**: Raise `ValueError` for data validation errors
- **Services**: Catch model errors, add business context, log errors, re-raise with context
- **Controllers**: Catch service errors, convert to appropriate HTTP responses
- **Views**: Display user-friendly error messages from controller responses

### Testing Architecture
- **Unit Tests**: Test service layer business logic in isolation
- **Integration Tests**: Test controller + service + model integration  
- **End-to-End Tests**: Test complete view → controller → service → model flow

## Core Development Constraints

### 1. Database Operations
- **ALWAYS** use database triggers for SKU and picture name generation
- **NEVER** manually set `variant_sku` or `picture_name` fields
- Use `selectinload` for better performance with collections
- All models inherit from `Base` class with `component_app` schema
- Clear session cache with `db.session.expunge_all()` after picture operations

### 2. Picture Management Rules
- Pictures stored in `/components/` directory (no subfolders)
- Automatic naming: `{supplier_code}_{product_number}_{color}_{order}` or `{product_number}_{color}_{order}`
- WebDAV URL prefix: `http://31.182.67.115/webdav/components`
- Image optimization: max 1920x1920, JPEG quality 85
- Always implement transaction rollback for failed saves

### 3. File Upload Workflow (MANDATORY)
1. Files read into memory during form processing
2. Database records created first (triggers generate names)
3. Files saved to disk with generated names
4. URLs updated in database
5. Session cache cleared with `db.session.expunge_all()`

### 4. Component Variant Rules
- Each component must have at least one variant
- Each variant must have at least one picture
- Colors are unique per component
- SKUs auto-generated by database triggers

## Required Code Patterns

### Database Query Pattern
```python
# ALWAYS use selectinload for collections
component = Component.query.options(
    joinedload(Component.component_type),
    selectinload(Component.variants).joinedload(ComponentVariant.color),
    selectinload(Component.pictures)
).get_or_404(id)
```

### Atomic File Operations Pattern (REQUIRED)
```python
# CRITICAL: Database operations BEFORE file operations
all_pending_files = []  # Track files to save after DB commit
saved_files = []        # Track saved files for cleanup

try:
    # 1. Database operations first
    # Create component/variants/pictures (triggers generate names)
    db.session.commit()  # Commit database first
    
    # 2. File operations second  
    for file_info in all_pending_files:
        file_path = save_file_with_db_name(file_info)
        saved_files.append(file_path)
        # Update URLs in database
    
    db.session.commit()  # Commit URL updates
    
except Exception:
    # Clean up any saved files on failure
    for file_path in saved_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.rollback()
    raise
```

### CSRF Protection (MANDATORY)
- All forms must include `{{ csrf_token() }}`
- AJAX requests must include `X-CSRFToken` header

## Areas of Caution

### 1. Session Caching Issues
- Use `db.session.expunge_all()` after picture operations
- Implement AJAX refresh for data consistency
- Multiple retry attempts with exponential backoff

### 2. File Operations
- Always use atomic operations for file saving
- Implement proper cleanup on failures
- Validate file types server-side

### 3. Database Triggers
- Never bypass database-generated fields
- Understand trigger cascade effects
- Test SKU/name generation after changes

## Dependency Management (MANDATORY)

### Requirements.txt Management (CRITICAL)
**ALWAYS keep requirements.txt updated with exact versions**:

#### When to Update requirements.txt:
1. **Adding new dependencies**: Immediately after `pip install <package>`
2. **Updating existing packages**: After version upgrades for compatibility
3. **Testing dependencies**: Add pytest, selenium, and testing frameworks
4. **Security updates**: When vulnerabilities are found in dependencies
5. **Project setup**: When setting up development environment

#### Requirements.txt Best Practices:
```bash
# Generate exact current environment
pip freeze > requirements.txt

# Install from requirements in new environment  
pip install -r requirements.txt

# Add new package and update requirements
pip install new-package==1.2.3
pip freeze > requirements.txt
```

#### Version Pinning Strategy:
- **Production dependencies**: Pin exact versions (Flask==2.0.1)
- **Development tools**: Pin major versions (pytest>=8.0.0,<9.0.0)
- **Security-critical packages**: Always pin exact versions
- **Stable packages**: Pin to avoid breaking changes

#### Required Dependencies Categories:
```txt
# Core Framework
Flask==2.0.1
SQLAlchemy==1.4.23
Flask-SQLAlchemy==2.5.1

# Database & Migrations  
psycopg2-binary==2.9.1
Flask-Migrate==3.1.0

# Security & Forms
Flask-WTF==0.15.1
Werkzeug==2.0.1

# Testing Framework
pytest==8.4.1
pytest-cov>=6.0.0
selenium>=4.15.0

# Development Tools
python-dotenv==0.19.0
```

#### Virtual Environment Management:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Keep requirements in sync
pip install -r requirements.txt
pip freeze > requirements.txt  # After any changes
```

## Code Quality Standards

### Code Documentation Rules
- **NO COMMENTS IN PYTHON FILES**: Never add comments, docstrings, or explanatory text to .py files
- **External Documentation Only**: Use markdown files in claude_workflow/ for all documentation
- **Clean Code**: Code should be self-explanatory without comments
- **Database Documentation**: Maintain separate database schema documentation

### Debugging and Logging Requirements (CRITICAL)
- **COMPREHENSIVE LOGGING**: Always add detailed logging for complex operations
- **LOG CRITICAL PATHS**: File operations, database operations, API calls must be logged
- **LOG VARIABLES**: Log important variable values (IDs, file names, counts, status)
- **LOG ERRORS**: Every exception must be logged with context
- **LOG FLOW**: Log entry/exit of critical functions with parameters

#### Required Logging Pattern:
```python
# Log function entry with parameters
current_app.logger.info(f"Starting operation X with param1={param1}, param2={param2}")

# Log important variable values
current_app.logger.info(f"Found {len(items)} items to process")

# Log before critical operations
current_app.logger.info(f"About to save file: {filename} to {path}")

# Log results of operations
current_app.logger.info(f"File saved successfully: {file_path}")

# Log errors with context
current_app.logger.error(f"Failed to save file {filename}: {str(e)}")
```

#### When to Add Logging:
1. **File Operations**: Upload, save, delete operations
2. **Database Operations**: Create, update, commit operations
3. **API Endpoints**: Request processing, validation, response
4. **Complex Logic**: Multi-step operations, loops, conditionals
5. **Error Handling**: All exception blocks
6. **Background Tasks**: Threading, async operations

### Error Handling
- Implement comprehensive try/catch blocks
- Log all file operations and errors
- Provide user-friendly error messages
- Always clean up resources on failure

### Performance Requirements
- Use selectinload for collections
- Implement query optimization
- Cache expensive operations
- Monitor database query performance

### Security Requirements
- CSRF protection on all forms
- File upload validation
- SQL injection prevention via SQLAlchemy
- Secure file handling practices

## Testing Requirements (Updated for TDD)

### TDD Testing Hierarchy
1. **Unit Tests** (milliseconds) - Business logic, utilities, model methods
2. **Integration Tests** (seconds) - Database operations, API endpoints
3. **End-to-End Tests** (minutes) - Complete user workflows via Selenium

### Test Coverage Requirements
- **Minimum 80% code coverage** for new features
- **100% coverage** for critical paths (picture operations, SKU generation)
- **All database triggers** must have corresponding tests
- **All AJAX endpoints** must have integration tests

### TDD-Specific Testing Patterns
```python
# Example: Testing picture visibility with TDD approach
class TestComponentPictureVisibility:
    
    def test_variant_picture_visible_immediately_after_creation(self):
        # RED: This test should fail initially
        component = create_test_component()
        variant_data = {'color_id': 1, 'pictures': [test_image]}
        
        response = client.post(f'/components/{component.id}/variants', data=variant_data)
        
        # Should be visible without page refresh
        response = client.get(f'/components/{component.id}')
        assert 'test_image' in response.data
    
    def test_ajax_refresh_loads_new_pictures(self):
        # Test the AJAX solution specifically
        pass
```

### Manual Testing Checklist (Post-TDD)
- Run automated test suite first
- Component creation with variants and pictures
- Component editing with picture changes  
- Picture visibility in component detail view
- AJAX refresh mechanism working
- No JavaScript console errors
- Cross-browser compatibility (Chrome, Firefox)

### Automated Testing (Enhanced)
- **pytest** for unit/integration tests
- **Selenium** for end-to-end workflows
- **Coverage.py** for code coverage tracking
- **Factory Boy** for test data generation
- **Mock/patch** for external dependencies (WebDAV)

## API-First Architecture Patterns (NEW - JULY 2025)

### Separation of Concerns (MANDATORY)
**CRITICAL RULE**: Clear separation between web routes and API endpoints established during variant management migration.

**📚 COMPREHENSIVE DOCUMENTATION**: See `claude_workflow/endpoint_separation_guide.md` for detailed patterns, security fixes, and code review findings.

#### Web Routes (`/app/web/`)
- **Purpose**: Page rendering and navigation only
- **Responsibilities**: Template rendering, form display, redirect logic
- **NO DATA OPERATIONS**: Forms should not process variants, pictures, or complex operations
- **Pattern**: Return rendered templates or simple redirects
- **Blueprint Naming**: Use `_web` suffix (e.g., `component_web`, `admin_web`)
- **Response Type**: ALWAYS `render_template()` or `redirect()`

```python
# Good: Web route for page rendering
@component_web.route('/components/<int:id>/edit')
def edit_component(id):
    component = Component.query.get_or_404(id)  # Simple query only
    return render_template('component_edit_form.html', component=component)

# Bad: Web route doing complex data operations (OLD PATTERN)
@component_web.route('/components', methods=['POST'])
def create_component():
    # Complex variant/picture processing - SHOULD BE IN API
    pass
```

#### API Endpoints (`/app/api/`)
- **Purpose**: Data operations and business logic
- **Responsibilities**: CRUD operations, file handling, validation, database operations
- **Return JSON**: Always return structured JSON responses
- **Proper Error Handling**: HTTP status codes and error messages
- **Blueprint Naming**: Use `_api` or `_api_bp` suffix
- **URL Pattern**: ALL routes must be under `/api` prefix
- **Response Type**: ALWAYS use `ApiResponse` utility class

```python
# Good: API endpoint for data operations
@variant_api.route('/<int:variant_id>/pictures', methods=['POST'])
def add_variant_pictures(variant_id):
    try:
        # Business logic here
        return ApiResponse.success('Pictures added', {'pictures': pictures_data})
    except ValidationError as e:
        return ApiResponse.validation_error(e.errors)
    except Exception as e:
        db.session.rollback()
        return ApiResponse.server_error()
```

### Security Requirements (CRITICAL)
- **CSRF Protection**: ALL forms must include `{{ csrf_token() }}`
- **API CSRF**: ALL AJAX requests must include `X-CSRFToken` header
- **Input Validation**: Use validator classes before database operations
- **SQL Injection Prevention**: Use SQLAlchemy queries, never string concatenation
- **File Upload Security**: Validate extensions, size, content type

### JavaScript API Integration Pattern
**MANDATORY**: Frontend must use API endpoints for real-time operations:

```javascript
// Good: API-first frontend pattern
class VariantManager {
    async createVariantViaAPI(variantId) {
        const response = await fetch('/api/variant/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify(variantData)
        });
        
        if (response.ok) {
            const result = await response.json();
            this.updateUI(result);
        } else {
            this.handleError(response);
        }
    }
}

// Bad: Form-based approach (OLD PATTERN)
function submitVariantForm() {
    // Submitting forms for real-time operations
}
```

### Smart Creation Workflow Pattern
**NEW PATTERN**: Component creation with API-based variant management:

1. **Component Creation**: Submit form to create component (web route)
2. **Extract Component ID**: From redirect URL or response
3. **Variant Creation**: Use API endpoints to create variants with pictures
4. **Real-time Updates**: No page reload needed for variant operations

```javascript
// Implementation pattern
async function handleNewComponentSubmission() {
    // 1. Create component via form submission
    const formData = new FormData(form);
    // Remove variant fields - they'll be handled via API
    removeVariantFields(formData);
    
    const response = await fetch(form.action, {
        method: 'POST',
        body: formData
    });
    
    // 2. Extract component ID from redirect
    const componentId = extractComponentId(response);
    
    // 3. Create variants via API
    await this.createVariantsViaAPI(componentId);
    
    // 4. Redirect to component detail
    window.location.href = response.url;
}
```

### File Handling with Database Integration
**CRITICAL PATTERN**: Proper WebDAV and database trigger integration:

```python
# Good: Let database generate names, then save files
@variant_api.route('/<int:variant_id>/pictures', methods=['POST'])
def add_variant_pictures(variant_id):
    try:
        # 1. Create picture records (triggers generate names)
        pictures = []
        for file in files:
            picture = Picture(
                component_id=variant.component_id,
                variant_id=variant_id,
                picture_order=order,
                # DO NOT set picture_name - database trigger handles this
            )
            db.session.add(picture)
        
        db.session.commit()  # Triggers generate picture names
        
        # 2. Save files with generated names
        for picture, file in zip(pictures, files):
            file_path = f"/components/{picture.picture_name}"
            save_uploaded_file(file, file_path)
            picture.url = f"http://31.182.67.115/webdav{file_path}"
        
        db.session.commit()
        return jsonify({'success': True, 'pictures': pictures_data})
        
    except Exception as e:
        db.session.rollback()
        # Clean up any saved files
        cleanup_saved_files(saved_files)
        return jsonify({'error': str(e)}), 500
```

### Error Handling and User Feedback
**ENHANCED PATTERN**: Professional loading states and error handling:

```javascript
// Loading states for API operations
async function performOperation() {
    try {
        this.showLoadingIndicator('Processing...');
        
        const response = await this.apiCall();
        
        if (response.ok) {
            this.showSuccessMessage('Operation completed');
            this.updateUI(response.data);
        } else {
            throw new Error(`Server error: ${response.status}`);
        }
    } catch (error) {
        this.showErrorMessage(`Operation failed: ${error.message}`);
    } finally {
        this.hideLoadingIndicator();
    }
}
```

## Modular Architecture Patterns (ESTABLISHED)

### Frontend Organization Rules
**MANDATORY**: All new features must follow modular architecture pattern established for component-detail and component-edit:

#### CSS Module Structure
```
app/static/css/<feature-name>/
├── main.css           # Entry point with @import statements
├── variables.css      # Design system variables
├── base.css           # Reset and typography
├── layout.css         # Grid and page structure
├── <feature>.css      # Feature-specific styles (variants, forms, etc.)
└── responsive.css     # Mobile and accessibility
```

#### JavaScript Module Structure  
```
app/static/js/<feature-name>/
├── <main-handler>.js  # Primary functionality (e.g., form-handler.js)
├── <feature1>.js      # Specific feature modules (e.g., variant-manager.js)
├── <feature2>.js      # Additional features (e.g., keyword-autocomplete.js)
└── utils.js           # Shared utilities (if needed)
```

### Modular Architecture Benefits
- **Maintainability**: Each file focuses on single responsibility
- **Debugging**: Issues can be traced to specific modules
- **Performance**: Better browser caching of modular files
- **Consistency**: Same patterns across all forms/pages
- **Scalability**: New features added as separate modules

### Refactoring Guidelines
When encountering large monolithic CSS/JS files:
1. **Analyze sections**: Look for natural boundaries (comments, functionality)
2. **Create module structure**: Follow established patterns
3. **Extract incrementally**: One module at a time with testing
4. **Update references**: Template files to point to new modules
5. **Delete original**: Only after verification all modules work

### Template Integration
```html
<!-- Template data initialization -->
<script>
    window.featureData = {{ template_data|tojson }};
    window.isEditMode = {{ is_edit|tojson }};
</script>

<!-- Modular CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/feature-name/main.css') }}">

<!-- Modular JavaScript -->
<script src="{{ url_for('static', filename='js/feature-name/main-handler.js') }}"></script>
<script src="{{ url_for('static', filename='js/feature-name/feature-manager.js') }}"></script>
```

## Deployment Patterns

### Common Commands
- Start: `./start.sh`
- Restart: `./restart.sh`
- Status: `./start.sh status`
- Logs: `docker-compose logs`

### Database Migrations
- Always use Flask-Migrate
- Test migrations in development first
- Backup before production migrations
- Schema: `component_app`

## Association Handling Patterns (NEW - July 2025)

### Shared Utility Functions (MANDATORY)
**Location**: `app/utils/association_handlers.py`

**Rule**: All component association handling MUST use shared utility functions to eliminate code duplication.

#### Required Functions
```python
# Handle all types of associations consistently
handle_brand_associations(component, is_edit=False)
handle_categories(component, is_edit=False) 
handle_keywords(component, is_edit=False)
handle_component_properties(component, component_type_id)
get_association_counts(component)
```

#### Usage Pattern
```python
# In both API endpoints and web routes
from app.utils.association_handlers import (
    handle_component_properties, 
    handle_brand_associations, 
    handle_categories, 
    handle_keywords
)

# Create/Edit mode handling
handle_component_properties(component, component_type_id)
handle_brand_associations(component, is_edit=is_editing)
handle_categories(component, is_edit=is_editing)
handle_keywords(component, is_edit=is_editing)
```

### Field Name Detection (CRITICAL)
**Problem**: Frontend forms may send data with varying field names
**Solution**: Check multiple field name patterns

```python
# Example: Handle both single and array field names
brand_field_names = ['brand_ids[]', 'brand_id', 'brands[]', 'brands', 'selected_brands[]']
for field_name in brand_field_names:
    values = request.form.getlist(field_name)
    if values:
        # Process found values
```

### Edit Mode Requirements
- **Brands**: Delete existing `ComponentBrand` records before adding new ones
- **Categories**: Use `component.categories.clear()` before adding new ones  
- **Keywords**: Use `component.keywords.clear()` before adding new ones
- **Properties**: Replace entire `properties` JSON object

### Database Tables Affected
- `component_app.component_brand` - Brand associations
- `component_app.component_category` - Category associations (many-to-many)
- `component_app.keyword_component` - Keyword associations  
- `component.properties` JSON field - Dynamic properties

## API Architecture Consistency Rules (NEW - July 2025)

### API-First Development (MANDATORY)
- **Creation**: Use API endpoints (`POST /api/component/create`)
- **Editing**: Use API endpoints (`PUT /api/component/<id>`) - NEEDS IMPLEMENTATION
- **Reading**: Use API endpoints (`GET /api/components/<id>/edit-data`)
- **Web Routes**: Only for page rendering and navigation

### Consistent Response Format
```python
return jsonify({
    'success': True,
    'message': 'Operation completed successfully',
    'component': {
        'id': component.id,
        'product_number': component.product_number,
        **get_association_counts(component)
    }
})
```

## 📦 Requirements.txt Management (MANDATORY)

### Package Installation Rules (CRITICAL)
1. **ALWAYS UPDATE requirements.txt** when installing new packages during development
2. **IMMEDIATE UPDATE**: Add package to requirements.txt as soon as you install it
3. **VERSION PINNING**: Always specify exact versions for production stability
4. **CATEGORIZATION**: Group packages by purpose with comments

### Required Package Categories
```txt
# Core Flask Application
Flask==2.0.1
SQLAlchemy==1.4.23
Flask-SQLAlchemy==2.5.1

# Database and Migration
psycopg2-binary==2.9.1
Flask-Migrate==3.1.0

# Forms and Security
Flask-WTF==0.15.1
email-validator==1.1.3

# File and Image Handling
Pillow==8.3.2
requests==2.31.0

# Testing Framework (MANDATORY)
pytest==8.4.1
pytest-cov==4.1.0
pytest-html==3.2.0
pytest-mock==3.11.1
selenium==4.15.0
coverage==7.3.2
pytest-json-report==1.5.0
```

### Package Installation Workflow
```bash
# 1. Install package
pip install package_name==version

# 2. IMMEDIATELY update requirements.txt
echo "package_name==version" >> requirements.txt

# 3. Test the application
python tools/run_tests.py

# 4. Commit the change
git add requirements.txt
git commit -m "Add package_name for [purpose]"
```

### Development vs Production Dependencies
- **Core Application**: All packages needed to run the app
- **Testing**: All packages needed for testing (pytest, selenium, etc.)
- **Development**: Tools for development only (if any)

### Regular Maintenance (MONTHLY)
1. **Security Updates**: Check for security vulnerabilities
2. **Version Updates**: Update to latest stable versions (with testing)
3. **Cleanup**: Remove unused dependencies
4. **Documentation**: Update comments explaining package purposes

## 📊 Testing Documentation and Reporting

### Test Report Requirements (MANDATORY)
1. **Update tests.md**: After every testing session, add entry to tests.md
2. **Chronological Order**: Newest entries at top with timestamp
3. **Comprehensive Details**: What was tested, results, issues found
4. **Action Items**: What needs to be fixed or improved

### Test Report Format
```markdown
## 📊 [DATE] - [COMPREHENSIVE TITLE]
**Timestamp**: YYYY-MM-DD HH:MM:SS  
**Tester**: [Name]  
**Session Type**: [Unit/API/Selenium/Full Suite]  

### Test Results
- **Total Tests**: [number]
- **Passed**: [number] 
- **Failed**: [number]
- **Coverage**: [percentage]

### Issues Identified
1. **[Issue Type]**: [Description]
   - **Status**: [Fixed/Pending/Investigating]
   - **Priority**: [High/Medium/Low]

### Recommendations
- [Action item 1]
- [Action item 2]

### Next Steps
- [What needs to be done next]
```