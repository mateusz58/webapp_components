# Testing Rules

**Last Updated**: July 11, 2025

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

### 1. Testing Framework (MANDATORY)

**WE USE PYTEST, NOT UNITTEST**

This project uses **pytest** as the testing framework, NOT Python's unittest module.

**CRITICAL REQUIREMENTS:**
- ❌ **NEVER use `unittest.TestCase`** - This is wrong for this project
- ✅ **USE pytest functions and fixtures** 
- ❌ **NEVER import unittest** in test files
- ✅ **USE pytest.fixture** for test setup
- ❌ **NEVER use `self.assertEqual`, `self.assertTrue`** - These are unittest assertions
- ✅ **USE `assert` statements** - This is pytest style

**CORRECT PYTEST TEST STRUCTURE:**
```python
# ✅ CORRECT: pytest style
import pytest
from app.services.component_service import ComponentService

@pytest.fixture
def component_service():
    return ComponentService()

def test_should_create_component_successfully_when_valid_data(component_service):
    """
    Test: Component creation with valid data
    Given: Valid component data
    When: create_component is called
    Then: Component should be created successfully
    """
    # Arrange
    data = {'product_number': 'TEST-001', 'component_type_id': 1}
    
    # Act
    result = component_service.create_component(data)
    
    # Assert
    assert result['success'] is True
    assert result['component']['product_number'] == 'TEST-001'
```

**❌ WRONG UNITTEST STYLE (DO NOT USE):**
```python
# ❌ WRONG: unittest style - DO NOT USE
import unittest
from unittest.mock import Mock

class TestComponentService(unittest.TestCase):  # ❌ WRONG
    def setUp(self):  # ❌ WRONG
        pass
        
    def test_something(self):
        self.assertTrue(something)  # ❌ WRONG - use assert instead
        self.assertEqual(a, b)      # ❌ WRONG - use assert a == b
```

**WHY PYTEST?**
- Better fixtures and dependency injection
- Simpler assert statements
- Better test discovery
- Cleaner test code
- Better integration with modern Python tools

### 2. Test Organization Structure (MANDATORY - STRICTLY ENFORCED)

#### ❌ **CRITICAL: NO TEST FILES IN PROJECT ROOT DIRECTORY**
All test files MUST be in the `tests/` directory structure. Any test file in the project root is a VIOLATION.

#### ✅ **PROPER TEST ORGANIZATION STRUCTURE**
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Fast isolated tests (< 1s each)
│   ├── services/           # One file per service class
│   │   ├── test_component_service.py      # ALL unit tests for ComponentService
│   │   ├── test_csv_service.py           # ALL unit tests for CsvService
│   │   └── test_webdav_storage_service.py # ALL unit tests for WebDAVStorageService
│   ├── utils/              # Utility function tests
│   ├── models/             # Model-specific unit tests
│   └── web/                # Web route logic tests (mocked)
├── integration/             # Database integration tests (< 5s each)
│   ├── services/           # Service integration tests
│   │   ├── test_component_service_integration.py  # ComponentService + DB
│   │   └── test_csv_service_integration.py       # CsvService + DB
│   ├── models/             # Model integration tests
│   └── workflows/          # Multi-component workflow tests
├── api/                     # API endpoint tests (< 3s each)
│   ├── test_component_api.py    # ALL component API endpoints
│   ├── test_brand_api.py        # ALL brand API endpoints
│   ├── test_supplier_api.py     # ALL supplier API endpoints
│   └── test_variant_api.py      # ALL variant API endpoints
├── selenium/                # E2E UI tests (10-30s each)
│   ├── features/           # BDD/Gherkin test features
│   │   ├── component_creation.feature
│   │   └── step_definitions/
│   ├── pages/              # Page Object Model classes
│   └── workflows/          # Complete user workflow tests
└── performance/            # Performance and load tests
```

#### 🚫 **STRICT RULES FOR TEST FILE ORGANIZATION**

1. **ONE TEST FILE PER SERVICE/COMPONENT**
   - ❌ WRONG: `test_component_service_complete.py`, `test_component_service_comprehensive.py`, `test_component_service_final.py`
   - ✅ RIGHT: `test_component_service.py` (containing ALL tests for ComponentService)

2. **NEVER CREATE MULTIPLE FILES FOR SAME COMPONENT**
   - ❌ WRONG: Creating new test file for each scenario
   - ✅ RIGHT: Add new test cases to existing appropriate file

3. **GROUP TESTS BY COMPONENT, NOT BY FEATURE**
   - ❌ WRONG: `test_picture_renaming.py`, `test_sku_generation.py` (scattered)
   - ✅ RIGHT: All in `test_component_service.py` under appropriate test classes

4. **USE TEST CLASSES FOR LOGICAL GROUPING**
   ```python
   # tests/unit/services/test_component_service.py
   class TestComponentServiceCreation:
       """Tests for component creation functionality"""
       
   class TestComponentServiceUpdate:
       """Tests for component update functionality"""
       
   class TestComponentServicePictureHandling:
       """Tests for picture management functionality"""
   ```

5. **INTEGRATION VS UNIT TEST SEPARATION**
   - Unit tests: Mock all external dependencies (DB, WebDAV, etc.)
   - Integration tests: Test with real database but mock external services
   - Keep them in separate files with clear naming

### 2. Test Type Definitions (CRITICAL)

#### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and methods in isolation
- **Speed**: < 1 second each
- **Dependencies**: All external dependencies mocked (database, files, APIs)
- **Focus**: Logic validation, data transformation, calculations

#### Integration Tests (`tests/integration/`) - **NO MOCKING ALLOWED**
- **Purpose**: Test interaction between components (database + code + external services)
- **Speed**: < 5 seconds each
- **Dependencies**: **REAL DATABASE + REAL EXTERNAL SERVICES** (WebDAV, file systems, etc.)
- **Focus**: Database operations, ORM relationships, transaction handling, file operations
- **❌ CRITICAL RULE: NO MOCKING IN INTEGRATION TESTS**
  - Integration tests MUST use real PostgreSQL database operations
  - Integration tests MUST use real WebDAV file operations (when available)
  - Integration tests MUST test actual service integrations
  - If external service unavailable, test should SKIP (not mock)
  - Only acceptable to mock: network timeouts, system failures for error testing

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

### 3. Integration Test Requirements (MANDATORY)

#### **NO MOCKING RULE FOR INTEGRATION TESTS**
Integration tests in `tests/integration/` MUST follow these strict requirements:

1. **REAL DATABASE OPERATIONS ONLY**
   - Use actual PostgreSQL database with `component_app` schema
   - Test real database triggers, constraints, and relationships
   - Test real transaction rollbacks and commits
   - Test real foreign key constraints and cascade operations

2. **REAL EXTERNAL SERVICE OPERATIONS**
   - Use real WebDAV server: `http://31.182.67.115/webdav/components`
   - Test actual file upload, delete, move operations
   - Test real network timeouts and connectivity issues
   - If WebDAV unavailable, use `pytest.skip()` - DO NOT MOCK
   - **🚨 CRITICAL SAFETY RULE: ONLY manipulate files in `http://31.182.67.115/webdav/components`**
     - NEVER access or modify files outside this specific directory
     - NEVER test on production file systems or other WebDAV paths
     - ALL file operations must be scoped to the components directory only

3. **REAL COMPONENT SERVICE INTEGRATION**
   - Test ComponentService with all real dependencies
   - Test picture renaming with actual file operations
   - Test SKU generation with real database interactions
   - Test error handling with real service failures

4. **ACCEPTABLE EXCEPTIONS (LIMITED)**
   - Only mock system-level failures for error testing
   - Only mock network timeouts for resilience testing
   - Never mock business logic or database operations
   - Never mock file operations or storage services

#### **Example Integration Test Structure**
```python
def test_should_rename_pictures_when_product_number_changes(self, component_service, test_data):
    """REAL integration test - no mocking allowed"""
    # Create real component in database
    component = Component(...)
    db.session.add(component)
    db.session.flush()
    
    # Upload real file to WebDAV
    upload_result = component_service.upload_picture_to_webdav(real_file_data, filename)
    if not upload_result['success']:
        pytest.skip("WebDAV not available for real integration test")
    
    # Test real product number change with real file renaming
    result = component_service.update_component(component.id, {'product_number': 'NEW-NAME'})
    
    # Verify real database was updated
    assert Component.query.get(component.id).product_number == 'NEW-NAME'
    
    # Verify real file was renamed on WebDAV
    # ... check actual file exists with new name
```

### 4. Test Organization Rules (CRITICAL)
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

### 5. BDD/Gherkin Test Organization (FOR ALL TEST LEVELS)

#### **Gherkin Feature Files**
All test scenarios should have corresponding Gherkin documentation (not just Selenium):

```gherkin
# tests/selenium/features/component_creation.feature
Feature: Component Creation
  As a product manager
  I want to create new components
  So that I can manage our product catalog

  Background:
    Given I am logged in as an admin
    And I am on the component creation page

  Scenario: Create component with all required fields
    When I fill in "Product Number" with "TEST-001"
    And I select "Supplier" as "Nike"
    And I select "Component Type" as "Shirt"
    And I fill in "Description" with "Test component"
    And I click "Create Component"
    Then I should see "Component created successfully"
    And the component "TEST-001" should exist in the database

  Scenario: Create component with variants and pictures
    When I create a component "SHIRT-001"
    And I add a "Red" variant with picture "red_shirt.jpg"
    And I add a "Blue" variant with picture "blue_shirt.jpg"
    Then both variant pictures should be visible immediately
    And the pictures should have correct naming convention
```

#### **Step Definitions Organization**
```python
# tests/selenium/features/step_definitions/component_steps.py
from behave import given, when, then
from tests.selenium.pages import ComponentCreationPage

@given('I am on the component creation page')
def step_impl(context):
    context.page = ComponentCreationPage(context.driver)
    context.page.load()

@when('I fill in "{field}" with "{value}"')
def step_impl(context, field, value):
    context.page.fill_field(field, value)
```

### 6. Test Documentation Standards (MANDATORY)

#### **Test Method Naming Convention**

**REQUIRED FORMAT: Use `test_should_<expected_behavior>_when_<context>` pattern**

This is the most readable and self-documenting format for test method names that works with unittest/pytest discovery.

```python
# ✅ CORRECT: Clear, descriptive naming
def test_should_save_component_successfully_when_valid_input():
    """
    Test: Component creation with valid data
    Given: Valid component data with all required fields
    When: Component is saved via service layer
    Then: Component should be saved successfully with auto-generated ID
    """

def test_should_throw_validation_error_when_product_number_is_empty():
    """
    Test: Product number validation
    Given: Component data with empty product_number
    When: Component creation is attempted
    Then: ValidationError should be raised with appropriate message
    """

def test_should_return_empty_list_when_no_components_in_database():
    """
    Test: Query behavior with empty database
    Given: Database with no components
    When: get_all_components() is called
    Then: Empty list should be returned
    """
```

**NAMING RULES (MANDATORY):**

1. **Use `test_should_<expected_behavior>_when_<condition>` format**
2. **Method names must be written in `snake_case` (Python standard)**
3. **Be specific and descriptive, reflecting what is being tested**
4. **Avoid generic names like `test1` or `check_something`**
5. **Prefer clarity over brevity, but avoid overly long names**
6. **Include both success and failure scenarios in naming**

**ALTERNATIVE FORMAT (BDD-style, optional):**
```python
def given_user_with_valid_data_when_saving_then_success():
    """BDD-style naming acceptable for behavior-driven tests"""

def given_empty_cart_when_checkout_then_throw_exception():
    """Clear given-when-then structure"""
```

**❌ BAD EXAMPLES (NEVER USE):**
```python
def test1():                           # Too vague
def check_login():                     # Unclear what's being checked
def validate_something():              # Too generic
def Should_Return_User_When_Exists():  # Wrong case convention
def testComponentCreation():           # Unclear what aspect is tested
```

**✅ GOOD EXAMPLES:**
```python
def test_should_generate_correct_sku_when_supplier_exists():
def test_should_rename_all_pictures_when_product_number_changes():
def test_should_not_allow_duplicate_product_numbers_when_creating_component():
def test_should_handle_large_file_upload_when_generating_picture():
def test_should_return_404_when_component_not_found():
```

#### **Example Test Documentation**
```python
class TestComponentService:
    """All tests for ComponentService functionality"""
    
    def test_update_component_with_product_number_change_renames_all_pictures(self):
        """
        Test: Product number change triggers picture renaming in WebDAV
        Given: Component exists with product_number "OLD-001" and 3 pictures
        When: Product number is changed to "NEW-001"
        Then: All 3 pictures are renamed in WebDAV from OLD-001_*.jpg to NEW-001_*.jpg
        """
        # Test implementation
        
    def test_update_component_with_invalid_data_raises_validation_error(self):
        """
        Test: Invalid component data raises appropriate validation error
        Given: Component exists with ID 123
        When: Update is attempted with empty product_number
        Then: ValidationError is raised with message "Product number is required"
        """
        # Test implementation
```

#### **Test Class Organization**
```python
# tests/unit/services/test_component_service.py
class TestComponentServiceCreation:
    """Tests for component creation functionality"""
    # All creation-related tests here
    
class TestComponentServiceUpdate:
    """Tests for component update functionality"""
    # All update-related tests here
    
class TestComponentServiceDeletion:
    """Tests for component deletion functionality"""
    # All deletion-related tests here
    
class TestComponentServicePictureHandling:
    """Tests for picture management functionality"""
    # All picture-related tests here
```

### 7. Testing Rules (NON-NEGOTIABLE)
1. **NO TEMPORARY TESTS IN ROOT**: All tests must be in `tests/` folder with proper organization
2. **NO BROKEN TESTS**: Failing tests must be fixed immediately, not ignored
3. **NO DEVELOPMENT ON RED**: Do not write new code when tests are failing
4. **CLEAN TEST CODE**: Tests must be maintainable and well-organized
5. **TEST COVERAGE**: New features require corresponding tests
6. **ISOLATION**: Tests must not depend on each other or external state
7. **ONE FILE PER SERVICE**: All tests for a service must be in ONE file with clear test classes
8. **DESCRIPTIVE TEST NAMES**: Every test must clearly describe action, context, and expected result

### 8. Test Failure Protocol (MANDATORY)
When tests fail:
1. **STOP ALL DEVELOPMENT WORK**
2. **Analyze the failure** - read the error messages carefully
3. **Fix the root cause** - don't just make tests pass artificially
4. **Run full test suite** - ensure fix doesn't break other tests
5. **Only then continue** with planned development work

---

## 🔴 TDD (Test-Driven Development) Rules

### **TDD Principles for This Project**
TDD is a **technical methodology** focused on code quality and design through the Red-Green-Refactor cycle.

#### **1. TDD Workflow (MANDATORY)**
```
RED → GREEN → REFACTOR
```

**RED Phase:**
- Write a **failing test first** that describes the desired behavior
- Test must **fail for the right reason** (functionality doesn't exist yet)
- Test should be **minimal and focused** on one specific behavior
- Run test to **confirm it fails**

**GREEN Phase:**
- Write **minimal code** to make the test pass
- Don't optimize yet - just make it work
- Code can be ugly but must pass the test
- Run test to **confirm it passes**

**REFACTOR Phase:**
- Improve code quality while keeping tests green
- Remove duplication, improve naming, optimize
- **Run tests frequently** during refactoring
- Tests must **remain green** throughout

#### **2. TDD Test Categories**

**Unit Tests (TDD Focus):**
```python
class TestComponentServiceSKUGeneration:
    def test_generate_sku_with_supplier_creates_correct_format(self):
        """
        Test: SKU generation with supplier
        Given: Supplier "NIKE", product "SHIRT-001", color "RED"
        When: SKU is generated
        Then: Result should be "NIKE_SHIRT-001_RED"
        """
        # RED: Test fails - method doesn't exist
        result = ComponentService.generate_sku("NIKE", "SHIRT-001", "RED")
        assert result == "NIKE_SHIRT-001_RED"
```

**Integration Tests (TDD for Data Flow):**
```python
def test_component_creation_generates_variant_skus_in_database(self):
    """
    Test: Database triggers generate SKUs during component creation
    Given: Component data with 2 variants
    When: Component is created in database
    Then: Both variants should have auto-generated SKUs
    """
    # Test database integration with TDD cycle
```

#### **3. TDD Rules for This Project**

1. **Write Test First**: No production code without failing test
2. **One Test at a Time**: Focus on single failing test until green
3. **Minimal Implementation**: Write only enough code to pass current test
4. **Fast Feedback**: Tests should run quickly (< 1 second each)
5. **Isolated Tests**: No dependencies between tests
6. **Descriptive Names**: Test names describe behavior, not implementation

#### **4. TDD Implementation Patterns**

**Dependency Injection for Testing:**
```python
class ComponentService:
    def __init__(self, storage_service=None, db_session=None):
        self.storage = storage_service or default_storage
        self.db = db_session or default_db
```

**Mock External Dependencies:**
```python
@patch('app.services.component_service.webdav_client')
def test_picture_upload_calls_webdav_correctly(self, mock_webdav):
    mock_webdav.upload.return_value = {'success': True}
    service = ComponentService()
    
    result = service.upload_picture(file_data, 'test.jpg')
    
    mock_webdav.upload.assert_called_once_with(file_data, 'test.jpg')
    assert result['success'] is True
```

---

## 🎯 BDD (Behavior-Driven Development) Rules

### **BDD Principles for This Project**
BDD is a **collaboration methodology** focused on business behavior and requirements using natural language.

#### **1. BDD Three Amigos Approach**
- **Developer**: Technical implementation perspective
- **Tester**: Quality and edge case perspective  
- **Business**: Requirements and user value perspective

#### **2. BDD Gherkin Structure (MANDATORY)**

**Feature Files Organization:**
```
tests/selenium/features/
├── component_lifecycle.feature
├── picture_management.feature
├── variant_management.feature
├── status_workflow.feature
└── brand_associations.feature
```

**Gherkin Syntax Rules:**
```gherkin
Feature: [Business Value Statement]
  As a [role]
  I want [functionality]
  So that [business benefit]

  Background:
    Given [common setup for all scenarios]

  Scenario: [Specific business scenario]
    Given [initial context]
    When [action taken]
    Then [expected outcome]
    And [additional verification]

  Scenario Outline: [Template for multiple scenarios]
    Given [context with "<placeholder>"]
    When [action with "<placeholder>"]
    Then [outcome with "<placeholder>"]
    
    Examples:
      | placeholder1 | placeholder2 |
      | value1      | value2      |
```

#### **3. BDD Scenario Categories**

**Critical Path Scenarios:**
```gherkin
Feature: Component Creation
  As a product manager
  I want to create components with variants
  So that I can manage our product catalog

  Scenario: Create component with multiple variants
    Given I am logged in as a product manager
    When I create component "SHIRT-001" with colors "Red, Blue, Green"
    Then 3 variants should be created with unique SKUs
    And each variant should be visible in the component list
```

**Error Handling Scenarios:**
```gherkin
Feature: Component Validation
  Scenario: Duplicate product number rejection
    Given a component "SHIRT-001" already exists
    When I try to create another component "SHIRT-001"
    Then I should see error "Product number already exists"
    And the component should not be created
```

**Integration Scenarios:**
```gherkin
Feature: Picture Management
  Scenario: Product number change renames pictures
    Given component "OLD-001" has 3 pictures
    When I change product number to "NEW-001"
    Then all 3 pictures should be renamed with "NEW-001"
    And old picture files should be deleted from WebDAV
```

#### **4. BDD Step Definition Patterns**

**Reusable Step Definitions:**
```python
# features/steps/component_steps.py
@given('component "{product_number}" has {count:d} pictures')
def step_component_has_pictures(context, product_number, count):
    context.component = create_test_component(product_number)
    context.pictures = []
    for i in range(count):
        picture = create_test_picture(context.component, f"{product_number}_{i}.jpg")
        context.pictures.append(picture)

@when('I change product number to "{new_product_number}"')
def step_change_product_number(context, new_product_number):
    response = ComponentService.update_component(
        context.component.id,
        {'product_number': new_product_number}
    )
    context.response = response

@then('all {count:d} pictures should be renamed with "{product_number}"')
def step_pictures_renamed(context, count, product_number):
    updated_component = Component.query.get(context.component.id)
    for picture in updated_component.pictures:
        assert product_number.lower() in picture.picture_name.lower()
```

#### **5. BDD Test Levels**

**Unit Level BDD (Business Logic):**
```gherkin
Feature: SKU Generation Logic
  Scenario: SKU with supplier
    Given supplier "NIKE", product "SHIRT", color "RED"
    When SKU is generated
    Then result should be "NIKE_SHIRT_RED"
```

**API Level BDD (Service Integration):**
```gherkin
Feature: Component API
  Scenario: Create component via API
    Given valid component data
    When I POST to "/api/components"
    Then response status should be 201
    And response should contain component ID
```

**E2E Level BDD (User Workflows):**
```gherkin
Feature: Component Management Workflow
  Scenario: Complete component creation workflow
    Given I am on the component creation page
    When I fill all required fields and submit
    Then I should see "Component created successfully"
    And the component should appear in the list
```

---

## 🔄 TDD + BDD Integration Rules

### **How TDD and BDD Work Together**

#### **1. Outside-In Development Process**
```
BDD (Requirements) → TDD (Implementation)
```

**Step 1: BDD Defines WHAT to Build**
```gherkin
Scenario: Component picture renaming
  Given component with 3 pictures
  When product number changes
  Then pictures should be renamed
```

**Step 2: TDD Defines HOW to Build It**
```python
# RED: Write failing test
def test_rename_pictures_updates_webdav_files():
    assert False  # Not implemented yet

# GREEN: Minimal implementation
def rename_pictures(component):
    pass  # Just make test pass

# REFACTOR: Proper implementation
def rename_pictures(component):
    for picture in component.pictures:
        webdav.rename(picture.old_name, picture.new_name)
```

#### **2. Test Pyramid with BDD/TDD**
```
E2E Tests (BDD Selenium)    ←  User Workflows
    ↓
API Tests (BDD + TDD)       ←  Service Integration  
    ↓
Integration Tests (TDD)     ←  Component Integration
    ↓  
Unit Tests (TDD)           ←  Code Quality & Design
```

#### **3. Complementary Practices**

**BDD Provides:**
- Business requirements clarity
- User behavior documentation
- Acceptance criteria
- Living documentation

**TDD Provides:**
- Code quality assurance
- Design guidance
- Regression protection
- Refactoring confidence

#### **4. Non-Contradictory Rules**

**When to Use TDD:**
- ✅ Writing business logic methods
- ✅ Creating utility functions
- ✅ Implementing algorithms (SKU generation, picture naming)
- ✅ Testing error handling code

**When to Use BDD:**
- ✅ Defining user workflows
- ✅ Testing business scenarios
- ✅ Integration testing
- ✅ Acceptance testing

**Both TDD and BDD:**
- ✅ Can test the same functionality at different levels
- ✅ Should follow Given/When/Then structure
- ✅ Must have descriptive test names
- ✅ Should be isolated and repeatable
- ✅ Must maintain high quality standards

#### **5. Workflow Integration Example**

**BDD Scenario (defines requirement):**
```gherkin
Scenario: Auto-generate component SKUs
  Given component with supplier "NIKE" and variants "Red, Blue"
  When component is created
  Then variants should have SKUs "NIKE_COMP_RED, NIKE_COMP_BLUE"
```

**TDD Implementation (implements requirement):**
```python
# RED
def test_generate_sku_formats_correctly():
    result = generate_sku("NIKE", "COMP", "RED")
    assert result == "NIKE_COMP_RED"

# GREEN  
def generate_sku(supplier, product, color):
    return f"{supplier}_{product}_{color}"

# REFACTOR
def generate_sku(supplier_code, product_number, color_name):
    return f"{supplier_code.upper()}_{product_number.upper()}_{color_name.upper()}"
```

### **6. Quality Standards for Both**

**Test Documentation (Both TDD & BDD):**
- Clear Given/When/Then structure
- Descriptive test names explaining behavior
- Business value clearly stated
- Error scenarios covered

**Test Organization (Both TDD & BDD):**
- One file per service/feature
- Logical test class grouping
- Consistent naming conventions
- Proper setup/teardown

**Test Execution (Both TDD & BDD):**
- Fast feedback cycles
- Isolated test execution
- Reliable and repeatable
- Clear failure messages

---

This integration ensures TDD and BDD complement each other without contradiction, providing both technical excellence and business value alignment.

---

## 📊 Test Implementation Standards

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

## Test File Consolidation Requirements (CRITICAL)

### MANDATORY CONSOLIDATION RULES

#### 1. **Component Service Tests**
All tests for `app/services/component_service.py` MUST be in:
- **Unit Tests**: `tests/unit/services/test_component_service.py`
- **Integration Tests**: `tests/integration/services/test_component_service_integration.py`

❌ **DELETE THESE DUPLICATE FILES**:
- `test_component_service_complete.py`
- `test_component_service_comprehensive.py`
- `test_component_lifecycle_complete.py`
- Any other `test_component_*` variations

#### 2. **API Endpoint Tests**
All tests for each API MUST be in ONE file:
- **Component API**: `tests/api/test_component_api.py` (ALL component endpoints)
- **Brand API**: `tests/api/test_brand_api.py` (ALL brand endpoints)
- **Supplier API**: `tests/api/test_supplier_api.py` (ALL supplier endpoints)

❌ **CONSOLIDATE THESE**:
- `test_component_api_simple.py`
- `test_component_crud_endpoints.py`
- `test_component_delete_api.py`
- `test_component_update_endpoint.py`

#### 3. **Picture Management Tests**
All picture-related tests MUST be organized by test type:
- **Unit**: `tests/unit/services/test_component_service.py` (in picture handling class)
- **Integration**: `tests/integration/workflows/test_picture_management.py`
- **API**: `tests/api/test_picture_api.py`
- **Selenium**: `tests/selenium/workflows/test_picture_workflows.py`

#### 4. **Selenium Test Organization**
- **Features**: Use Gherkin files in `tests/selenium/features/`
- **Workflows**: Group related scenarios in single workflow files
- **Pages**: One page object per application page

❌ **AVOID**: Creating 7 different files for component deletion scenarios

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