# Selenium Testing Guidelines

**Last Updated**: July 1, 2025 - Added API-Based Testing Patterns

## Overview
Selenium tests are located in `tests/selenium/` and follow the Page Object Model pattern for maintainability. These tests handle end-to-end user workflows and critical UI interactions, including the new API-based variant management system.

## Selenium Testing Rules (MANDATORY)

### Core Principles
- **Use Page Object Model** - Separate page interactions from test logic
- **Explicit waits only** - No `time.sleep()`, use WebDriverWait
- **Test real user workflows** - Complete scenarios, not individual elements
- **Clean state between tests** - Reset database to known state
- **Cross-browser testing** - Chrome (headless for CI), Firefox for manual verification

### TDD Integration with Selenium
Selenium tests are part of the **RED-GREEN-REFACTOR** cycle for end-to-end features:
1. **RED**: Write failing Selenium test for user workflow
2. **GREEN**: Implement frontend/backend code to pass
3. **REFACTOR**: Improve code while keeping E2E tests green

## Page Object Model Pattern

### Page Object Structure
```python
# File: tests/selenium/pages/component_detail_page.py
class ComponentDetailPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    PICTURE_CONTAINER = (By.CLASS_NAME, "picture-container")
    UPLOAD_BUTTON = (By.ID, "upload-picture-btn")
    VARIANT_FORM = (By.ID, "variant-form")
    
    def load(self, component_id):
        """Navigate to component detail page"""
        self.driver.get(f"/components/{component_id}")
        return self
    
    def wait_for_pictures_to_load(self):
        """Wait for pictures to be visible after AJAX refresh"""
        self.wait.until(
            EC.presence_of_element_located(self.PICTURE_CONTAINER)
        )
        return self
    
    def upload_variant_picture(self, color_name, image_path):
        """Upload picture for specific variant"""
        # Find variant section
        variant_section = self.driver.find_element(
            By.XPATH, f"//div[@data-color='{color_name}']"
        )
        
        # Upload file
        file_input = variant_section.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(image_path)
        
        # Submit
        submit_btn = variant_section.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        
        return self
    
    def get_visible_pictures(self):
        """Get list of currently visible pictures"""
        pictures = self.driver.find_elements(By.CSS_SELECTOR, ".picture-container img")
        return [pic.get_attribute("src") for pic in pictures]
```

## Test Categories

### 1. Critical Path Tests (MUST HAVE)
Tests for the main picture visibility issue and core functionality.

```python
# File: tests/selenium/test_component_picture_visibility.py
class TestComponentPictureVisibility:
    """Tests for the main picture visibility issue"""
    
    def test_variant_creation_shows_pictures_immediately(self):
        """RED-GREEN-REFACTOR: Picture visible after variant creation"""
        # Given: Component exists
        component_page = ComponentDetailPage(self.driver)
        component_page.load(self.test_component.id)
        
        # When: User creates variant with picture
        component_page.upload_variant_picture("Red", "/path/to/test/image.jpg")
        
        # Then: Picture appears without page refresh
        component_page.wait_for_pictures_to_load()
        pictures = component_page.get_visible_pictures()
        assert len(pictures) > 0, "Picture should be visible immediately"
    
    def test_component_edit_updates_pictures_realtime(self):
        """Picture changes visible during component editing"""
        # Test edit workflow with picture updates
        pass
    
    def test_ajax_refresh_mechanism_works(self):
        """AJAX refresh loads new pictures correctly"""
        # Test the AJAX solution specifically
        pass
```

### 2. User Workflow Tests
Complete user journey tests from login to task completion.

```python
# File: tests/selenium/test_component_workflows.py
class TestComponentManagementWorkflows:
    """Complete user journey tests"""
    
    def test_complete_component_creation_workflow(self):
        """From login to component with variants and pictures"""
        # Full workflow test
        pass
    
    def test_component_editing_and_approval_workflow(self):
        """Edit component through Proto → SMS → PPS status"""
        # Status progression test
        pass
    
    def test_bulk_component_operations(self):
        """CSV import/export workflows"""
        # Bulk operations test
        pass
```

### 3. Cross-Browser Compatibility Tests
```python
# File: tests/selenium/test_browser_compatibility.py
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
class TestBrowserCompatibility:
    """Ensure features work across browsers"""
    
    def test_picture_upload_cross_browser(self, browser):
        """Picture upload works in all supported browsers"""
        pass
```

## Test Configuration

### Driver Setup
```python
# File: tests/selenium/conftest.py
@pytest.fixture(scope="session")
def selenium_driver():
    """Configure WebDriver for tests"""
    options = ChromeOptions()
    options.add_argument("--headless")  # For CI/CD
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(1)  # Minimal implicit wait
    yield driver
    driver.quit()

@pytest.fixture
def clean_database():
    """Reset database to clean state before each test"""
    # Database cleanup implementation
    with app.app_context():
        db.session.query(Picture).delete()
        db.session.query(ComponentVariant).delete()
        db.session.query(Component).delete()
        db.session.commit()
```

### Test Data Factories
```python
# File: tests/selenium/factories.py
@pytest.fixture
def test_component_with_variants():
    """Create component with known variants for testing"""
    component = ComponentFactory.create(
        product_number="TEST-001",
        description="Test Component"
    )
    
    variant1 = ComponentVariantFactory.create(
        component=component,
        color=ColorFactory.create(name="Red")
    )
    
    variant2 = ComponentVariantFactory.create(
        component=component,
        color=ColorFactory.create(name="Blue")
    )
    
    return component
```

## Best Practices

### Wait Strategies
```python
# GOOD: Explicit waits for dynamic content
def wait_for_picture_upload_complete(self):
    """Wait for upload to complete with proper feedback"""
    self.wait.until(
        EC.text_to_be_present_in_element(
            (By.ID, "upload-status"), "Upload complete"
        )
    )

def wait_for_ajax_to_complete(self):
    """Wait for AJAX requests to finish"""
    self.wait.until(
        lambda driver: driver.execute_script("return jQuery.active == 0")
    )

# BAD: Fixed time delays
time.sleep(5)  # NEVER use this
```

### Element Location Strategies
```python
# Priority order for element location:
1. By.ID - Most reliable, use when possible
2. By.CLASS_NAME - For component-specific elements
3. By.CSS_SELECTOR - For complex selections
4. By.XPATH - Last resort only, avoid if possible

# GOOD: Stable selectors
picture_element = driver.find_element(By.ID, "picture-123")
variant_container = driver.find_element(By.CLASS_NAME, "variant-container")
upload_btn = driver.find_element(By.CSS_SELECTOR, "[data-action='upload']")

# BAD: Fragile selectors
element = driver.find_element(By.XPATH, "//div[3]/span[2]/img")  # Avoid
```

### Error Handling and Debugging
```python
class BasePage:
    """Base page with debugging helpers"""
    
    def take_screenshot(self, name):
        """Take screenshot for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_{name}_{timestamp}.png"
        self.driver.save_screenshot(f"tests/selenium/screenshots/{filename}")
        print(f"Screenshot saved: {filename}")
    
    def wait_and_debug(self, locator, timeout=10):
        """Wait for element with debug info on failure"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            print(f"Element not found: {locator}")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page title: {self.driver.title}")
            self.take_screenshot("timeout_debug")
            raise
    
    def log_console_errors(self):
        """Check for JavaScript console errors"""
        logs = self.driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        if errors:
            print("JavaScript errors found:")
            for error in errors:
                print(f"  {error['message']}")
```

## Test Commands

### Running Selenium Tests
```bash
# Run all Selenium tests
pytest tests/selenium/

# Run specific test file
pytest tests/selenium/test_component_picture_visibility.py

# Run with visible browser (for debugging)
pytest tests/selenium/ --headed

# Run with specific browser
pytest tests/selenium/ --browser=firefox

# Run only critical path tests
pytest tests/selenium/ -m "critical"

# Run with detailed output
pytest tests/selenium/ -v -s

# Run with screenshot on failure
pytest tests/selenium/ --screenshot-on-failure
```

### Parallel Execution
```bash
# Run tests in parallel (faster execution)
pytest tests/selenium/ -n 4

# Run specific markers in parallel
pytest tests/selenium/ -m "not slow" -n 2
```

## CI/CD Integration

### Headless Configuration
```python
# For CI environments
@pytest.fixture
def ci_driver():
    """Driver configuration for CI/CD"""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    return driver
```

### Failure Artifacts
- **Screenshot on failure** - Automatic capture for debugging
- **HTML source dump** - Save page source when tests fail
- **Browser logs** - Capture console errors and warnings
- **Video recording** - For complex workflow failures (optional)

## API-Based Testing Patterns (NEW - JULY 2025)

### Testing Real-time API Operations
**CRITICAL**: Test the new API-first variant management system:

```python
# File: tests/selenium/test_api_based_operations.py
class TestAPIBasedVariantManagement:
    """Tests for API-first variant operations"""
    
    def test_real_time_variant_creation(self):
        """Create variant via API without page reload"""
        # Given: Component edit page is loaded
        edit_page = ComponentEditPage(self.driver)
        edit_page.load(self.test_component.id)
        
        # When: User adds new variant with API
        edit_page.add_variant_via_ui("Green")
        edit_page.upload_pictures_for_variant("Green", [test_image_path])
        
        # Then: Variant appears immediately without refresh
        variants = edit_page.get_displayed_variants()
        assert "Green" in [v.color_name for v in variants]
        
        # And: Pictures are visible immediately
        pictures = edit_page.get_variant_pictures("Green")
        assert len(pictures) > 0
    
    def test_api_error_handling_workflow(self):
        """Test graceful error handling for API failures"""
        # Given: Network issues or API failures
        edit_page = ComponentEditPage(self.driver)
        edit_page.load(self.test_component.id)
        
        # When: API operation fails
        # Simulate network failure or server error
        
        # Then: User sees helpful error message
        error_message = edit_page.get_error_message()
        assert "Failed to create variant" in error_message
        
        # And: UI remains functional for retry
        assert edit_page.is_retry_button_visible()
    
    def test_loading_states_during_api_operations(self):
        """Test professional loading indicators"""
        edit_page = ComponentEditPage(self.driver)
        edit_page.load(self.test_component.id)
        
        # When: Starting variant creation
        edit_page.start_variant_creation("Blue")
        
        # Then: Loading indicator is visible
        assert edit_page.is_loading_indicator_visible()
        
        # When: Operation completes
        edit_page.wait_for_variant_creation_complete()
        
        # Then: Loading indicator disappears
        assert not edit_page.is_loading_indicator_visible()
```

### Testing Smart Creation Workflow
```python
def test_component_creation_with_api_variants(self):
    """Test new creation workflow: component first, then variants via API"""
    # Given: Component creation form
    create_page = ComponentCreatePage(self.driver)
    create_page.load()
    
    # When: User fills form with variants
    create_page.fill_component_details("TEST-001", "Test Component")
    create_page.add_variant("Red", [test_image_path])
    create_page.add_variant("Blue", [test_image_path])
    create_page.submit_form()
    
    # Then: Redirected to detail page with variants
    detail_page = ComponentDetailPage(self.driver)
    detail_page.wait_for_component_load()
    
    variants = detail_page.get_displayed_variants()
    assert len(variants) == 2
    assert "Red" in [v.color_name for v in variants]
    assert "Blue" in [v.color_name for v in variants]
    
    # And: All pictures are visible immediately
    for variant in variants:
        pictures = detail_page.get_variant_pictures(variant.color_name)
        assert len(pictures) > 0
```

### Testing File Upload Integration
```python
def test_webdav_file_integration(self):
    """Test proper WebDAV file handling with database triggers"""
    edit_page = ComponentEditPage(self.driver)
    edit_page.load(self.test_component.id)
    
    # When: Upload picture for variant
    edit_page.upload_picture_for_variant("Red", test_image_path)
    
    # Then: Picture appears with correct WebDAV URL
    picture_url = edit_page.get_picture_url("Red", 0)
    assert "http://31.182.67.115/webdav/components" in picture_url
    
    # And: Picture name follows database naming convention
    picture_name = edit_page.get_picture_name("Red", 0)
    assert "_red_1" in picture_name.lower()  # Follows naming pattern
```

## Current Testing Priorities (UPDATED)

### Immediate Focus (Critical)
1. **API-based variant operations** - Real-time creation, editing, deletion
2. **Smart creation workflow** - Component first, then variants via API
3. **Error handling and recovery** - Graceful failure handling
4. **Loading states and UX** - Professional feedback during operations

### Secondary Priorities
1. **Cross-browser compatibility** - Chrome, Firefox with API operations
2. **Performance testing** - API response times, real-time updates
3. **File upload integration** - WebDAV and database trigger testing
4. **Mobile responsiveness** - Touch interactions with API operations

## Test Markers
```python
# Use pytest markers to categorize tests
@pytest.mark.critical
def test_core_functionality():
    """Critical path test - must pass"""
    pass

@pytest.mark.slow
def test_complex_workflow():
    """Slow test - run separately"""
    pass

@pytest.mark.browser_specific
def test_firefox_feature():
    """Browser-specific functionality"""
    pass
```

## Integration with TDD Cycle

### For New Features
1. **RED**: Write failing Selenium test for user story
2. **GREEN**: Implement minimal frontend/backend code
3. **REFACTOR**: Improve while keeping E2E test green

### For Bug Fixes
1. **RED**: Write Selenium test that reproduces the bug
2. **GREEN**: Fix the bug to make test pass
3. **REFACTOR**: Clean up fix while maintaining test success

This ensures that critical user workflows are always protected by automated tests.