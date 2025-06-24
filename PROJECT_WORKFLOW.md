# Project Workflow Documentation

This document contains comprehensive workflow documentation for all major features in the Component Management System.

---

## Table of Contents
1. [Picture Visibility Issue Resolution](#picture-visibility-issue-resolution) *(UPDATED)*
2. [Testing Framework Workflow](#testing-framework-workflow) 
3. [Component Variants Workflow](#component-variants-workflow)
4. [Component Creation Workflow](#component-creation-workflow) *(To be added)*
5. [Brand Management Workflow](#brand-management-workflow) *(To be added)*
6. [Picture Management Workflow](#picture-management-workflow) *(To be added)*

---

## Picture Visibility Issue Resolution

### Current Implementation Status
**Issue**: Pictures don't appear immediately on component detail page after create/edit redirect.
**Status**: AJAX refresh solution implemented - awaiting validation.

### 1. Problem Analysis

#### 1.1 Root Cause
- SQLAlchemy session caching prevents fresh variant picture data loading
- Template renders with stale data before session refresh occurs
- Backend session clearing insufficient for immediate resolution

#### 1.2 Failed Solutions
1. **Backend Session Clearing**: `db.session.expunge_all()` + explicit refresh loops
2. **Query Optimization**: Enhanced `joinedload` for variant pictures
3. **Debug Logging**: Confirmed pictures save correctly but don't load immediately

### 2. AJAX Refresh Solution (Current Implementation)

#### 2.1 Architecture
```
Component Detail Page Load
├── Template renders with initial data (potentially stale)
├── JavaScript executes multiple refresh attempts:
│   ├── 500ms: First attempt
│   ├── 1.5s: Second attempt  
│   └── 3s: Final fallback
├── AJAX calls /api/components/<id>/variants
├── Fresh data updates Alpine.js reactively
└── Pictures appear without manual refresh
```

#### 2.2 Implementation Files
```
app/api/component_api.py (lines 395-465)
├── @component_api.route('/components/<int:component_id>/variants')
├── db.session.expunge_all() for fresh data
├── Explicit variant/picture refresh loops
└── JSON response with complete variant data

app/static/js/pages/component_detail.js
├── ComponentDetailManager class
├── Multiple refresh attempts with timing
├── Alpine.js data updates
└── Console logging for debugging

app/templates/component_detail.html (line 1189)
└── Script inclusion for component detail pages
```

#### 2.3 Key Features
- **Aggressive Refresh**: Multiple attempts ensure data loading
- **Alpine.js Integration**: Updates component data reactively
- **Error Handling**: Retry logic with exponential backoff
- **Debugging**: Console logs for troubleshooting

### 3. Testing and Validation

#### 3.1 Selenium Test Framework
```
tests/selenium/
├── test_component_picture_visibility.py (Main test)
├── test_ajax_endpoint.py (API validation)
├── pages/ (Page Object Model)
├── utils/ (Driver management, image generation)
└── config/ (Test configuration)
```

#### 3.2 Manual Testing Process
1. **Create Component**: Use `/component/new` with variants + pictures
2. **Monitor Console**: Check browser developer tools for JavaScript logs
3. **Observe Behavior**: Verify pictures appear without manual refresh
4. **Timing Analysis**: Note if multiple attempts needed

#### 3.3 Expected Behavior
- Pictures should appear within 3 seconds of page load
- Console should show "Refreshing variant data..." messages
- No manual refresh required
- Variant switching should work immediately

### 4. Next Steps if Issue Persists

#### 4.1 Alternative Approaches
1. **Client-Side Image Loading**: Pre-load images via JavaScript
2. **Template-Level Fix**: Enhanced server-side session handling
3. **Caching Strategy**: Implement Redis for session data
4. **Database Optimization**: Review PostgreSQL transaction isolation

#### 4.2 Debugging Steps
1. Monitor browser Network tab for API calls
2. Check application logs: `docker-compose logs`
3. Verify AJAX endpoint response: `curl http://localhost:6002/api/components/<id>/variants`
4. Test timing adjustments in JavaScript

---

## Testing Framework Workflow

### Overview
Comprehensive Selenium-based testing framework for automated component creation and picture visibility testing. Built to reproduce and verify fixes for the critical picture display issue.

### 1. Test Framework Structure

#### 1.1 Modular Architecture
```
modular_component_test.py
├── ComponentFormModule (Base class)
├── EssentialInformationModule
├── KeywordsModule  
├── ImageGeneratorModule
├── VariantsModule
├── FormSubmissionModule
├── PictureTestModule
└── ModularComponentTest (Main orchestrator)
```

#### 1.2 Key Features
- **Modular Design**: Each form section handled by separate module
- **Image Generation**: Automatically creates colored test images
- **Complete Form Filling**: Handles all required fields
- **Evidence Collection**: Screenshots at each step
- **Issue Reproduction**: Tests immediate vs post-refresh picture visibility

### 2. Test Execution Flow

#### 2.1 Setup Phase
1. Initialize Chrome/Chromium driver
2. Navigate to component creation form
3. Generate test images for variants

#### 2.2 Form Filling Phase
1. **Essential Information**: Product number, description, component type, supplier
2. **Keywords**: Add relevant search keywords  
3. **Variants**: Add color variants with generated pictures
4. **Validation**: Ensure all required fields completed

#### 2.3 Submission and Testing Phase
1. Submit form and capture redirect URL
2. **Immediate Test**: Check picture visibility right after redirect
3. **Post-Refresh Test**: Refresh page and check picture visibility again
4. **Comparison**: Identify if pictures only appear after refresh

#### 2.4 Results Analysis
- ✅ **PASS**: Pictures visible immediately after redirect
- ❌ **FAIL**: Pictures only visible after manual refresh (confirms bug)
- ⚠️ **WARNING**: No pictures found even after refresh

### 3. Usage Instructions

#### 3.1 Prerequisites
```bash
# Install dependencies
pip3 install selenium pillow

# Ensure Chrome/Chromium and ChromeDriver installed
sudo apt install chromium-browser chromium-chromedriver
```

#### 3.2 Running Tests
```bash
# Start application
./start.sh start

# Run comprehensive test
python3 modular_component_test.py

# Check results
ls /tmp/*screenshot*  # View evidence screenshots
```

#### 3.3 Test Configuration
```python
# Customize test variants
test_variants = [
    {'color': 'Red'},
    {'color': 'Blue'},
    {'color': 'Green'}
]

# Run with custom variants
test.run_full_test(test_variants)
```

### 4. Evidence Collection

#### 4.1 Screenshots Captured
- `01_main_page_*.png` - Application homepage
- `02_form_loaded_*.png` - Component creation form
- `03_basic_info_filled_*.png` - After filling essential information
- `04_variant_*_added_*.png` - After adding each variant
- `05_before_submit_*.png` - Form ready for submission
- `immediate_after_redirect_*.png` - Detail page immediately after redirect
- `after_manual_refresh_*.png` - Detail page after manual refresh

#### 4.2 Debug Information
- Detailed logging of each step
- Picture URL detection and counting
- Form validation status tracking
- Browser interaction timing

### 5. Extension Points

#### 5.1 Adding New Test Modules
```python
class NewFormSectionModule(ComponentFormModule):
    def fill_section(self, data):
        # Implementation for new form section
        pass
```

#### 5.2 Custom Test Scenarios
```python
# Add to ModularComponentTest
def run_edge_case_test(self):
    # Custom test scenario implementation
    pass
```

### 6. Troubleshooting

#### 6.1 Common Issues
- **File Upload Fails**: Check image generation and file paths
- **Form Validation Errors**: Ensure all required fields filled
- **Browser Issues**: Verify Chrome/Chromium installation
- **Network Issues**: Check application accessibility

#### 6.2 Debug Options
```python
# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

# Keep browser open longer for manual inspection
time.sleep(60)  # Increase inspection time
```

---

## Component Variants Workflow

### Overview
The Component Variants system allows users to create and manage color variants of components with associated pictures. Each variant represents a different color option of the same component and can have multiple pictures.

### 1. Frontend Structure

#### 1.1 Main Components
- **Main Form**: `/app/templates/component_edit_form.html`
- **Variants Section**: `/app/templates/sections/component_variants.html`
- **JavaScript Manager**: `/app/static/js/modules/variant_manager.js`

#### 1.2 UI Elements
- **Add Variant Button**: Triggers creation of new variant form
- **Variant Cards**: Each variant displayed as a card with:
  - Color selection dropdown
  - SKU display (read-only, auto-generated)
  - Picture miniatures preview
  - Manage Pictures button
  - Remove variant button

### 2. Variant Creation Flow

#### 2.1 Add New Variant
1. User clicks "Add Variant" button
2. JavaScript creates new variant card with temporary ID (`new_1`, `new_2`, etc.)
3. Card includes:
   - Color dropdown with available colors
   - Option to add custom color
   - SKU field (shows preview, not saved until form submission)
   - Empty picture section

#### 2.2 Color Selection
1. **Available Colors**: System shows only colors not already used by other variants
2. **Custom Color**: User can select "+ Add New Color" option
   - Shows text input for new color name
   - Creates new color in database on form submission
3. **Duplicate Prevention**: JavaScript prevents selecting same color twice

#### 2.3 SKU Generation
- **Display**: SKU field is read-only, shows current database value
- **Preview**: When color changes, JavaScript shows preview of new SKU
- **Pattern**: `{supplier_code}_{product_number}_{color_name}` (all lowercase, spaces → underscores)
- **Database Trigger**: Actual SKU generated by PostgreSQL function on save

### 3. Picture Management Workflow

#### 3.1 Picture Upload Methods
1. **Click to Upload**: Click on drop zone or "Add Pictures" button
2. **Drag & Drop**: Drag image files onto drop zone
3. **Multiple Files**: Can select/drop multiple images at once

#### 3.2 Picture Display
- **Miniatures View**: Shows up to 4 thumbnail images
  - Click miniatures to open full picture management
  - Shows count if more than 4 pictures
- **Full View**: Expandable section with:
  - Upload drop zone
  - Grid of all pictures
  - Picture management controls

#### 3.3 Picture Actions
- **Set Primary**: Star button marks picture as primary
- **Remove**: X button removes picture
- **Preview**: Click image to open full-size preview
- **Alt Text**: Each picture has editable alt text field

### 4. Form Submission Process

#### 4.1 Client-Side Validation (Real-time + Pre-submit)

**Real-time Visual Feedback:**
- **Color Selection**: Red border if no color selected
- **Picture Requirements**: Red border on pictures header if no pictures
- **Variant Status**: 
  - Green border: Complete variant (color + pictures)
  - Yellow border: Incomplete variant (missing color or pictures)
  - Red border: Empty variant
- **Submit Button**: 
  - Disabled if no valid variants
  - Warning style if some variants incomplete
  - Primary style when all variants valid

**Pre-submit Validation:**
```javascript
// validateComponentVariants() checks:
- Component must have at least one variant
- Each variant must have a color selected
- Each variant must have at least one picture
- Custom color names must be provided when selected
```

**User Guidance:**
- Clear validation rules displayed above variants section
- Real-time feedback prevents invalid submissions
- Descriptive error messages for each validation rule

#### 4.2 Data Collection
1. **Existing Variants**: 
   - `variant_color_{id}`: Selected color ID
   - `variant_custom_color_{id}`: Custom color name (if applicable)
   - `variant_images_{id}[]`: New picture files
   - `existing_pictures`: IDs of kept pictures

2. **New Variants**:
   - `variant_color_new_{n}`: Selected color ID
   - `variant_custom_color_new_{n}`: Custom color name
   - `variant_images_new_{n}[]`: Picture files

#### 4.3 Server-Side Processing (Correct Implementation)
1. **Phase 1 - Data Processing** (`_handle_variants`):
   - Process variant data (colors, custom colors)
   - Create Picture records with empty URLs
   - Store file data in memory (not saved to disk yet)
   - Return list of pending pictures

2. **Phase 2 - Database Commit**:
   - Triggers fire to generate:
     - `variant_sku` via `generate_variant_sku()`
     - `picture_name` via `generate_picture_name()`

3. **Phase 3 - File Saving** (`_save_pending_pictures`):
   - Read database-generated picture names
   - Save files directly to final location with proper names
   - Update Picture URLs to WebDAV paths
   - No temporary files or renaming needed

#### 4.4 Edit Mode Special Handling
**When editing components, additional processing handles:**

1. **Product Number Changes**:
   - Database triggers regenerate ALL picture names
   - `_handle_picture_renames()` renames all files on disk
   - Updates all Picture URLs in database

2. **Supplier Changes**:
   - Database triggers regenerate ALL picture names  
   - Files renamed to include new supplier code
   - All Picture URLs updated

3. **Variant Color Changes**:
   - Database triggers regenerate variant picture names
   - Variant SKU regenerated with new color
   - Variant picture files renamed on disk

4. **Picture Deletions**:
   - Component pictures: handled via `delete_pictures[]` form field
   - Variant pictures: handled via `existing_pictures` exclusion
   - Files deleted from `/components/` directory
   - Database records removed

### 5. Database Operations

#### 5.1 Tables Involved
- `component_variant`: Stores variant data
- `color`: Color reference table
- `picture`: Stores picture metadata
- Database triggers handle:
  - SKU generation (`trigger_update_variant_sku`)
  - Picture naming (`trigger_update_picture_name`)
  - Timestamp updates

#### 5.2 SKU Generation Function
```sql
generate_variant_sku(component_id, color_id)
- Gets supplier code from component
- Gets product number from component
- Gets color name from color table
- Formats: lowercase, spaces → underscores
- Returns: supplier_code_product_number_color_name
```

#### 5.3 Picture Storage (Correct Implementation)
- **Before Submit**: Files stored in browser memory only
- **On Submit**: Files saved directly to final location
- **WebDAV Mount**: `/components/` maps to `http://31.182.67.115/webdav/components/`
- **Storage Location**: ALL pictures saved directly in `/components/` (no subfolders)
- **Picture Name**: Auto-generated by database trigger
- **Pattern**: `{supplier_code}_{product_number}_{color_name}_{order}`
- **Final Path**: `/components/{picture_name}.{ext}`
- **URLs**: `http://31.182.67.115/webdav/components/{picture_name}.{ext}`

### 6. Database Query Issues & Fixes

#### 6.1 Component Detail View Fix (RESOLVED)
**Issue**: After creating/editing components, pictures weren't showing on component detail page until refresh.

**Root Cause**: The `component_detail` function query was missing `joinedload(ComponentVariant.variant_pictures)`.

**Fix**: Updated query to include:
```python
component = Component.query.options(
    joinedload(Component.component_type),
    joinedload(Component.supplier),
    joinedload(Component.pictures),
    joinedload(Component.variants).joinedload(ComponentVariant.color),
    joinedload(Component.variants).joinedload(ComponentVariant.variant_pictures),  # ← ADDED
    joinedload(Component.keywords)
).get_or_404(id)
```

**Status**: PARTIALLY RESOLVED - Query fixed but pictures still not showing on detail page after redirect.

#### 6.2 Frontend Validation Enhancement (RESOLVED)
**Issue**: Users could submit forms without variants, causing backend errors and hanging submit buttons.

**Root Cause**: Frontend validation was only checked on form submission, not in real-time.

**Fix**: Enhanced real-time validation system:
```javascript
updateSubmitButtonState() {
    // Real-time checking of variants and validation state
    // Disables submit button when requirements not met
    // Shows clear validation status with detailed feedback
}
```

**Features Added**:
- **Submit Button States**: Disabled (red) when invalid, enabled (green) when valid
- **Dynamic Button Text**: Shows specific action needed ("Add at least one variant", "Fix validation errors")
- **Validation Status Panel**: Real-time feedback showing exact issues
- **Color-coded Indicators**: Warning (yellow) for issues, success (green) when ready

**Result**: Submit button is always disabled until all validation requirements are met, preventing form submission errors.

#### 6.3 Component Detail Picture Loading (ONGOING ISSUE)
**Issue**: After creating/editing components with pictures, when redirected to `http://localhost:6002/component/<id>`, pictures don't show until page refresh.

**Investigation Done**:
1. **Query Fix**: Added `joinedload(ComponentVariant.variant_pictures)` to component_detail query ✅
2. **Session Management**: Tried various session management approaches
3. **Transaction Issues**: Enhanced commit/flush/expunge patterns
4. **URL Generation**: Added debugging to verify picture URLs are set correctly
5. **File Storage**: Pictures are saved to `/components/` with correct names

**Current Status**: 
- Frontend validation works perfectly ✅
- Picture files are saved correctly ✅  
- Database records created with proper URLs ✅
- Query loads variant pictures correctly ✅
- **BUT**: Pictures still don't appear on detail page immediately after redirect ❌

**Next Steps Needed**:
- Check if URLs in database match actual saved files
- Verify WebDAV URL accessibility
- Investigate template rendering of variant pictures
- Check browser network requests for failed image loads

### 7. API Endpoints

#### 7.1 Variant API (`/api/variant/`)
- `POST /<id>/pictures`: Add pictures to variant
- `DELETE /<id>/pictures/<pic_id>`: Remove picture
- `POST /<id>/pictures/<pic_id>/primary`: Set primary picture
- `GET /colors/available/<component_id>`: Get available colors

#### 7.2 Response Handling
- Success: Updates UI without page reload
- Error: Shows alert with error message
- Picture uploads tracked in memory until form submission

### 8. Change Tracking

#### 8.1 Change Summary Modal
- Shows before submission for existing components
- Lists all changes:
  - Variant additions/removals
  - Color changes
  - Picture additions/removals
- User must confirm before saving

#### 8.2 Validation Summary
- Shows at top of form if validation fails
- Lists all errors that need correction
- Scrolls to first error field

### 9. Special Features

#### 9.1 Drag & Drop
- Visual feedback on drag over
- Supports multiple file drops
- Validates file types (PNG, JPG, JPEG, WEBP)
- 16MB file size limit

#### 9.2 Real-time Updates
- Picture count updates immediately
- Miniature previews refresh on changes
- SKU preview shows expected value
- Available colors update as selections made

#### 9.3 Performance Optimizations
- Lazy loading of variant pictures
- Miniature generation for quick preview
- Batch file uploads
- Efficient database queries with joins

### 10. Error Handling

#### 10.1 Client-Side
- File type validation
- File size validation
- Duplicate color prevention
- Required field validation

#### 10.2 Server-Side
- Database constraint violations
- File upload failures
- Transaction rollback on errors
- Detailed error logging

### 11. User Experience Features
- Intuitive drag & drop interface
- Visual feedback for all actions
- Confirmation dialogs for destructive actions
- Progress indicators during uploads
- Responsive design for mobile devices

---

## Component Creation Workflow
*(To be documented)*

---

## Brand Management Workflow
*(To be documented)*

---

## Picture Management Workflow
*(To be documented)*