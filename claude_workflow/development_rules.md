# Development Rules

**Last Updated**: July 9, 2025

## Core Development Rules

### 1. Code Quality Standards
- **NO COMMENTS IN PYTHON FILES**: Never add comments, docstrings, or explanatory text to .py files
- **External Documentation Only**: Use markdown files in claude_workflow/ for all documentation
- **Clean Code**: Code should be self-explanatory without comments
- **Database Documentation**: Maintain separate database schema documentation

### 2. MVC Architecture (MANDATORY)
**CRITICAL REQUIREMENT**: This project MUST follow strict Model-View-Controller architecture with Service Layer separation.

#### Model Layer (`app/models.py`)
- **Purpose**: Database entities and basic data operations only
- **Responsibilities**: SQLAlchemy models, relationships, simple property getters/setters
- **NO BUSINESS LOGIC**: Models should only contain data structure and basic validation
- **NO service calls**: Models should not call services or other models

#### View Layer (`app/templates/`, `app/static/`)
- **Purpose**: User interface presentation only  
- **Templates**: Data display, form rendering, user interaction
- **JavaScript**: UI interactions, API calls, DOM manipulation
- **CSS**: Styling and visual presentation
- **NO BUSINESS LOGIC**: Views should only handle presentation

#### Controller Layer (`app/web/`, `app/api/`)
- **Purpose**: Request/response handling and routing only
- **Web Routes**: Render templates, handle navigation, simple redirects
- **API Routes**: Handle HTTP requests, delegate to service layer, return JSON
- **NO BUSINESS LOGIC**: Controllers should delegate all business logic to service layer

#### Service Layer (`app/services/`) - **MANDATORY**
- **Purpose**: Business logic, data processing, orchestration
- **Responsibilities**: Component CRUD operations, validation, association management
- **Transaction Management**: Database commits, rollbacks, error handling
- **Cross-cutting Concerns**: Logging, error handling, data transformation

### 3. Database Operations
- **ALWAYS** use database triggers for SKU and picture name generation
- **NEVER** manually set `variant_sku` or `picture_name` fields
- Use `selectinload` for better performance with collections
- All models inherit from `Base` class with `component_app` schema
- Clear session cache with `db.session.expunge_all()` after picture operations

### 4. Picture Management Rules
- Pictures stored in `/components/` directory (no subfolders)
- Automatic naming: `{supplier_code}_{product_number}_{color}_{order}` or `{product_number}_{color}_{order}`
- WebDAV URL prefix: `http://31.182.67.115/webdav/components`
- Image optimization: max 1920x1920, JPEG quality 85
- Always implement transaction rollback for failed saves

### 5. CSRF Protection (MANDATORY)
- All forms must include `{{ csrf_token() }}`
- AJAX requests must include `X-CSRFToken` header
- API endpoints must validate CSRF tokens

### 6. Error Handling Architecture
- **Models**: Raise `ValueError` for data validation errors
- **Services**: Catch model errors, add business context, log errors, re-raise with context
- **Controllers**: Catch service errors, convert to appropriate HTTP responses
- **Views**: Display user-friendly error messages from controller responses

### 7. Performance Requirements
- Use selectinload for collections
- Implement query optimization
- Cache expensive operations
- Monitor database query performance

### 8. Security Requirements
- CSRF protection on all forms
- File upload validation
- SQL injection prevention via SQLAlchemy
- Secure file handling practices

## Backend Implementation Standards

### 1. Service Layer Requirements
- **EVERY** complex operation must have a corresponding service class
- Services handle: CRUD operations, validation, business rules, transaction management
- Services are **stateless** - no instance variables for business data
- Services use **static methods** for operations or dependency injection pattern

### 2. API-First Architecture
- **Web Routes**: Page rendering and navigation only
- **API Endpoints**: Data operations and business logic
- **URL Pattern**: ALL API routes must be under `/api` prefix
- **Response Type**: Always use `ApiResponse` utility class for APIs

### 3. Database Query Pattern
```python
# ALWAYS use selectinload for collections
component = Component.query.options(
    joinedload(Component.component_type),
    selectinload(Component.variants).joinedload(ComponentVariant.color),
    selectinload(Component.pictures)
).get_or_404(id)
```

### 4. Atomic File Operations Pattern
```python
# CRITICAL: Database operations BEFORE file operations
try:
    # 1. Database operations first
    db.session.commit()  # Commit database first
    
    # 2. File operations second  
    for file_info in all_pending_files:
        file_path = save_file_with_db_name(file_info)
        saved_files.append(file_path)
    
    db.session.commit()  # Commit URL updates
    
except Exception:
    # Clean up any saved files on failure
    for file_path in saved_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.rollback()
    raise
```

### 5. Association Handling Pattern
- **Location**: `app/utils/association_handlers.py`
- **Rule**: All component association handling MUST use shared utility functions
- **Usage**: `handle_brand_associations()`, `handle_categories()`, `handle_keywords()`

### 6. Logging Requirements
- **COMPREHENSIVE LOGGING**: Always add detailed logging for complex operations
- **LOG CRITICAL PATHS**: File operations, database operations, API calls must be logged
- **LOG VARIABLES**: Log important variable values (IDs, file names, counts, status)
- **LOG ERRORS**: Every exception must be logged with context

## Frontend Implementation Standards

### 1. UX Design Guidelines for Manufacturing

#### Core Design Philosophy: Manufacturing Workflow Efficiency
This application serves **manufacturing professionals** who:
- Work 8+ hours daily in the system
- Need rapid access to component specifications and images
- Switch between components frequently during their workflow
- Work under time pressure with production deadlines
- Require clear visual confirmation of component details

#### Two-Column Layout Standard (MANDATORY)
```css
.component-content-grid {
  display: grid;
  grid-template-columns: 1fr 480px;  /* NEVER change this ratio */
  gap: var(--cd-space-lg);
  align-items: start;
}
```
**Rule**: All component detail pages MUST use this layout. Never revert to single-column.

#### Image Gallery Requirements
```css
.component-content__gallery {
  position: sticky;        /* ALWAYS sticky */
  top: var(--cd-space-lg); /* ALWAYS maintain top offset */
  max-height: 90vh;        /* Prevent excessive height */
}

.main-image-container {
  aspect-ratio: 1 / 1;     /* ALWAYS square aspect ratio */
  max-width: 450px;        /* NEVER exceed this width */
}
```
**Rule**: Images must remain visible while user browses information. Critical for manufacturing workflow.

#### Information Panel Constraints
```css
.component-content__info {
  max-height: calc(100vh - 140px);  /* ALWAYS constrain height */
  overflow-y: auto;                 /* ALWAYS allow scrolling within panel */
}

.tab-content-modern {
  max-height: calc(100vh - 400px);  /* ALWAYS prevent tab content overflow */
  overflow-y: auto;
}
```
**Rule**: Never allow information to expand beyond viewport. Scrolling must be contained.

#### Responsive Design Requirements
```css
/* Desktop Standard - NEVER remove this */
@media (max-width: 1400px) {
  .component-content-grid {
    grid-template-columns: 1fr 420px;
  }
}

/* Laptop - MUST collapse to single column */
@media (max-width: 1200px) {
  .component-content-grid {
    grid-template-columns: 1fr;
  }
  .component-content__gallery {
    position: relative;  /* Remove sticky on small screens */
    max-height: 400px;
  }
}
```

#### Manufacturing-Specific Component Standards
- **Brand Information**: Always include brand tab with name, ID, association date
- **Status Indicators**: Use color-coded status badges for approval workflow
- **Information Hierarchy**: Product number + status (header), Images (left), Details (right)

#### Critical "Do NOT" Rules for Manufacturing UX
1. **NEVER** revert to single-column layout on desktop resolutions
2. **NEVER** remove sticky positioning from image gallery
3. **NEVER** increase font sizes above specified scale
4. **NEVER** add excessive spacing that pushes content below fold
5. **NEVER** hide status information or make it secondary
6. **NEVER** remove color coding from status indicators
7. **NEVER** allow horizontal scrolling on any screen size
8. **NEVER** prioritize aesthetics over manufacturing workflow efficiency

### 2. Modular Architecture
**MANDATORY**: All new features must follow modular architecture pattern:

#### CSS Module Structure
```
app/static/css/<feature-name>/
├── main.css           # Entry point with @import statements
├── variables.css      # Design system variables
├── base.css           # Reset and typography
├── layout.css         # Grid and page structure
├── <feature>.css      # Feature-specific styles
└── responsive.css     # Mobile and accessibility
```

#### JavaScript Module Structure  
```
app/static/js/<feature-name>/
├── <main-handler>.js  # Primary functionality
├── <feature1>.js      # Specific feature modules
├── <feature2>.js      # Additional features
└── utils.js           # Shared utilities
```

### 2. JavaScript API Integration Pattern
```javascript
// MANDATORY: Frontend must use API endpoints
class FeatureManager {
    async performAction(data) {
        const response = await fetch('/api/endpoint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            this.updateUI(result);
        } else {
            this.handleError(response);
        }
    }
}
```

### 3. Error Handling and User Feedback
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

### 4. Template Integration
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
```

## Deployment Rules

### 1. Common Commands
- Start: `./start.sh`
- Restart: `./restart.sh`
- Status: `./start.sh status`
- Logs: `docker-compose logs`

### 2. Database Migrations
- Always use Flask-Migrate
- Test migrations in development first
- Backup before production migrations
- Schema: `component_app`

### 3. Requirements.txt Management
- **ALWAYS UPDATE requirements.txt** when installing new packages
- **IMMEDIATE UPDATE**: Add package to requirements.txt as soon as you install it
- **VERSION PINNING**: Always specify exact versions for production stability
- **CATEGORIZATION**: Group packages by purpose with comments

## Component Management Rules

### 1. Component Variant Rules
- Each component must have at least one variant
- Each variant must have at least one picture
- Colors are unique per component
- SKUs auto-generated by database triggers

### 2. File Upload Workflow
1. Files read into memory during form processing
2. Database records created first (triggers generate names)
3. Files saved to disk with generated names
4. URLs updated in database
5. Session cache cleared with `db.session.expunge_all()`

### 3. Areas of Caution
- **Session Caching Issues**: Use `db.session.expunge_all()` after picture operations
- **File Operations**: Always use atomic operations for file saving
- **Database Triggers**: Never bypass database-generated fields

## Development Workflow

### 1. Before Development
- Run full test suite: `python tools/run_tests.py`
- Fix any failing tests before proceeding
- Check project status in `project_status.md`

### 2. During Development
- Follow TDD methodology (Red-Green-Refactor)
- Use comprehensive logging
- Test frequently during development
- Update documentation as needed

### 3. After Development
- Run full test suite again
- Update test reports
- Update project status
- Only commit when all tests pass