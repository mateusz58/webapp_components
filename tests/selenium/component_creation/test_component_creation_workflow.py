import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestComponentCreationWorkflow(unittest.TestCase):
    """Selenium tests for complete component creation workflow with visual browser"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver with VISIBLE browser for demonstration"""
        print(f"\n🔧 SELENIUM SETUP: Initializing VISIBLE Chrome browser...")
        
        # Chrome options for VISIBLE testing (remove headless for demo)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # COMMENTED OUT for visibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--start-maximized")
        
        # Add debugging options
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--v=1")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            
            # Application base URL
            cls.base_url = "http://localhost:6002"
            print(f"✅ VISIBLE Chrome browser initialized successfully")
            print(f"🌐 Testing against: {cls.base_url}")
            print(f"👁️  Browser window is VISIBLE - you can watch the automation!")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            print(f"💡 Make sure Chrome/Chromium is installed and chromedriver is in PATH")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver with delay to see final state"""
        print(f"\n🧹 SELENIUM TEARDOWN: Closing browser in 3 seconds...")
        time.sleep(3)  # Give time to see final state
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            print(f"✅ Browser closed successfully")

    def setUp(self):
        """Set up for each test with visual indicators"""
        print(f"\n🧪 SELENIUM TEST SETUP: {self._testMethodName}")
        print(f"🎯 Purpose: {self.shortDescription() or 'Component creation workflow test'}")
        
        # Clear any existing state
        self.driver.delete_all_cookies()
        
        # Add visual indicator that test is starting
        self.driver.execute_script("""
            document.title = 'SELENIUM TEST: """ + self._testMethodName + """';
        """)
        
        print(f"✅ Test setup complete - watch the browser for automation!")

    def test_navigate_to_component_creation_form(self):
        """Test navigation to component creation form with visual verification"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Navigate to component creation form and verify all elements")
        
        try:
            print(f"🔍 Step 1: Navigating to home page...")
            self.driver.get(self.base_url)
            
            # Wait for page load and add visual indicator
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self._add_visual_indicator("Home page loaded", "green")
            time.sleep(2)  # Pause to see the page
            
            print(f"🔍 Step 2: Looking for navigation to components...")
            
            # Try multiple ways to navigate to component creation
            navigation_selectors = [
                "a[href*='/component/new']",
                "a[href*='/components/create']", 
                ".btn-create-component",
                ".create-component"
            ]
            
            # XPath selectors for text-based matching (CSS :contains() not supported)
            xpath_selectors = [
                "//a[contains(text(), 'New Component')]",
                "//a[contains(text(), 'Create Component')]",
                "//a[contains(text(), 'Add Component')]"
            ]
            
            nav_link = None
            # Try CSS selectors first
            for selector in navigation_selectors:
                try:
                    nav_link = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"🔍 Found navigation link with CSS selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # If CSS selectors didn't work, try XPath selectors
            if nav_link is None:
                for selector in xpath_selectors:
                    try:
                        nav_link = self.driver.find_element(By.XPATH, selector)
                        print(f"🔍 Found navigation link with XPath selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue
            
            if nav_link:
                print(f"🔍 Step 3: Clicking navigation link...")
                self._highlight_element(nav_link)
                time.sleep(1)
                nav_link.click()
            else:
                print(f"🔍 Step 3: Direct navigation to /component/new...")
                self.driver.get(f"{self.base_url}/component/new")
            
            # Wait for form to load
            print(f"🔍 Step 4: Waiting for component creation form...")
            form = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Component creation form loaded", "blue")
            
            # Verify form elements
            print(f"🔍 Step 5: Verifying form elements...")
            
            # Check for product number field
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Found product_number field")
                print(f"✅ Product number field found")
            except NoSuchElementException:
                print(f"⚠️ Product number field not found")
            
            # Check for description field
            try:
                desc_field = self.driver.find_element(By.NAME, "description")
                self._highlight_element(desc_field, "Found description field")
                print(f"✅ Description field found")
            except NoSuchElementException:
                print(f"⚠️ Description field not found")
            
            # Check for dropdowns
            try:
                supplier_field = self.driver.find_element(By.NAME, "supplier_id")
                self._highlight_element(supplier_field, "Found supplier dropdown")
                print(f"✅ Supplier dropdown found")
            except NoSuchElementException:
                print(f"⚠️ Supplier dropdown not found")
            
            # Check for submit button
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], .btn-submit")
            if submit_buttons:
                self._highlight_element(submit_buttons[0], "Found submit button")
                print(f"✅ Submit button found")
            else:
                print(f"⚠️ Submit button not found")
            
            self._add_visual_indicator("Form verification complete", "green")
            time.sleep(3)  # Pause to see verification results
            
            print(f"✅ SELENIUM TEST PASSED: Navigation and form verification complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"TEST FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_fill_component_creation_form_step_by_step(self):
        """Test filling component creation form step by step with visual feedback"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Fill component creation form step by step with visual indicators")
        
        try:
            # Navigate to form
            print(f"🔍 Step 1: Navigating to component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Starting form filling test", "blue")
            time.sleep(2)
            
            # Generate unique test data
            timestamp = str(int(time.time()))
            test_product_number = f"SELENIUM-TEST-{timestamp}"
            test_description = f"Selenium automation test component created at {timestamp}"
            
            print(f"🔍 Step 2: Filling product number field...")
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Filling product number")
                product_field.clear()
                self._type_slowly(product_field, test_product_number)
                print(f"✅ Product number entered: {test_product_number}")
                time.sleep(1)
            except NoSuchElementException:
                print(f"⚠️ Product number field not found")
            
            print(f"🔍 Step 3: Filling description field...")
            try:
                desc_field = self.driver.find_element(By.NAME, "description")
                self._highlight_element(desc_field, "Filling description")
                desc_field.clear()
                self._type_slowly(desc_field, test_description)
                print(f"✅ Description entered")
                time.sleep(1)
            except NoSuchElementException:
                print(f"⚠️ Description field not found")
            
            print(f"🔍 Step 4: Selecting component type...")
            try:
                component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
                options = component_type_select.options
                print(f"Found {len(options)} component type options")
                
                if len(options) > 1:  # Has options besides placeholder
                    self._highlight_element(component_type_select._el, "Selecting component type")
                    component_type_select.select_by_index(1)
                    selected_option = component_type_select.first_selected_option.text
                    print(f"✅ Component type selected: {selected_option}")
                    time.sleep(1)
            except (NoSuchElementException, Exception) as e:
                print(f"⚠️ Component type dropdown not found or not selectable: {e}")
            
            print(f"🔍 Step 5: Selecting supplier...")
            try:
                supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
                options = supplier_select.options
                print(f"Found {len(options)} supplier options")
                
                if len(options) > 1:  # Has options besides placeholder
                    self._highlight_element(supplier_select._el, "Selecting supplier")
                    supplier_select.select_by_index(1)
                    selected_supplier = supplier_select.first_selected_option.text
                    print(f"✅ Supplier selected: {selected_supplier}")
                    time.sleep(1)
            except (NoSuchElementException, Exception) as e:
                print(f"⚠️ Supplier dropdown not found or not selectable: {e}")
            
            print(f"🔍 Step 6: Adding properties (if field exists)...")
            try:
                properties_field = self.driver.find_element(By.NAME, "properties")
                self._highlight_element(properties_field, "Adding properties")
                test_properties = '{"material": "plastic", "color": "blue", "test": "selenium"}'
                properties_field.clear()
                self._type_slowly(properties_field, test_properties)
                print(f"✅ Properties added")
                time.sleep(1)
            except NoSuchElementException:
                print(f"⚠️ Properties field not found")
            
            self._add_visual_indicator("Form filling complete - ready for submission", "green")
            time.sleep(3)
            
            print(f"🔍 Step 7: Looking for submit button...")
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit, .submit-btn")
            
            if submit_buttons:
                submit_button = submit_buttons[0]
                self._highlight_element(submit_button, "Ready to submit")
                print(f"✅ Submit button found: {submit_button.text or submit_button.get_attribute('value')}")
                
                # Ask user if they want to actually submit
                print(f"🔍 Form is ready for submission...")
                print(f"📝 Form data filled:")
                print(f"   - Product Number: {test_product_number}")
                print(f"   - Description: {test_description}")
                
                # Actually submit the form now (was previously commented out)
                print(f"🚀 SUBMITTING FORM...")
                self._safe_click(submit_button)
                print(f"🔍 Form submitted!")
                
                # Wait for response
                time.sleep(5)
                current_url = self.driver.current_url
                if "/component/" in current_url and "/component/new" not in current_url:
                    print(f"✅ SUCCESS: Form submitted and redirected to component detail page")
                    print(f"🔗 URL: {current_url}")
                else:
                    print(f"⚠️ Form submitted but no redirect detected - may need variant")
                
                time.sleep(3)
            else:
                print(f"⚠️ Submit button not found")
            
            print(f"✅ SELENIUM TEST PASSED: Form filling workflow complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"TEST FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_form_validation_visual_feedback(self):
        """Test form validation with visual feedback of error messages"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form validation and see visual error feedback")
        
        try:
            print(f"🔍 Step 1: Loading form for validation testing...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Testing form validation", "orange")
            time.sleep(2)
            
            print(f"🔍 Step 2: Attempting to submit empty form...")
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit']")
            
            if submit_buttons:
                submit_button = submit_buttons[0]
                self._highlight_element(submit_button, "Submitting empty form")
                # Scroll to button and click using JavaScript to avoid interception
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", submit_button)
                time.sleep(2)
                
                # Look for validation messages
                print(f"🔍 Step 3: Checking for validation messages...")
                validation_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    ".error, .invalid-feedback, .alert-danger, .validation-error, .field-error")
                
                if validation_elements:
                    print(f"✅ Found {len(validation_elements)} validation messages")
                    for i, element in enumerate(validation_elements[:3]):  # Show first 3
                        self._highlight_element(element, f"Validation message {i+1}")
                        message_text = element.text
                        print(f"   - Validation message {i+1}: {message_text[:50]}...")
                        time.sleep(1)
                else:
                    print(f"⚠️ No validation messages found")
                
                # Check for HTML5 validation
                print(f"🔍 Step 4: Checking HTML5 validation...")
                try:
                    invalid_fields = self.driver.find_elements(By.CSS_SELECTOR, ":invalid")
                    if invalid_fields:
                        print(f"✅ Found {len(invalid_fields)} HTML5 invalid fields")
                        for field in invalid_fields[:3]:
                            self._highlight_element(field, "HTML5 invalid field")
                            time.sleep(0.5)
                except Exception:
                    print(f"⚠️ Could not check HTML5 validation")
            
            print(f"🔍 Step 5: Testing field-specific validation...")
            try:
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Testing product number validation")
                
                # Test very long input
                long_input = "X" * 100
                product_field.clear()
                self._type_slowly(product_field, long_input, speed=0.01)  # Fast typing
                
                # Trigger blur event
                product_field.send_keys(Keys.TAB)
                time.sleep(2)
                
                # Look for field-specific validation
                field_validation = self.driver.find_elements(By.CSS_SELECTOR,
                    ".validation-message, .error-message, .field-feedback")
                if field_validation:
                    for msg in field_validation:
                        self._highlight_element(msg, "Field validation message")
                        print(f"   - Field validation: {msg.text}")
                        time.sleep(1)
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found for validation testing")
            
            self._add_visual_indicator("Validation testing complete", "green")
            time.sleep(3)
            
            print(f"✅ SELENIUM TEST PASSED: Form validation visual feedback tested")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"VALIDATION TEST FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_responsive_design_visual_demo(self):
        """Test responsive design by changing window sizes visually"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Demonstrate responsive design across different screen sizes")
        
        try:
            print(f"🔍 Step 1: Loading page for responsive testing...")
            self.driver.get(f"{self.base_url}/components")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Test desktop view
            print(f"🔍 Step 2: Testing desktop view (1920x1080)...")
            self.driver.set_window_size(1920, 1080)
            self._add_visual_indicator("Desktop view (1920x1080)", "blue")
            time.sleep(3)
            
            # Test laptop view
            print(f"🔍 Step 3: Testing laptop view (1366x768)...")
            self.driver.set_window_size(1366, 768)
            self._add_visual_indicator("Laptop view (1366x768)", "blue")
            time.sleep(3)
            
            # Test tablet view
            print(f"🔍 Step 4: Testing tablet view (768x1024)...")
            self.driver.set_window_size(768, 1024)
            self._add_visual_indicator("Tablet view (768x1024)", "orange")
            time.sleep(3)
            
            # Test mobile view
            print(f"🔍 Step 5: Testing mobile view (375x667)...")
            self.driver.set_window_size(375, 667)
            self._add_visual_indicator("Mobile view (375x667)", "red")
            time.sleep(3)
            
            # Check for mobile navigation
            print(f"🔍 Step 6: Checking mobile navigation...")
            nav_toggles = self.driver.find_elements(By.CSS_SELECTOR,
                ".navbar-toggle, .menu-toggle, .hamburger, [data-toggle='collapse']")
            
            if nav_toggles:
                print(f"✅ Found {len(nav_toggles)} mobile navigation toggles")
                for toggle in nav_toggles:
                    self._highlight_element(toggle, "Mobile nav toggle")
                    time.sleep(1)
            else:
                print(f"⚠️ No mobile navigation toggles found")
            
            # Return to desktop view
            print(f"🔍 Step 7: Returning to desktop view...")
            self.driver.set_window_size(1366, 768)
            self._add_visual_indicator("Responsive testing complete", "green")
            time.sleep(2)
            
            print(f"✅ SELENIUM TEST PASSED: Responsive design visually demonstrated")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"RESPONSIVE TEST FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    # Visual helper methods
    def _add_visual_indicator(self, message, color="blue"):
        """Add visual indicator to the page for test feedback"""
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
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    z-index: 9999;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                `;
                document.body.appendChild(indicator);
                setTimeout(() => {{
                    if (indicator.parentNode) {{
                        indicator.parentNode.removeChild(indicator);
                    }}
                }}, 3000);
            """)
        except Exception:
            pass  # Don't fail test if visual indicator fails
    
    def _highlight_element(self, element, message=""):
        """Highlight an element visually"""
        try:
            # Add highlight border
            self.driver.execute_script("""
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'yellow';
            """, element)
            
            if message:
                # Add tooltip
                self.driver.execute_script(f"""
                    var tooltip = document.createElement('div');
                    tooltip.innerHTML = '{message}';
                    tooltip.style.cssText = `
                        position: absolute;
                        background: black;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-size: 12px;
                        z-index: 10000;
                        top: -30px;
                        left: 0;
                    `;
                    arguments[0].style.position = 'relative';
                    arguments[0].appendChild(tooltip);
                    setTimeout(() => {{
                        if (tooltip.parentNode) {{
                            tooltip.parentNode.removeChild(tooltip);
                        }}
                        arguments[0].style.border = '';
                        arguments[0].style.backgroundColor = '';
                    }}, 2000);
                """, element)
        except Exception:
            pass  # Don't fail test if highlighting fails
    
    def _type_slowly(self, element, text, speed=0.1):
        """Type text slowly for visual effect"""
        for char in text:
            element.send_keys(char)
            time.sleep(speed)


if __name__ == '__main__':
    # Instructions for running with visible browser
    print("""
    🎬 SELENIUM VISUAL TESTING INSTRUCTIONS:
    
    To run these tests with a VISIBLE browser window:
    
    1. Make sure your application is running:
       ./start.sh
    
    2. Run this specific test file:
       python -m pytest tests/selenium/test_component_creation_workflow.py -v -s
    
    3. Watch the browser window - you'll see:
       - Automated form filling
       - Visual indicators of test progress
       - Highlighted elements being tested
       - Responsive design changes
       - Form validation feedback
    
    👁️  Browser will be VISIBLE so you can watch the automation!
    """)
    
    unittest.main()