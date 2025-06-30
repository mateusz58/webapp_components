# Instructions for Claude

## Project Overview - START HERE
**Flask-based Component Management System** for manufacturing components with variants, suppliers, brands, and pictures. PostgreSQL database with `component_app` schema. Docker containerized.

## ✅ CRITICAL ISSUE RESOLVED
**Picture Loading Indicator System**: Component creation redirect now shows proper loading feedback
- **Root Cause**: Loading indicator wasn't visible during component/new → component/<id> redirect
- **Solution**: Multi-layer loading detection with CSS, Alpine.js, and URL parameters
- **Status**: RESOLVED - Loading indicator works correctly with WebDAV integration
- **Result**: Users see clear loading feedback during picture processing

## 🟡 CURRENT STATUS
**System Working Correctly**: All components functional with comprehensive loading indicators
- **WebDAV Integration**: ✅ WORKING - Images save to WebDAV and load properly
- **Loading Indicators**: ✅ WORKING - Multi-layer system provides immediate feedback
- **Auto-refresh System**: ✅ WORKING - API calls refresh image data automatically
- **URL Parameter System**: ✅ WORKING - Reliable redirect detection implemented

## Essential Architecture
- **Backend**: Flask with Blueprints (`app/web/` and `app/api/`)
- **Database**: PostgreSQL at `192.168.100.35:5432/promo_database`, schema `component_app`
- **Storage**: WebDAV at `http://31.182.67.115/webdav/components`
- **Frontend**: Bootstrap 5.3.2 + Alpine.js + Lucide icons
- **Port**: Application runs on `6002`

## Core Development Rules (MANDATORY)

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
- **Frontend**: `app/static/js/components/alpine-component-detail.js` (picture visibility)
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
- `claude_workflow/selenium_testing_guidelines.md` - Selenium E2E testing framework
- `claude_workflow/architecture_overview.md` - Full system architecture

## When to Update Workflow Files (IMPORTANT)
**REGULARLY UPDATE** these markdown files throughout development:

- **Update `project_status.md`** when:
  - Resolving critical issues or finding new ones
  - Changing project priorities
  - Completing major milestones

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

**ALWAYS use TodoWrite tool** for complex multi-step tasks

## Current Development Focus
1. **Continue feature development** - Core picture system working
2. **Follow TDD methodology** for all new development (MANDATORY)
3. **Follow selectinload patterns** for database queries
4. **Maintain CSRF protection** on all forms
5. **Use comprehensive testing** with Selenium for UI validation

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