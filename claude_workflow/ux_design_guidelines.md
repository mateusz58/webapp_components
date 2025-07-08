# UX Design Guidelines

## 🎯 Core Design Philosophy: Manufacturing Workflow Efficiency

### Daily User Context
This application serves **manufacturing professionals** who:
- Work 8+ hours daily in the system
- Need rapid access to component specifications and images
- Switch between components frequently during their workflow
- Work under time pressure with production deadlines
- Require clear visual confirmation of component details
- Need efficient brand and supplier information access

### 📊 Measured UX Improvements (January 2025)
**Score**: 52.5/100 → 76.2/100 (45% improvement)  
**Status**: "POOR - Not suitable for daily use" → "GOOD - Suitable for daily use"

## 🏭 Manufacturing-Specific Design Principles

### 1. **Information Density Priority**
**Rationale**: Manufacturing teams need multiple data points visible simultaneously
- Component images + specifications + status + brands
- Minimal clicking/scrolling between related information
- Visual hierarchy that prioritizes critical manufacturing data

### 2. **Visual Confirmation Workflow**
**Rationale**: Manufacturing requires visual verification to prevent costly errors
- Large, clear product images always visible
- Multiple variant views accessible without losing context
- Color/material information prominently displayed

### 3. **Status-First Design**
**Rationale**: Production workflow depends on approval status
- Approval workflow (Proto → SMS → PPS) prominently displayed
- Color-coded status indicators for quick scanning
- Progress indicators for pending approvals

### 4. **Rapid Information Access**
**Rationale**: Time-pressured environment requires efficient navigation
- Two-column layout keeps images visible while browsing details
- Tabbed interface for logical information grouping
- Sticky elements prevent re-navigation

### 5. **Error Prevention Focus**
**Rationale**: Manufacturing errors are costly and time-consuming
- Clear visual distinctions between component variants
- Prominent supplier and brand information
- Consistent naming conventions and SKU display

## ✅ Proven Layout Design Patterns

### Two-Column Grid Layout
**Implementation**: `component-content-grid` with CSS Grid
```css
.component-content-grid {
  display: grid;
  grid-template-columns: 1fr 480px;
  gap: var(--cd-space-lg);
  align-items: start;
}
```

**Benefits**:
- ✅ Reduces vertical scrolling by 30-40%
- ✅ Keeps image gallery visible while browsing information
- ✅ Maximizes viewport usage efficiency

### Sticky Image Gallery (Left Column)
**Implementation**: `position: sticky` with proper top offset
```css
.component-content__gallery {
  position: sticky;
  top: var(--cd-space-lg);
  overflow: hidden;
}
```

**Benefits**:
- ✅ Images remain visible during information browsing
- ✅ Reduces cognitive load for daily users
- ✅ Improves workflow efficiency

### Compact Information Panel (Right Column)
**Implementation**: Fixed height with scrollable content
```css
.component-content__info {
  min-height: calc(100vh - 140px);
  max-height: calc(100vh - 140px);
  overflow-y: auto;
}
```

**Benefits**:
- ✅ Contains scrolling to information area only
- ✅ Prevents full-page vertical scrolling
- ✅ Maintains consistent layout height

## 📐 Responsive Design Standards

### Breakpoint Strategy
```css
/* Large Desktop (2560x1440) */
@media (min-width: 1400px) {
  /* Full two-column experience */
  grid-template-columns: 1fr 480px;
}

/* Standard Desktop (1920x1080) */
@media (max-width: 1400px) {
  grid-template-columns: 1fr 420px;
}

/* Laptop (1366x768) */
@media (max-width: 1200px) {
  /* Single column with optimized heights */
  grid-template-columns: 1fr;
  .component-content__gallery {
    max-height: 400px;
    overflow-y: auto;
  }
}
```

### Viewport Usage Targets
- **Desktop (1920x1080)**: 70-85% viewport usage
- **Large Desktop (2560x1440)**: 85%+ viewport usage
- **Laptop (1366x768)**: 45-60% viewport usage (acceptable due to height constraints)

## 🎨 Visual Design Standards

### Color Hierarchy
```css
/* Primary brand color for interactive elements */
--cd-primary: #3b82f6;
--cd-primary-dark: #1d4ed8;
--cd-primary-light: #dbeafe;

/* Status colors for workflow stages */
--cd-success: #10b981;
--cd-warning: #f59e0b;
--cd-error: #ef4444;
```

### Spacing Optimization for Daily Use
```css
/* Reduced padding for compact layouts */
--cd-space-xs: 0.25rem;
--cd-space-sm: 0.5rem;
--cd-space-md: 1rem;    /* Primary spacing unit */
--cd-space-lg: 1.5rem;  /* Section separation */
--cd-space-xl: 2rem;    /* Major section separation */
```

### Typography Scale
```css
/* Optimized for readability during extended use */
--cd-text-xs: 0.75rem;   /* Labels, metadata */
--cd-text-sm: 0.875rem;  /* Body text, form inputs */
--cd-text-base: 1rem;    /* Primary content */
--cd-text-lg: 1.125rem;  /* Section headers */
--cd-text-xl: 1.25rem;   /* Tab headers */
```

## 🔧 Specific Implementation Guidelines

### MANDATORY: Always Apply These Design Rules

#### 1. **Two-Column Layout Standard**
```css
.component-content-grid {
  display: grid;
  grid-template-columns: 1fr 480px;  /* NEVER change this ratio */
  gap: var(--cd-space-lg);
  align-items: start;
}
```
**Rule**: All component detail pages MUST use this layout. Never revert to single-column.

#### 2. **Image Gallery Requirements**
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
**Rule**: Images must remain visible while user browses information. This is critical for manufacturing workflow.

#### 3. **Information Panel Constraints**
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

#### 4. **Status Workflow Positioning**
```css
.status-workflow-compact {
  padding: var(--cd-space-md);  /* ALWAYS use compact padding */
  margin-bottom: var(--cd-space-md);  /* NEVER use xl spacing */
}
```
**Rule**: Status must be immediately visible. No excessive spacing that pushes it down.

#### 5. **Responsive Breakpoints (MANDATORY)**
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
**Rule**: These breakpoints are tested and proven. Do not modify without re-testing.

### Manufacturing-Specific Component Standards

#### Brand Information Display
```html
<!-- ALWAYS include brand tab -->
<button class="nav-link" @click="selectTab('brands')">
  <i data-lucide="package"></i>
  Brands
</button>

<!-- Brand cards MUST show: name, ID, association date -->
<div class="brand-card">
  <h6 class="brand-name">{{ brand.name }}</h6>
  <div class="brand-detail">
    <span class="brand-detail-label">ID</span>
    <span class="brand-detail-value">{{ brand.id }}</span>
  </div>
</div>
```
**Rule**: Brand information is critical for manufacturing. Always prominently display.

#### Status Indicators (CRITICAL)
```html
<!-- ALWAYS use color-coded status badges -->
<span class="status-badge status-badge--{{ status }}">{{ status|title }}</span>

<!-- Workflow progress MUST be visual -->
<div class="approval-workflow">
  <div class="workflow-step {{ 'completed' if proto_status == 'ok' }}">
    Proto Review
  </div>
</div>
```
**Rule**: Manufacturing teams scan status quickly. Color coding is mandatory.

#### Component Information Hierarchy
```
1. HEADER: Product number + status (most critical)
2. LEFT: Images + variant selection (visual confirmation)
3. RIGHT TOP: Approval workflow (production status)
4. RIGHT BOTTOM: Detailed information tabs
```
**Rule**: This hierarchy is tested and optimized. Do not change order.

### Typography and Spacing Rules

#### Font Sizes (FIXED - Do Not Change)
```css
--cd-text-xs: 0.75rem;   /* Labels, metadata only */
--cd-text-sm: 0.875rem;  /* Body text, form inputs */
--cd-text-base: 1rem;    /* Primary content */
--cd-text-lg: 1.125rem;  /* Section headers only */
--cd-text-xl: 1.25rem;   /* Tab headers only */
```
**Rule**: These sizes are optimized for 8+ hour daily use. Larger text causes scrolling.

#### Spacing Standards (MANDATORY)
```css
/* Component sections */
margin-bottom: var(--cd-space-lg);  /* Between major sections */

/* Within components */
padding: var(--cd-space-md);        /* Standard component padding */

/* Information density */
gap: var(--cd-space-sm);            /* Between related items */
```
**Rule**: Consistent spacing reduces cognitive load during long work sessions.

### Color Usage Guidelines

#### Status Colors (NEVER Change)
```css
--cd-success: #10b981;   /* Approved, OK status */
--cd-warning: #f59e0b;   /* Pending, awaiting review */
--cd-error: #ef4444;     /* Rejected, not OK status */
```
**Rule**: Manufacturing teams rely on color coding for rapid status assessment.

#### Interactive Elements
```css
--cd-primary: #3b82f6;      /* Primary actions, selected states */
--cd-primary-dark: #1d4ed8; /* Hover states, emphasis */
```
**Rule**: Consistent interaction colors reduce learning curve.

### Performance Requirements

#### Image Loading
- Main image MUST load within 2 seconds
- Thumbnails MUST be optimized for rapid switching
- Gallery MUST remain responsive during image changes

#### Tab Switching
- Tab content MUST appear within 500ms
- No loading states required for tab switching
- Smooth transitions without jarring layout shifts

#### Responsive Behavior
- Layout changes MUST be instant on resize
- No horizontal scrolling ever permitted
- Sticky elements MUST maintain position during scroll

### Error Prevention Standards

#### Visual Feedback
- Selected variants MUST be clearly highlighted
- Active tabs MUST have distinct visual states
- Status changes MUST be immediately visible

#### Information Clarity
- SKUs MUST be displayed with monospace font
- Color names MUST match visual color swatches
- Supplier codes MUST be easily distinguishable

### Testing Requirements

#### Before ANY Layout Changes
1. Run daily user perspective test
2. Verify score maintains 70+ rating
3. Test on all three standard resolutions
4. Validate manufacturing workflow efficiency

#### Mandatory Test Scenarios
1. Component with multiple variants (Component 2)
2. Component with brand associations (Component 217)
3. Components with missing images
4. Components in different approval states

**Rule**: Any UX change that reduces daily user score below 70 must be reverted.

## 📊 Testing and Validation

### Daily User Score Calculation
```
Score = Viewport Efficiency (30pts) + 
        Layout Structure (25pts) + 
        Information Accessibility (20pts) + 
        Workflow Efficiency (15pts) + 
        Reduced Scrolling (10pts)
```

### Score Targets
- **90-100**: Excellent for daily use
- **70-89**: Good for daily use (target achieved: 76.2/100)
- **50-69**: Fair, may cause fatigue
- **Below 50**: Poor, not suitable for daily use

### Testing Scenarios
1. **Component 2**: Primary test case (user-suggested)
2. **Component 217**: Brand association functionality test
3. **Multiple Resolutions**: 1366x768, 1920x1080, 2560x1440
4. **Selenium Automation**: Visual testing with score calculation

## 🚀 Implementation Checklist

### Before Layout Changes
- [ ] Read current UX score via Selenium test
- [ ] Identify specific pain points from test metrics
- [ ] Plan responsive behavior across breakpoints

### During Implementation
- [ ] Maintain two-column grid structure
- [ ] Optimize spacing for daily use (reduce padding/margins)
- [ ] Implement sticky positioning for key elements
- [ ] Add max-height constraints to prevent excessive scrolling

### After Implementation
- [ ] Run comprehensive Selenium UX test
- [ ] Verify score improvement (target: 70+)
- [ ] Test across all responsive breakpoints
- [ ] Validate information accessibility

## 🔄 Continuous Improvement

### Performance Monitoring
- Monthly UX score testing via Selenium
- User feedback collection for daily usage patterns
- Performance metrics for tab switching and scrolling

### Future Enhancements
- Advanced viewport size detection
- User preference settings for layout density
- Dynamic content optimization based on usage patterns

## 📝 File Structure for UX Components

### CSS Organization
```
app/static/css/component-detail/
├── main.css           # Core layout and grid system
├── tabs.css           # Tab component and content styling
├── gallery.css        # Image gallery and variant display
└── workflow.css       # Status workflow and approval system
```

### Template Structure
```
app/templates/
├── component_detail.html              # Main layout template
└── sections/
    ├── component_info_tabs.html        # Information tabs
    ├── variant_gallery.html            # Image gallery
    └── status_workflow.html            # Approval workflow
```

### Testing Structure
```
tests/selenium/
├── test_component_layout_daily_user_perspective.py  # UX testing
└── utils/
    └── ux_score_calculator.py                       # Score calculation
```

## 🎯 Key Success Metrics

### Achieved Improvements (January 2025)
- **45% UX Score Improvement**: 52.5 → 76.2
- **Viewport Usage**: 71.9%-86.1% across screen sizes
- **Layout Structure**: Two-column grid implemented
- **Scrolling Reduction**: Information more accessible above fold
- **Responsive Design**: Consistent experience across devices

### Design Philosophy
> **"Design for the user who spends 8 hours daily in the application"**

This means prioritizing:
1. **Reduced eye strain** through efficient layouts
2. **Minimal scrolling** via optimized information density
3. **Predictable interactions** for workflow efficiency
4. **Visual consistency** across all screen sizes
5. **Information accessibility** without excessive navigation

## 🚨 Critical "Do NOT" Rules for Manufacturing UX

### NEVER Do These Things:
1. **NEVER** revert to single-column layout on desktop resolutions
2. **NEVER** remove sticky positioning from image gallery
3. **NEVER** increase font sizes above the specified scale
4. **NEVER** add excessive spacing that pushes content below fold
5. **NEVER** hide status information or make it secondary
6. **NEVER** remove color coding from status indicators
7. **NEVER** allow horizontal scrolling on any screen size
8. **NEVER** make layout changes without running UX score test first
9. **NEVER** prioritize aesthetics over manufacturing workflow efficiency
10. **NEVER** assume users want "pretty" over "functional"

### Manufacturing Context Priorities:
1. **Speed of information access** > Visual appeal
2. **Information density** > White space
3. **Workflow efficiency** > Modern design trends
4. **Error prevention** > Simplified interfaces
5. **Visual confirmation** > Text-only information

## 🎯 Your Specific Manufacturing Workflow Needs

### Primary User Goals (In Order of Priority):
1. **Rapidly verify component appearance** - Large, persistent images
2. **Check approval status quickly** - Color-coded, prominent workflow
3. **Access supplier/brand information** - Immediate tab access
4. **Compare component variants** - Easy variant switching
5. **Confirm technical specifications** - Tabbed detail organization

### Time-Critical Tasks That Must Be Optimized:
- **Component verification**: Image + status visible simultaneously
- **Variant comparison**: No context loss when switching colors
- **Status checking**: Approval workflow always visible
- **Brand verification**: One-click access to brand information
- **SKU confirmation**: Clearly displayed, copy-friendly format

### Daily Workflow Pattern:
```
1. Open component → See image + status immediately
2. Check variants → Gallery stays visible, variants switch fast
3. Verify brands → Click brands tab, information loads instantly
4. Check specifications → Tab through properties without losing image context
5. Confirm status → Workflow progress clear at all times
```

### Screen Usage Patterns:
- **Primary monitor**: 1920x1080 (most common)
- **Secondary monitor**: Often smaller, 1366x768
- **Dual monitor setup**: Application on secondary while main has CAD/specs
- **Usage time**: 6-8 hours continuous daily use

### Information Priority Hierarchy:
```
CRITICAL (Always visible):
- Component image
- Product number/SKU
- Approval status

HIGH (One click away):
- Component variants
- Brand information
- Supplier details

MEDIUM (Tabbed access):
- Technical properties
- Keywords/tags
- Additional specifications
```

### Fatigue Prevention Requirements:
- **Minimal scrolling**: Reduces repetitive strain
- **High contrast**: Reduces eye strain
- **Consistent layouts**: Reduces cognitive load
- **Predictable interactions**: Reduces mental effort
- **Compact spacing**: Maximizes information density

---

**Last Updated**: January 2025  
**Context**: Manufacturing component management for daily professional use  
**Focus**: Workflow efficiency over visual design  
**Testing**: Validated with 76.2/100 daily user score  
**Status**: Active guidelines - Mandatory for all UX work