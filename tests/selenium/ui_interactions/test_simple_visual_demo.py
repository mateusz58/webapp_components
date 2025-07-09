import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestSimpleVisualDemo(unittest.TestCase):
    """Simple visual demonstration of Selenium automation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up visible browser for demonstration"""
        print(f"\n🎬 VISUAL SELENIUM DEMO: Starting visible Chrome browser...")
        
        # Chrome options for VISIBLE testing
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # COMMENTED OUT for visibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--start-maximized")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(5)
            cls.wait = WebDriverWait(cls.driver, 10)
            
            cls.base_url = "http://localhost:6002"
            print(f"✅ Visible browser ready - you can watch the automation!")
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise

    @classmethod 
    def tearDownClass(cls):
        """Clean up browser with delay to see final state"""
        print(f"\n🛑 Closing browser in 3 seconds...")
        time.sleep(3)
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        print(f"✅ Demo complete!")

    def test_visual_navigation_demo(self):
        """Visual demonstration of navigating the application"""
        print(f"\n🎬 VISUAL DEMO: Website navigation")
        
        try:
            # Step 1: Load home page
            print(f"🔍 Step 1: Loading home page...")
            self.driver.get(self.base_url)
            self._add_visual_indicator("Loading home page", "blue")
            time.sleep(2)
            
            # Step 2: Check page title
            title = self.driver.title
            print(f"🔍 Step 2: Page title: '{title}'")
            self._add_visual_indicator(f"Page title: {title}", "green")
            time.sleep(2)
            
            # Step 3: Navigate to components page
            print(f"🔍 Step 3: Navigating to components page...")
            self.driver.get(f"{self.base_url}/components")
            self._add_visual_indicator("Loading components page", "orange")
            time.sleep(2)
            
            # Step 4: Navigate to component creation
            print(f"🔍 Step 4: Navigating to component creation...")
            self.driver.get(f"{self.base_url}/component/new")
            self._add_visual_indicator("Loading component creation form", "purple")
            time.sleep(2)
            
            # Step 5: Find and highlight form elements
            print(f"🔍 Step 5: Finding form elements...")
            try:
                form = self.driver.find_element(By.TAG_NAME, "form")
                self._highlight_element(form, "Component creation form")
                print(f"✅ Form found and highlighted")
                time.sleep(2)
            except NoSuchElementException:
                print(f"⚠️ Form not found on this page")
            
            # Step 6: Find input fields
            print(f"🔍 Step 6: Looking for input fields...")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"Found {len(inputs)} input fields")
            
            for i, input_field in enumerate(inputs[:3]):  # Show first 3
                field_type = input_field.get_attribute('type')
                field_name = input_field.get_attribute('name')
                self._highlight_element(input_field, f"Input {i+1}: {field_type}")
                print(f"   Input {i+1}: type='{field_type}', name='{field_name}'")
                time.sleep(1)
            
            # Step 7: Find buttons
            print(f"🔍 Step 7: Looking for buttons...")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons")
            
            for i, button in enumerate(buttons[:2]):  # Show first 2
                button_text = button.text or button.get_attribute('value') or 'No text'
                self._highlight_element(button, f"Button {i+1}: {button_text}")
                print(f"   Button {i+1}: '{button_text}'")
                time.sleep(1)
            
            self._add_visual_indicator("Navigation demo complete!", "green")
            time.sleep(3)
            
            print(f"✅ VISUAL DEMO PASSED: Navigation complete")
            
        except Exception as e:
            print(f"❌ VISUAL DEMO FAILED: {str(e)}")
            self._add_visual_indicator(f"DEMO FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_visual_form_interaction_demo(self):
        """Visual demonstration of form interactions"""
        print(f"\n🎬 VISUAL DEMO: Form interaction")
        
        try:
            # Navigate to form
            print(f"🔍 Loading component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self._add_visual_indicator("Testing form interactions", "blue")
            time.sleep(2)
            
            # Find and fill product number field
            try:
                print(f"🔍 Looking for product number field...")
                product_field = self.driver.find_element(By.NAME, "product_number")
                self._highlight_element(product_field, "Product number field")
                
                # Clear and type slowly
                product_field.clear()
                test_value = f"VISUAL-DEMO-{int(time.time())}"
                print(f"🔍 Typing: {test_value}")
                self._type_slowly(product_field, test_value)
                time.sleep(1)
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found")
            
            # Find and fill description
            try:
                print(f"🔍 Looking for description field...")
                desc_field = self.driver.find_element(By.NAME, "description")
                self._highlight_element(desc_field, "Description field")
                
                desc_field.clear()
                desc_text = "Visual Selenium demonstration component"
                print(f"🔍 Typing description...")
                self._type_slowly(desc_field, desc_text, speed=0.05)
                time.sleep(1)
                
            except NoSuchElementException:
                print(f"⚠️ Description field not found")
            
            # Show window resize demo
            print(f"🔍 Demonstrating responsive design...")
            
            # Desktop view
            self.driver.set_window_size(1200, 800)
            self._add_visual_indicator("Desktop view (1200x800)", "blue")
            time.sleep(2)
            
            # Tablet view
            self.driver.set_window_size(768, 1024)
            self._add_visual_indicator("Tablet view (768x1024)", "orange")
            time.sleep(2)
            
            # Mobile view
            self.driver.set_window_size(375, 667)
            self._add_visual_indicator("Mobile view (375x667)", "red")
            time.sleep(2)
            
            # Back to desktop
            self.driver.set_window_size(1200, 800)
            self._add_visual_indicator("Back to desktop view", "green")
            time.sleep(2)
            
            self._add_visual_indicator("Form interaction demo complete!", "green")
            time.sleep(3)
            
            print(f"✅ VISUAL DEMO PASSED: Form interaction complete")
            
        except Exception as e:
            print(f"❌ VISUAL DEMO FAILED: {str(e)}")
            self._add_visual_indicator(f"DEMO FAILED: {str(e)}", "red")
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
                    max-width: 300px;
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
                arguments[0].style.border = '4px solid red';
                arguments[0].style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
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
    🎬 SIMPLE VISUAL SELENIUM DEMO
    
    This will run a simple visual demonstration with a visible browser.
    You can watch the automation happening in real-time!
    
    To run: python -m pytest tests/selenium/test_simple_visual_demo.py -v -s
    """)
    
    unittest.main()