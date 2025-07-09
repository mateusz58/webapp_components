# Testing Rules

**Last Updated**: July 9, 2025

## 🚨 CRITICAL: MANDATORY TESTING REQUIREMENTS 🚨

### BEFORE ANY DEVELOPMENT WORK (ABSOLUTE REQUIREMENT)
**ALL TESTS MUST PASS BEFORE PROCEEDING WITH ANY TASK**

1. **Run Test Suite**: Execute `python tools/run_tests.py` before starting ANY development work
2. **Fix Failing Tests**: If any tests fail, STOP development and fix them first
3. **No Exceptions**: No new features, bug fixes, or refactoring until all tests pass
4. **After Changes**: Run full test suite again after making ANY changes
5. **Commit Only Green**: Only commit code when all tests are passing

### TDD (Test-Driven Development) Protocol (MANDATORY)
**STICK TO ONE TEST - FIX UNTIL IT PASSES**

1. **One Test Focus**: Pick ONE failing test and focus only on it
2. **Run Single Test**: Use `python -m pytest tests/path/to/test.py::TestClass::test_method -v`
3. **Analyze Failure**: Read the error message carefully - don't guess
4. **Make Minimal Fix**: Fix only what's needed to make THIS test pass
5. **Re-run Same Test**: Test the same test again after fix
6. **Repeat Until Green**: Continue fixing until this ONE test passes
7. **Move to Next**: Only after success, move to the next failing test
8. **No Parallel Fixes**: Don't fix multiple tests simultaneously

## Universal Testing Rules

### 1. Test Organization Structure (MANDATORY)
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Fast isolated tests (< 1s each)
├── integration/             # Database integration tests (< 5s each)
├── api/                     # API endpoint tests (< 3s each)
├── selenium/                # E2E UI tests (10-30s each)
├── services/                # Service layer tests (business logic)
├── utils/                   # Utility function tests
└── models/                  # Database model tests
```

### 2. Test Type Definitions (CRITICAL)

#### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and methods in isolation
- **Speed**: < 1 second each
- **Dependencies**: All external dependencies mocked (database, files, APIs)
- **Focus**: Logic validation, data transformation, calculations

#### Integration Tests (`tests/integration/`)
- **Purpose**: Test interaction between components (database + code)
- **Speed**: < 5 seconds each
- **Dependencies**: Real database, mocked external services (WebDAV)
- **Focus**: Database operations, ORM relationships, transaction handling

#### API Tests (`tests/api/`)
- **Purpose**: Test HTTP endpoints end-to-end
- **Speed**: < 3 seconds each  
- **Dependencies**: Real Flask app, real database, mocked external services
- **Focus**: Request/response handling, status codes, JSON format

#### Selenium Tests (`tests/selenium/`)
- **Purpose**: Test complete user workflows in browser
- **Speed**: 10-30 seconds each
- **Dependencies**: Real application, real browser, real database
- **Focus**: UI interactions, JavaScript functionality, visual validation

### 3. Test Organization Rules (CRITICAL)
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

### 4. Test Execution Commands (MANDATORY)
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

### 5. Testing Rules (NON-NEGOTIABLE)
1. **NO TEMPORARY TESTS IN ROOT**: All tests must be in `tests/` folder with proper organization
2. **NO BROKEN TESTS**: Failing tests must be fixed immediately, not ignored
3. **NO DEVELOPMENT ON RED**: Do not write new code when tests are failing
4. **CLEAN TEST CODE**: Tests must be maintainable and well-organized
5. **TEST COVERAGE**: New features require corresponding tests
6. **ISOLATION**: Tests must not depend on each other or external state

### 6. Test Failure Protocol (MANDATORY)
When tests fail:
1. **STOP ALL DEVELOPMENT WORK**
2. **Analyze the failure** - read the error messages carefully
3. **Fix the root cause** - don't just make tests pass artificially
4. **Run full test suite** - ensure fix doesn't break other tests
5. **Only then continue** with planned development work

## TDD (Test-Driven Development) Methodology

### 1. TDD Workflow (MANDATORY)
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

### 2. TDD Rules for This Project
- **No production code** without a failing test first
- **Tests must be isolated** - no dependencies between tests
- **Use descriptive test names** that explain behavior
- **Test one behavior per test** - keep tests focused
- **Mock external dependencies** (WebDAV, file system)

### 3. Testing Framework Structure
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

### 4. TDD for UI Race Conditions (PROVEN PATTERN)
1. **Write Selenium test** that detects timing issues with millisecond precision
2. **Implement multi-layer solutions** to pass all timing scenarios
3. **Refactor** with console logging and comprehensive fallbacks

Example Pattern for Loading Indicators:
- Layer 1: Immediate CSS (`body[data-attribute]`)
- Layer 2: JavaScript URL parameter detection
- Layer 3: Alpine.js component factory initialization
- Layer 4: API auto-refresh with exponential backoff

## Backend Testing Standards

### 1. Unit Testing Pattern
```python
# Test business logic in isolation
def test_generate_variant_sku_with_supplier():
    # Test SKU generation logic
    pass

def test_picture_name_generation():
    # Test picture naming logic
    pass
```

### 2. Integration Testing Pattern
```python
# Test database operations
def test_component_variant_creation_updates_sku():
    # Test database triggers work correctly
    pass

def test_picture_save_with_rollback():
    # Test transaction rollback on file save failure
    pass
```

### 3. API Testing Pattern
```python
# Test HTTP endpoints
def test_component_creation_endpoint():
    # Test API request/response handling
    pass

def test_validation_error_responses():
    # Test proper error handling
    pass
```

### 4. Service Layer Testing
- **Unit Tests**: Test service layer business logic in isolation
- **Integration Tests**: Test service + database integration  
- **Mock Dependencies**: Mock external services (WebDAV, file system)
- **Transaction Testing**: Test rollback scenarios

### 5. Database Testing
- Use **fixtures** for consistent test data
- **Clean up after tests** - restore database state
- **Use test-specific data** - avoid shared state
- **Test triggers**: Ensure database triggers work correctly

## Frontend Testing Standards

### 1. Selenium Testing Guidelines

#### Core Principles
- **Use Page Object Model** - Separate page interactions from test logic
- **Explicit waits only** - No `time.sleep()`, use WebDriverWait
- **Test real user workflows** - Complete scenarios, not individual elements
- **Clean state between tests** - Reset database to known state
- **Cross-browser testing** - Chrome (headless for CI), Firefox for manual verification

#### Page Object Model Pattern
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

#### Wait Strategies
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

#### Element Location Strategies
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

#### Error Handling and Debugging
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

#### Test Categories
1. **Critical Path Tests**: Main picture visibility issue and core functionality
2. **User Workflow Tests**: Complete user journey tests from login to task completion
3. **Cross-Browser Compatibility Tests**: Ensure features work across browsers
4. **API-Based Testing**: Test real-time API operations and integration

#### Test Configuration
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
```

#### Running Selenium Tests
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

### 2. JavaScript Testing

#### Page Object Model Pattern
```python
class ComponentEditPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def fill_product_number(self, value):
        element = self.wait.until(EC.presence_of_element_located((By.ID, "product_number")))
        element.clear()
        element.send_keys(value)
    
    def submit_form(self):
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
```

#### Test Categories
1. **UI Interactions**: Form submissions, button clicks, navigation
2. **AJAX Functionality**: Real-time updates, dynamic content loading
3. **Visual Validation**: Element visibility, layout correctness
4. **Error Handling**: Error message display, validation feedback

#### Best Practices
- Use explicit waits instead of sleep()
- Handle stale element exceptions
- Test across different browsers
- Use proper element locators (ID > CSS > XPath)

### 2. JavaScript Testing
- **Unit Tests**: Test individual JS functions
- **Integration Tests**: Test API interactions
- **DOM Testing**: Test DOM manipulation
- **Event Testing**: Test user interactions

### 3. CSS Testing
- **Visual Regression**: Compare screenshots
- **Responsive Testing**: Test different screen sizes
- **Cross-browser Testing**: Ensure consistency
- **Accessibility Testing**: Test with screen readers

## Testing Data Management

### 1. Test Fixtures
- Create reusable test data factories
- Use Factory Boy for object creation
- Maintain test data isolation
- Clean up after each test

### 2. Database Testing
- Use separate test database
- Reset database state between tests
- Use transactions for rollback
- Test database constraints

### 3. File Testing
- Mock file operations in unit tests
- Use temporary files for integration tests
- Clean up test files after tests
- Test file upload/download workflows

## Performance Testing

### 1. Load Testing
- Test API endpoints under load
- Measure response times
- Test concurrent user scenarios
- Monitor resource usage

### 2. Database Performance
- Test query performance
- Monitor slow queries
- Test with realistic data volumes
- Optimize based on test results

### 3. Frontend Performance
- Test page load times
- Measure JavaScript execution time
- Test with slow network conditions
- Monitor memory usage

## Test Coverage Requirements

### 1. Coverage Targets
- **Minimum 80% code coverage** for new features
- **100% coverage** for critical paths (picture operations, SKU generation)
- **All database triggers** must have corresponding tests
- **All AJAX endpoints** must have integration tests

### 2. Coverage Analysis
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Coverage for specific modules
pytest --cov=app.services --cov-report=term-missing
```

### 3. Critical Areas for Testing
- File upload and processing
- Database trigger operations
- API endpoint responses
- User authentication and authorization
- Error handling and validation

## Testing Tools and Framework

### 1. Required Testing Dependencies
```txt
# Testing Framework (MANDATORY)
pytest==8.4.1
pytest-cov==4.1.0
pytest-html==3.2.0
pytest-mock==3.11.1
selenium==4.15.0
coverage==7.3.2
pytest-json-report==1.5.0
```

### 2. Testing Configuration
- Configure pytest in `pytest.ini` or `pyproject.toml`
- Set up test database configuration
- Configure Selenium WebDriver
- Set up CI/CD pipeline integration

### 3. Test Report Generation
```bash
# Generate HTML test report
pytest --html=reports/test_report.html

# Generate JSON test report
pytest --json-report --json-report-file=reports/test_results.json

# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term
```

## Continuous Integration

### 1. Pre-commit Hooks
- Run linting and formatting
- Execute fast test suite
- Check code coverage
- Validate commit messages

### 2. CI Pipeline
- Run full test suite on every commit
- Test on multiple Python versions
- Generate and store test reports
- Deploy only if all tests pass

### 3. Quality Gates
- All tests must pass
- Code coverage must meet threshold
- No critical security vulnerabilities
- Performance benchmarks must pass

## Testing Best Practices

### 1. Test Writing Guidelines
- Write tests before implementing features (TDD)
- Use descriptive test names
- Keep tests simple and focused
- Avoid test dependencies
- Use proper assertions

### 2. Test Maintenance
- Update tests when requirements change
- Remove obsolete tests
- Refactor tests for clarity
- Monitor test execution time

### 3. Debugging Tests
- Use comprehensive logging
- Add debug output to failing tests
- Use debugger for complex issues
- Test in isolation when debugging

## Test Documentation

### 1. Test Report Format
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

### 2. Test Documentation Requirements
- Update `test_reports.md` after every testing session
- Document test failures and resolutions
- Track test coverage improvements
- Document testing strategy changes