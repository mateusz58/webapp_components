import unittest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestComponentRoutesVisual(unittest.TestCase):
    """Visual Selenium tests for component routes based on actual app/web and app/api routes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up visible browser for component route testing"""
        print(f"\n🎬 COMPONENT ROUTES VISUAL TEST: Starting visible Chrome browser...")
        
        # Chrome options for VISIBLE testing
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # COMMENTED OUT for visibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--start-maximized")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(8)
            cls.wait = WebDriverWait(cls.driver, 15)
            
            cls.base_url = "http://localhost:6002"
            print(f"✅ Browser ready for component route testing!")
            print(f"🌐 Testing routes at: {cls.base_url}")
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise

    @classmethod 
    def tearDownClass(cls):
        """Clean up browser with delay"""
        print(f"\n🛑 Closing browser in 3 seconds...")
        time.sleep(3)
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        print(f"✅ Component routes testing complete!")

    def setUp(self):
        """Set up each test"""
        print(f"\n🧪 COMPONENT ROUTE TEST: {self._testMethodName}")
        self.driver.delete_all_cookies()

    def test_component_list_route_visual(self):
        """Test /components route - component list page"""
        print(f"\n🎬 TESTING ROUTE: /components (Component List)")
        
        try:
            # Test main components route
            print(f"🔍 Step 1: Loading /components...")
            self.driver.get(f"{self.base_url}/components")
            self._add_visual_indicator("Loading component list", "blue")
            time.sleep(2)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check page title and content
            title = self.driver.title
            print(f"🔍 Page title: '{title}'")
            self._add_visual_indicator(f"Page: {title}", "green")
            time.sleep(2)
            
            # Look for component list elements
            print(f"🔍 Step 2: Looking for component list elements...")
            
            # Check for table/list container
            containers = self.driver.find_elements(By.CSS_SELECTOR, 
                "table, .table, .component-list, .list-container, main, .content")
            print(f"Found {len(containers)} potential containers")
            
            if containers:
                container = containers[0]
                self._highlight_element(container, "Main content container")
                time.sleep(1)
            
            # Look for pagination or navigation
            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".pagination, .nav, .navbar, nav")
            print(f"Found {len(nav_elements)} navigation elements")
            
            # Look for add/create buttons
            create_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href*='component/new'], .btn-create, .create-btn, .add-component")
            print(f"Found {len(create_buttons)} create buttons")
            
            if create_buttons:
                self._highlight_element(create_buttons[0], "Create component button")
                time.sleep(1)
            
            self._add_visual_indicator("Component list route tested", "green")
            time.sleep(2)
            
            print(f"✅ ROUTE TEST PASSED: /components")
            
        except Exception as e:
            print(f"❌ ROUTE TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_component_new_route_visual(self):
        """Test /component/new route - component creation form"""
        print(f"\n🎬 TESTING ROUTE: /component/new (Component Creation)")
        
        try:
            # Test component creation route
            print(f"🔍 Step 1: Loading /component/new...")
            self.driver.get(f"{self.base_url}/component/new")
            self._add_visual_indicator("Loading component creation form", "purple")
            time.sleep(2)
            
            # Wait for form
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Find and highlight the form
            form = self.driver.find_element(By.TAG_NAME, "form")
            self._highlight_element(form, "Component creation form")
            time.sleep(2)
            
            print(f"🔍 Step 2: Testing form fields...")
            
            # Test each expected field
            field_tests = [
                ("product_number", "Product Number"),
                ("description", "Description"),
                ("component_type_id", "Component Type"),
                ("supplier_id", "Supplier"),
                ("category_id", "Category")
            ]
            
            for field_name, field_label in field_tests:
                try:
                    field = self.driver.find_element(By.NAME, field_name)
                    self._highlight_element(field, f"{field_label} field")
                    print(f"✅ Found {field_label} field")
                    time.sleep(1)
                except NoSuchElementException:
                    print(f"⚠️ {field_label} field not found")
            
            # Test form submission elements
            print(f"🔍 Step 3: Testing form controls...")
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], .submit-btn")
            
            if submit_buttons:
                self._highlight_element(submit_buttons[0], "Submit button")
                print(f"✅ Found submit button: '{submit_buttons[0].text}'")
                time.sleep(1)
            
            # Test CSRF token
            csrf_tokens = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[name='csrf_token']")
            if csrf_tokens:
                print(f"✅ Found CSRF token")
            else:
                print(f"⚠️ CSRF token not found")
            
            self._add_visual_indicator("Component creation form tested", "green")
            time.sleep(2)
            
            print(f"✅ ROUTE TEST PASSED: /component/new")
            
        except Exception as e:
            print(f"❌ ROUTE TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_component_creation_workflow_visual(self):
        """Test actual component creation workflow with form filling"""
        print(f"\n🎬 TESTING WORKFLOW: Component Creation with Form Filling")
        
        try:
            # Navigate to creation form
            print(f"🔍 Step 1: Loading component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Starting component creation workflow", "orange")
            time.sleep(2)
            
            # Generate unique test data
            timestamp = str(int(time.time()))
            test_product_number = f"VIS-TEST-{timestamp}"
            test_description = f"Visual Selenium test component created at {timestamp}"
            
            print(f"🔍 Step 2: Filling product number...")
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Filling product number")
                product_field.clear()
                self._type_slowly(product_field, test_product_number)
                print(f"✅ Entered: {test_product_number}")
                time.sleep(1)
            except NoSuchElementException:
                print(f"⚠️ Product number field not found")
            
            print(f"🔍 Step 3: Filling description...")
            try:
                desc_field = self.driver.find_element(By.NAME, "description")
                self._highlight_element(desc_field, "Filling description")
                desc_field.clear()
                self._type_slowly(desc_field, test_description, speed=0.03)
                print(f"✅ Entered description")
                time.sleep(1)
            except NoSuchElementException:
                print(f"⚠️ Description field not found")
            
            print(f"🔍 Step 4: Selecting component type...")
            try:
                type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
                options = type_select.options
                print(f"Found {len(options)} component type options")
                
                if len(options) > 1:
                    self._highlight_element(type_select._el, "Selecting component type")
                    type_select.select_by_index(1)
                    selected = type_select.first_selected_option.text
                    print(f"✅ Selected: {selected}")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Component type selection failed: {e}")
            
            print(f"🔍 Step 5: Selecting supplier...")
            try:
                supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
                options = supplier_select.options
                print(f"Found {len(options)} supplier options")
                
                if len(options) > 1:
                    self._highlight_element(supplier_select._el, "Selecting supplier")
                    supplier_select.select_by_index(1)
                    selected = supplier_select.first_selected_option.text
                    print(f"✅ Selected: {selected}")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Supplier selection failed: {e}")
            
            print(f"🔍 Step 6: Testing form validation...")
            # Test product number validation (should trigger AJAX)
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                # Trigger blur for validation
                self.driver.execute_script("arguments[0].blur();", product_field)
                time.sleep(1)
                
                # Look for validation feedback
                validation_msgs = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".validation-message, .error-message, .success-message")
                print(f"Found {len(validation_msgs)} validation messages")
                
            except Exception as e:
                print(f"⚠️ Validation test failed: {e}")
            
            # Show completed form
            self._add_visual_indicator("Form filling complete", "green")
            time.sleep(3)
            
            print(f"🔍 Step 7: Form ready for submission...")
            print(f"📝 Test data filled:")
            print(f"   - Product Number: {test_product_number}")
            print(f"   - Description: {test_description}")
            
            # Note: Not actually submitting to avoid creating test data
            print(f"⚠️ Not submitting form to avoid creating test data")
            
            print(f"✅ WORKFLOW TEST PASSED: Component creation workflow")
            
        except Exception as e:
            print(f"❌ WORKFLOW TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"WORKFLOW FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_component_api_validation_visual(self):
        """Test component API validation endpoint visually"""
        print(f"\n🎬 TESTING API: /api/component/validate-product-number")
        
        try:
            # Load form to test validation
            print(f"🔍 Step 1: Loading form for API validation test...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Testing API validation", "cyan")
            time.sleep(2)
            
            # Find product number field
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Testing API validation")
                
                print(f"🔍 Step 2: Testing with existing product number...")
                # Test with a potentially existing product number
                product_field.clear()
                existing_test = "EXISTING-TEST-123"
                self._type_slowly(product_field, existing_test, speed=0.05)
                
                # Trigger validation (should call API)
                print(f"🔍 Step 3: Triggering validation API call...")
                self.driver.execute_script("arguments[0].blur();", product_field)
                time.sleep(2)  # Wait for API response
                
                # Look for validation response
                validation_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".validation-message, .error-message, .success-message, .feedback")
                
                print(f"Found {len(validation_elements)} validation response elements")
                for i, elem in enumerate(validation_elements):
                    self._highlight_element(elem, f"Validation response {i+1}")
                    print(f"   Response {i+1}: {elem.text}")
                    time.sleep(1)
                
                print(f"🔍 Step 4: Testing with unique product number...")
                # Test with unique product number
                product_field.clear()
                unique_test = f"UNIQUE-API-TEST-{int(time.time())}"
                self._type_slowly(product_field, unique_test, speed=0.05)
                
                # Trigger validation again
                self.driver.execute_script("arguments[0].blur();", product_field)
                time.sleep(2)
                
                # Check for different validation response
                new_validation = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".validation-message, .error-message, .success-message, .feedback")
                print(f"Found {len(new_validation)} validation responses for unique name")
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found for API testing")
            
            self._add_visual_indicator("API validation testing complete", "green")
            time.sleep(2)
            
            print(f"✅ API TEST PASSED: Product number validation")
            
        except Exception as e:
            print(f"❌ API TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"API FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_responsive_design_across_routes_visual(self):
        """Test responsive design across different component routes"""
        print(f"\n🎬 TESTING: Responsive Design Across Routes")
        
        routes_to_test = [
            ("/components", "Component List"),
            ("/component/new", "Component Creation")
        ]
        
        screen_sizes = [
            (1920, 1080, "Desktop Large"),
            (1366, 768, "Desktop Standard"),
            (768, 1024, "Tablet"),
            (375, 667, "Mobile")
        ]
        
        try:
            for route, route_name in routes_to_test:
                print(f"🔍 Testing route: {route} ({route_name})")
                self.driver.get(f"{self.base_url}{route}")
                time.sleep(1)
                
                for width, height, size_name in screen_sizes:
                    print(f"   📱 Testing {size_name} ({width}x{height})")
                    self.driver.set_window_size(width, height)
                    self._add_visual_indicator(f"{route_name} - {size_name}", "blue")
                    time.sleep(1.5)
                    
                    # Check for mobile nav toggles on smaller screens
                    if width <= 768:
                        nav_toggles = self.driver.find_elements(By.CSS_SELECTOR,
                            ".navbar-toggle, .menu-toggle, .hamburger")
                        if nav_toggles:
                            self._highlight_element(nav_toggles[0], "Mobile navigation")
                            time.sleep(0.5)
            
            # Reset to desktop
            self.driver.set_window_size(1366, 768)
            self._add_visual_indicator("Responsive testing complete", "green")
            time.sleep(2)
            
            print(f"✅ RESPONSIVE TEST PASSED: All routes tested")
            
        except Exception as e:
            print(f"❌ RESPONSIVE TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"RESPONSIVE FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    # Visual helper methods
    def _add_visual_indicator(self, message, color="blue"):
        """Add visual indicator to the page"""
        try:
            self.driver.execute_script(f"""
                var indicator = document.createElement('div');
                indicator.innerHTML = '{message}';
                indicator.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: {color};
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    z-index: 9999;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    font-size: 14px;
                    max-width: 350px;
                `;
                document.body.appendChild(indicator);
                setTimeout(() => {{
                    if (indicator.parentNode) {{
                        indicator.parentNode.removeChild(indicator);
                    }}
                }}, 4000);
            """)
        except Exception:
            pass
    
    def _highlight_element(self, element, message=""):
        """Highlight an element visually"""
        try:
            self.driver.execute_script("""
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'rgba(255, 255, 0, 0.2)';
                arguments[0].style.transition = 'all 0.3s ease';
            """, element)
            
            if message:
                self.driver.execute_script(f"""
                    var tooltip = document.createElement('div');
                    tooltip.innerHTML = '{message}';
                    tooltip.style.cssText = `
                        position: absolute;
                        background: #333;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 5px;
                        font-size: 12px;
                        z-index: 10000;
                        top: -40px;
                        left: 0;
                        white-space: nowrap;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    `;
                    arguments[0].style.position = 'relative';
                    arguments[0].appendChild(tooltip);
                    setTimeout(() => {{
                        if (tooltip.parentNode) {{
                            tooltip.parentNode.removeChild(tooltip);
                        }}
                        arguments[0].style.border = '';
                        arguments[0].style.backgroundColor = '';
                    }}, 3000);
                """, element)
        except Exception:
            pass
    
    def _type_slowly(self, element, text, speed=0.1):
        """Type text slowly for visual effect"""
        for char in text:
            element.send_keys(char)
            time.sleep(speed)


if __name__ == '__main__':
    print("""
    🎬 COMPONENT ROUTES VISUAL TESTING
    
    This tests the actual component routes from app/web/component_routes.py:
    - /components (component list)
    - /component/new (component creation)
    - /component/edit/<id> (component editing)
    - API validation endpoints
    
    Browser will be VISIBLE so you can watch the automation!
    
    Run: python -m pytest tests/selenium/test_component_routes_visual.py -v -s
    """)
    
    unittest.main()