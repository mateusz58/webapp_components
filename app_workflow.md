# Component Management System - Application Workflow

## 🎯 Core Application Understanding

This is a comprehensive Flask-based Component Management System for manufacturing components with complex lifecycle management, approval workflows, and multi-variant support.

## 📄 Main HTML Templates & User Journey

### 1. **index.html** - Dashboard & Component List
**Route**: `/` or `/components`  
**Purpose**: Main entry point and component browsing interface

**Key Features**:
- Dashboard with component statistics
- Advanced filtering and search
- Grid/List view toggle
- Bulk operations
- Pagination controls
- Real-time component status display

**User Flow**:
```
User lands here → Sees component overview → Can filter/search → Selects component to view/edit
```

**Key Includes**:
- `dashboard_header.html` - Stats and overview
- `filter_panel.html` - Advanced filtering
- `pagination_controls.html` - Navigation
- `component_grid_item.html` - Card view
- `component_list_item.html` - Table view

### 2. **component_edit_form.html** - Component Creation/Editing
**Routes**: `/component/new` (creation) or `/component/edit/<id>` (editing)  
**Purpose**: Primary form for component lifecycle management

**Key Features**:
- Comprehensive form with all component properties
- Real-time validation (AJAX product number checking)
- Multi-section layout (basic info, variants, pictures, properties)
- Success notification system
- Dynamic property fields based on component type
- Variant management with color associations
- Picture upload with drag-and-drop
- Brand and keyword association

**User Flow**:
```
Create: Dashboard → "New Component" → Fill Form → Submit → Component Detail
Edit: Dashboard → Select Component → "Edit" → Modify → Submit → Component Detail
```

**Form Sections**:
- Basic Information (product_number, description, type, supplier)
- Component Properties (dynamic based on component_type)
- Component Variants (color variations with SKU generation)
- Picture Management (upload, organize, set primary)
- Associations (brands, keywords, categories)

### 3. **component_detail.html** - Component Information Display
**Route**: `/component/<id>`  
**Purpose**: Comprehensive component view with all details and actions

**Key Features**:
- Complete component information display
- Image gallery with lightbox
- Variant showcase with pictures
- Status workflow management (Proto → SMS → PPS)
- Approval status tracking
- Action buttons (Edit, Delete, Duplicate)
- Responsive tabs for organized information
- Real-time status updates

**User Flow**:
```
Dashboard → Select Component → View Details → Can Edit/Delete/Approve → Back to Dashboard
```

**Key Sections**:
- `component_header.html` - Title, status, actions
- `variant_gallery.html` - Image gallery and variants
- `status_workflow.html` - Approval workflow
- Information tabs for properties, associations, history

## 🛣️ Application Workflow Patterns

### 1. **Component Lifecycle Workflow**
```
CREATE → PROTO REVIEW → SMS REVIEW → PPS REVIEW → APPROVED
    ↓         ↓             ↓            ↓            ↓
   New    Pending OK    Pending OK   Pending OK   Production
          Prototype     SMS Check    PPS Check     Ready
```

### 2. **Data Flow Architecture**
```
Frontend Form → Flask Route → Service Layer → Database
     ↓              ↓            ↓              ↓
 HTML/JS    component_routes  ComponentService  PostgreSQL
Templates      (Web Layer)    (Business Logic)  (component_app schema)
```

### 3. **File Upload Workflow**
```
User Upload → Validation → Temp Storage → Database Entry → WebDAV Storage → URL Generation
```

## 🔧 Key Routes & Their Functions

### Web Routes (app/web/component_routes.py)
```python
@component_web.route('/')                           # Dashboard/List
@component_web.route('/components')                 # Component list
@component_web.route('/component/<int:id>')         # Component detail
@component_web.route('/component/new')              # Create form
@component_web.route('/component/edit/<int:id>')    # Edit form
@component_web.route('/component/delete/<int:id>')  # Delete action
```

### API Routes (app/api/component_api.py)
```python
@component_api.route('/component/create')                    # Create via API
@component_api.route('/component/<int:component_id>')        # Update via API
@component_api.route('/components/search')                  # Search API
@component_api.route('/components/<int:id>/duplicate')      # Duplicate
@component_api.route('/api/component/validate-product-number') # Validation
```

### Status Management Routes
```python
@component_web.route('/component/<int:id>/status/proto')     # Proto approval
@component_web.route('/component/<int:id>/status/sms')       # SMS approval  
@component_web.route('/component/<int:id>/status/pps')       # PPS approval
```

## 🎛️ Frontend Architecture

### JavaScript Structure
```
/static/js/
├── component-edit/
│   ├── form-handler.js      # Form submission and validation
│   ├── variant-manager.js   # Variant creation and management
│   └── picture-manager.js   # Image upload and gallery
├── component-detail/
│   ├── gallery.js          # Image gallery functionality
│   ├── status-workflow.js  # Approval workflow
│   └── tabs.js            # Information tabs
└── utils/
    ├── api.js             # API communication
    └── validation.js      # Form validation helpers
```

### CSS Architecture
```
/static/css/
├── component-edit/
│   ├── main.css           # Form styling
│   ├── variants.css       # Variant management
│   └── pictures.css       # Picture upload styling
├── component-detail/
│   ├── main.css           # Detail page styling
│   ├── gallery.css        # Image gallery
│   └── workflow.css       # Status workflow
└── base/
    ├── variables.css      # CSS custom properties
    └── components.css     # Reusable components
```

## 🗄️ Database Workflow

### Core Tables & Relationships
```
component (main entity)
├── component_variant (color variations)
├── picture (images for components/variants)
├── component_brand (many-to-many associations)
├── keyword_component (tagging system)
└── Status fields (proto_status, sms_status, pps_status)
```

### Auto-Generated Fields
- **SKUs**: Automatically generated for variants using database triggers
- **Picture Names**: Auto-generated based on component/variant/supplier
- **Timestamps**: Automatic created_at/updated_at via triggers

## 🔄 Key User Workflows

### 1. **Component Creation Workflow**
```
1. User clicks "New Component" from dashboard
2. Loads component_edit_form.html
3. User fills required fields (product_number, description, type, supplier)
4. System validates product_number uniqueness via AJAX
5. User adds variants with colors
6. User uploads pictures for component/variants
7. User sets properties, brands, keywords
8. User submits form
9. System creates component with auto-generated SKUs
10. Redirects to component_detail.html
```

### 2. **Component Editing Workflow**
```
1. User selects component from dashboard
2. Loads component_detail.html
3. User clicks "Edit" button
4. Loads component_edit_form.html with existing data
5. User modifies any fields
6. System tracks changes for success notification
7. User submits changes
8. System updates component and related entities
9. Shows success notification with changed fields
10. Returns to component_detail.html
```

### 3. **Approval Workflow**
```
1. Component created with proto_status = 'pending'
2. Reviewer opens component_detail.html
3. Reviews component information and images
4. Clicks Proto status button (OK/Not OK)
5. System updates proto_status and proto_date
6. Process repeats for SMS and PPS stages
7. Component reaches production-ready status
```

## 🎨 UI/UX Patterns

### Visual Design System
- **Modern Cards**: Clean component cards with shadows and hover effects
- **Color Coding**: Status-based color system (pending, OK, not_ok)
- **Progressive Enhancement**: JavaScript enhancements over solid HTML base
- **Responsive Design**: Mobile-first approach with breakpoints
- **Loading States**: Visual feedback for async operations

### Interactive Elements
- **Alpine.js**: Reactive components for complex interactions
- **AJAX Forms**: Seamless form submissions without page refresh
- **Image Galleries**: Lightbox functionality for picture viewing
- **Drag & Drop**: Picture upload with visual feedback
- **Real-time Validation**: Immediate feedback on form inputs

## 🔍 Testing Strategy

### Test Categories
1. **Unit Tests** (`tests/unit/`) - Business logic and utilities
2. **Integration Tests** (`tests/integration/`) - Database and service integration
3. **API Tests** (`tests/api/`) - API endpoint functionality
4. **Selenium Tests** (`tests/selenium/`) - End-to-end user workflows

### Key Test Scenarios
- Component creation with all variants
- Picture upload and management
- Status workflow transitions
- Form validation (client and server-side)
- Responsive design across devices
- AJAX functionality and error handling

## 🚨 Critical Business Rules

### Component Management
- Product numbers must be unique within supplier scope
- Components require supplier and component type
- Variants automatically generate SKUs via database triggers
- Pictures are automatically named based on component/variant data

### Approval Workflow
- Components start in 'pending' proto status
- Must progress through Proto → SMS → PPS stages
- Each stage requires explicit approval
- Status changes are logged with timestamps and comments

### Data Integrity
- Soft deletes for component data preservation
- Atomic picture uploads with rollback capability
- CSRF protection on all forms
- File upload validation and security checks

## 🔧 Development Workflow

### Adding New Features
1. Update database models if needed
2. Create/modify service layer logic
3. Update API routes for backend functionality
4. Update web routes for user interface
5. Create/modify HTML templates
6. Add JavaScript for interactivity
7. Style with CSS following design system
8. Write comprehensive tests
9. Update documentation

### Quality Assurance Process
1. Unit tests must pass (100% target)
2. Integration tests for database operations
3. API tests for all endpoints
4. Selenium tests for critical user workflows
5. Manual testing across browsers/devices
6. Performance testing for large datasets
7. Security review for vulnerabilities

This workflow documentation provides the foundation for understanding how users interact with the system, how data flows through the application, and how to properly develop and test new features.