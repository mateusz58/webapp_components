# Instructions for Claude

## 🚨 FIRST STEP - READ PROJECT STATUS DASHBOARD
**Before doing any work, ALWAYS read `claude_workflow/project_status.md`** - our **Kibana-like project management dashboard** that tracks:
- **📊 Active Tasks**: Current task breakdown with status, priority, and progress metrics
- **🎯 Milestones**: Development phases and completion goals
- **🔍 Next Actions**: Immediate next steps and TODO items
- **📈 Progress Metrics**: Overall project progress and completion estimates
- **🔄 Status Updates**: Real-time development status and issue tracking
- **✅ Completed Work**: Historical record of resolved issues and achievements

**📋 PROJECT PLAN FORMAT**: This file serves as our centralized task tracking system where all development activities, progress updates, and completion statuses are logged in chronological order for full project visibility.

## Project Overview - START HERE
**Flask-based Component Management System** for manufacturing components with variants, suppliers, brands, and pictures. PostgreSQL database with `component_app` schema. Docker containerized.

## 📋 ESSENTIAL WORKFLOW DOCUMENTATION
**MUST READ**: `app_workflow.md` - Complete application workflow documentation covering:
- **🎯 Main HTML Templates**: index.html, component_edit_form.html, component_detail.html
- **🛣️ User Journey Flows**: Component creation, editing, approval workflow
- **🔧 Route Structure**: Web routes (app/web) and API routes (app/api)
- **🎨 Frontend Architecture**: JavaScript and CSS organization
- **🗄️ Database Workflow**: Table relationships and auto-generated fields
- **🔄 Business Rules**: Component lifecycle, approval stages, data integrity
- **🧪 Testing Strategy**: Unit, integration, API, and Selenium test organization

This documentation provides complete understanding of how users interact with the system and how development should be approached.

## ✅ CRITICAL ISSUES RESOLVED

### Picture Upload Workflow Fixed (January 2025)
**Component Creation Picture Upload**: API/Web communication bridge implemented
- **Root Cause**: API endpoint and web workflow were disconnected causing broken picture uploads
- **Solution**: API endpoint now integrates with web loading page workflow  
- **Status**: FULLY COMPLETE - Component creation with variants and pictures working
- **Result**: Complete workflow from form → API → loading page → verification → component detail

### Picture Loading Indicator System
**Component creation redirect now shows proper loading feedback**
- **Root Cause**: Loading indicator wasn't visible during component/new → component/<id> redirect
- **Solution**: Multi-layer loading detection with CSS, Alpine.js, and URL parameters
- **Status**: RESOLVED - Loading indicator works correctly with WebDAV integration
- **Result**: Users see clear loading feedback during picture processing

## 🟢 CURRENT STATUS - ALL SYSTEMS OPERATIONAL
**Complete Component Creation Workflow**: API/Web communication bridge working perfectly
- **Component Creation**: ✅ WORKING - Full workflow with variants and pictures
- **WebDAV Integration**: ✅ WORKING - Atomic file operations with database-generated names  
- **Loading Page System**: ✅ WORKING - Professional loading with background verification
- **Database Trigger Integration**: ✅ WORKING - Proper SKU and picture name generation
- **Error Handling**: ✅ WORKING - Atomic operations with file cleanup on failure
- **API/Web Communication**: ✅ WORKING - API sets session status and returns loading URL

## Essential Architecture
- **Backend**: Flask with Blueprints (`app/web/` and `app/api/`)
- **Database**: PostgreSQL at `192.168.100.35:5432/promo_database`, schema `component_app`
- **Storage**: WebDAV at `http://31.182.67.115/webdav/components`
- **Frontend**: Bootstrap 5.3.2 + Alpine.js + Lucide icons
- **Port**: Application runs on `6002`

## Core Development Rules (MANDATORY)

### 🧪 TESTING FRAMEWORK (CRITICAL)
**MANDATORY**: Read `claude_workflow/tests.md` for complete testing strategy

**Testing Organization**:
```
tests/
├── unit/           # Fast isolated tests (< 1s each)
├── integration/    # Database integration tests (< 5s each)  
├── api/           # API endpoint tests (< 3s each)
├── selenium/      # E2E UI tests (10-30s each)
├── services/      # Service layer tests
├── utils/         # Utility function tests
└── models/        # Database model tests
```

**CRITICAL RULE**: ❌ **NEVER CREATE TEST FILES IN ROOT DIRECTORY** ❌
- ✅ Organize tests in proper `tests/` subdirectories
- ✅ Follow naming convention: `test_[feature]_[type].py`
- ✅ Include comprehensive debug logging in all tests

**Test Execution Sequence**:
1. **Before ANY work**: `python run_tests.py fast` (MUST be 100% passing)
2. **During development**: Run relevant test category after each change
3. **Before committing**: `python run_tests.py fast` + `python run_tests.py api`

### TDD Methodology (REQUIRED)
**ALL development must follow Test-Driven Development**:
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve while keeping tests green

**No production code without failing test first**

### Database Operations
```python
# ALWAYS use selectinload for collections
component = Component.query.options(
    joinedload(Component.component_type),
    selectinload(Component.variants).joinedload(ComponentVariant.color),
    selectinload(Component.pictures)
).get_or_404(id)

# ALWAYS clear session after picture operations
db.session.expunge_all()
```

### Picture Management
- **NEVER** manually set `variant_sku` or `picture_name` - database triggers handle this
- Pictures stored in `/components/` (no subfolders)
- Naming: `{supplier_code}_{product_number}_{color}_{order}` or `{product_number}_{color}_{order}`
- **ALWAYS** implement transaction rollback for failed picture saves:
```python
saved_files = []
try:
    # save files, track paths in saved_files
    db.session.commit()
except Exception:
    for file_path in saved_files:
        if os.path.exists(file_path): os.remove(file_path)
    raise
```

### Security
- **ALL forms**: Include `{{ csrf_token() }}`
- **ALL AJAX**: Include `X-CSRFToken` header

## Key File Locations
- **Main Routes**: `app/web/component_routes.py` (component CRUD)
- **Models**: `app/models.py` (database structure)
- **Frontend (Detail)**: `app/static/js/component-detail/` (modular detail page functionality)
- **Frontend (Edit)**: `app/static/js/component-edit/` (modular edit form functionality)
- **Templates**: `app/templates/component_detail.html`, `component_edit_form.html`
- **Tests**: `tests/selenium/test_component_picture_visibility.py`

## Commands
- Start: `./start.sh`
- Restart: `./restart.sh` 
- Logs: `docker-compose logs`
- DB Migration: `docker-compose exec app flask db migrate`

## ⚠️ CRITICAL: Docker Application Restart Required
**ALWAYS restart the Docker application after making changes to:**
- **Static files** (CSS, JavaScript, images)
- **Templates** (HTML files)
- **Python code** (routes, models, services)
- **Configuration files**

**Why restart is required:**
- Application runs in Docker containers
- Static files are mounted but may be cached
- Template changes require Flask app reload
- JavaScript changes need browser cache refresh

**Command to restart:** `./restart.sh`

## Workflow System Files
Read these for deeper details when needed:
- `CLAUDE.md` - Complete architecture documentation  
- `claude_workflow/project_status.md` - Current issues and priorities
- `claude_workflow/development_rules.md` - Detailed patterns and constraints
- `claude_workflow/api_documentation.md` - **Comprehensive API endpoint documentation and specifications**
- `claude_workflow/endpoint_separation_guide.md` - API/Web separation patterns and security fixes
- `claude_workflow/database_schema_guide.md` - Complete PostgreSQL schema documentation
- `claude_workflow/selenium_testing_guidelines.md` - Selenium E2E testing framework
- `claude_workflow/architecture_overview.md` - Full system architecture
- `claude_workflow/ux_design_guidelines.md` - **Daily user perspective UX design standards and testing methodology**

## When to Update Workflow Files (IMPORTANT)
**REGULARLY UPDATE** these markdown files throughout development:

- **Update `project_status.md`** (Kibana-like Dashboard) when:
  - **Starting new tasks**: Add to task dashboard with status and priority
  - **Task progress updates**: Update progress percentages and status
  - **Task completion**: Mark as COMPLETED and update metrics
  - **New issues discovered**: Log as new tasks with appropriate priority
  - **Milestone achievements**: Update milestone completion status
  - **Priority changes**: Adjust task priorities and next actions
  - **Daily progress**: Update overall progress metrics and estimates
  - **Status changes**: Modify active development status and focus areas

- **Update `development_rules.md`** when:
  - Establishing new coding patterns
  - Adding new constraints or requirements
  - Learning from debugging sessions

- **Update `selenium_testing_guidelines.md`** when:
  - Adding new test patterns
  - Finding better testing approaches
  - Solving testing challenges

- **Update this file (`instructions_for_claude.md`)** when:
  - Critical issues change
  - Architecture evolves
  - New essential information emerges

- **Update `database_schema_guide.md`** when:
  - Database schema changes occur
  - New tables or relationships added
  - Triggers or functions modified
  - Performance issues with queries identified

- **Update `api_documentation.md`** when:
  - Adding new API endpoints
  - Modifying existing endpoint behavior
  - Changing request/response formats
  - Adding new error codes or status codes
  - Updating authentication or security requirements
  - API architecture improvements or fixes

- **Update `ux_design_guidelines.md`** when:
  - Making layout or design changes to component pages
  - Implementing new responsive design patterns
  - Running UX testing and discovering new optimization opportunities
  - Establishing new design standards or components
  - Changing CSS architecture or design systems
  - User feedback reveals new daily-use requirements

**ALWAYS use TodoWrite tool** for complex multi-step tasks

## Database Documentation Responsibilities (MANDATORY)

**Database Connection**: `postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database`  
**Schema**: `component_app`

### Regular Database Documentation Tasks:
1. **Monitor Schema Changes**: Check for new tables, columns, or relationships
2. **Document Triggers**: Keep track of PostgreSQL functions and triggers
3. **Update Relationships**: Maintain accurate relationship documentation
4. **Performance Analysis**: Document query performance issues and solutions
5. **Data Flow Documentation**: Keep picture upload and SKU generation workflows current

### Critical Database Rules:
- **Never manually set**: `variant_sku` or `picture_name` (auto-generated by triggers)
- **Always use schema**: All models inherit from Base class with `component_app` schema
- **Picture management**: Files stored in WebDAV at `/components/` with auto-generated names
- **Unique constraints**: Respect `product_number + supplier_id` and `component_id + color_id` uniqueness
- **Status workflow**: Components have three-tier approval (Proto → SMS → PPS)

## 🎯 CURRENT WORK PRIORITIES & TASK TRACKING

**MANDATORY**: Always check `claude_workflow/project_status.md` for current task dashboard and priorities.

### 📊 Project Dashboard Maintenance (CRITICAL)
**ALWAYS update the project_status.md dashboard**:
1. **Before starting work**: Check current task status and next actions
2. **During development**: Update task progress and status regularly
3. **After completing tasks**: Mark as COMPLETED and update metrics
4. **When blocked**: Log issues and adjust priorities
5. **Daily updates**: Maintain progress metrics and completion estimates

**Dashboard Format**: Kibana-style tracking with task IDs, status, priority, progress percentages, and milestone tracking for complete project visibility.

The project status file contains:
- 🔴 Active critical issues requiring immediate attention
- 🟡 Current development tasks and priorities  
- ✅ Recently completed work and achievements
- 📊 Performance metrics and system status
- 🔧 Debugging information and analysis

**Before starting any work, read project_status.md to understand what needs to be done.**

## ⚡ CRITICAL COMPONENT CREATION WORKFLOW (WORKING)

### Complete Flow:
1. **Form Submit** → JavaScript prevents default → Calls `/api/component/create`
2. **API Processing** → Creates component + variants + pictures with atomic operations
3. **Session Setup** → API sets `component_creation_{id}` session status = 'verifying' 
4. **Verification Start** → API starts background thread with `_verify_images_accessible()`
5. **API Response** → Returns `redirect_url` to loading page
6. **JavaScript Redirect** → Navigates to `component_creation_loading.html`
7. **Loading Page** → Polls `/api/component/creation-status/<id>` every 2 seconds
8. **Verification Complete** → Session status changes to 'ready'
9. **Final Redirect** → Loading page redirects to `component/<id>` detail view

### Key Implementation:
- **Endpoint**: `/api/component/create` (handles complete creation)
- **Form Fields**: `variant_color_{id}`, `variant_images_{id}[]` (generated by JavaScript)
- **File Operations**: Atomic - database first, then files with cleanup on failure
- **WebDAV Names**: Uses database-generated names like `supplier_product_color_1.jpg`

## API-First Development Rules (NEW - JULY 2025)
**MANDATORY for all new features**: Follow the established separation of concerns:

**📋 REFERENCE**: See `claude_workflow/api_documentation.md` for complete API specifications, endpoints, and architectural guidelines.

### Web Routes (`/app/web/`)
- **Purpose**: Page rendering and navigation only
- **DO**: Return templates, handle redirects, display forms
- **DON'T**: Process complex data, handle file uploads, manage variants/pictures

### API Endpoints (`/app/api/`)
- **Purpose**: Data operations and business logic
- **DO**: CRUD operations, file handling, validation, JSON responses
- **DON'T**: Render templates or handle navigation

### Frontend Integration
- **Real-time Operations**: Use API endpoints with JavaScript for immediate feedback
- **Form Submissions**: Web routes for component creation, API for variant management
- **Error Handling**: Professional loading states and graceful error recovery

## Picture Loading System Status
- **Multi-Layer Loading Detection**: ✅ CSS + Alpine.js + URL parameters
- **Auto-refresh API**: ✅ `/api/components/<id>/variants` endpoint working
- **URL Parameter Passing**: ✅ `loading=true` parameter in redirects
- **Loading Indicator Visibility**: ✅ Prominent spinner with progress messages
- **Selenium Testing**: ✅ Comprehensive test suite validates functionality
- **WebDAV Integration**: ✅ Images save and load from WebDAV correctly
- **Race Condition Handling**: ✅ Multiple fallback mechanisms implemented

## Loading System Architecture
- **Layer 1**: Immediate CSS loading (`body[data-initial-loading="true"]`)
- **Layer 2**: Alpine.js component factory loading state
- **Layer 3**: Auto-refresh with exponential backoff
- **Layer 4**: Manual refresh button for user control

You now have sufficient context to start working. Read additional workflow files only when you need deeper details about specific areas.