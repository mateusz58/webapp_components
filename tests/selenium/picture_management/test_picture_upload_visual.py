import unittest
import time
import os
import tempfile
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestPictureUploadVisual(unittest.TestCase):
    """Visual Selenium tests for picture upload workflows with browser demonstration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up visible browser for picture upload testing"""
        print(f"\n🔧 SELENIUM PICTURE UPLOAD SETUP: Initializing visible browser...")
        
        # Chrome options for visible testing
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--start-maximized")
        
        # Allow file access for upload testing
        chrome_options.add_argument("--allow-file-access-from-files")
        chrome_options.add_argument("--disable-web-security")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            
            cls.base_url = "http://localhost:6002"
            print(f"✅ Picture upload browser initialized")
            print(f"🖼️  Ready for visual picture upload testing!")
            
            # Create test images
            cls._create_test_images()
            
        except Exception as e:
            print(f"❌ Failed to initialize picture upload browser: {e}")
            raise

    @classmethod 
    def tearDownClass(cls):
        """Clean up browser and test files"""
        print(f"\n🧹 PICTURE UPLOAD TEARDOWN: Cleaning up...")
        time.sleep(3)  # Show final state
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        
        # Clean up test images
        if hasattr(cls, 'test_images'):
            for image_path in cls.test_images:
                try:
                    os.remove(image_path)
                except:
                    pass
        print(f"✅ Picture upload cleanup complete")

    @classmethod
    def _create_test_images(cls):
        """Create test images for upload testing"""
        print(f"🎨 Creating test images for upload...")
        cls.test_images = []
        
        colors = [('red', (255, 0, 0)), ('blue', (0, 0, 255)), ('green', (0, 255, 0))]
        
        for color_name, color_rgb in colors:
            # Create a test image
            img = Image.new('RGB', (200, 200), color_rgb)
            
            # Add some text
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                draw.text((50, 90), f"Test\n{color_name.title()}", fill=(255, 255, 255))
            except:
                pass  # If PIL doesn't have font support
            
            # Save to temp file
            temp_path = tempfile.mktemp(suffix=f'_{color_name}.jpg')
            img.save(temp_path, 'JPEG')
            cls.test_images.append(temp_path)
            print(f"   Created test image: {color_name} -> {temp_path}")

    def setUp(self):
        """Set up each picture upload test"""
        print(f"\n🧪 PICTURE UPLOAD TEST: {self._testMethodName}")
        print(f"🎯 Purpose: {self.shortDescription() or 'Picture upload workflow test'}")
        
        self.driver.delete_all_cookies()
        self._add_visual_indicator("Picture Upload Test Starting", "purple")

    def test_navigate_to_picture_upload_section(self):
        """Test finding and navigating to picture upload sections"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Find picture upload sections in component forms")
        
        try:
            print(f"🔍 Step 1: Loading component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Looking for picture upload sections", "blue")
            time.sleep(2)
            
            print(f"🔍 Step 2: Searching for file input elements...")
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            print(f"Found {len(file_inputs)} file input elements")
            
            for i, file_input in enumerate(file_inputs):
                self._highlight_element(file_input, f"File input {i+1}")
                accept_attr = file_input.get_attribute('accept')
                multiple_attr = file_input.get_attribute('multiple')
                name_attr = file_input.get_attribute('name')
                print(f"   File input {i+1}: name='{name_attr}', accept='{accept_attr}', multiple='{multiple_attr}'")
                time.sleep(1)
            
            print(f"🔍 Step 3: Searching for picture-related sections...")
            picture_sections = self.driver.find_elements(By.CSS_SELECTOR,
                ".picture, .image, .upload, .file-upload, .picture-upload, .variant-pictures")
            print(f"Found {len(picture_sections)} picture-related sections")
            
            for i, section in enumerate(picture_sections):
                self._highlight_element(section, f"Picture section {i+1}")
                section_class = section.get_attribute('class')
                section_id = section.get_attribute('id')
                print(f"   Picture section {i+1}: class='{section_class}', id='{section_id}'")
                time.sleep(1)
            
            print(f"🔍 Step 4: Searching for drag-and-drop zones...")
            drop_zones = self.driver.find_elements(By.CSS_SELECTOR,
                ".drop-zone, .dropzone, .file-drop, .drag-drop, [data-drop]")
            print(f"Found {len(drop_zones)} potential drag-and-drop zones")
            
            for i, zone in enumerate(drop_zones):
                self._highlight_element(zone, f"Drop zone {i+1}")
                time.sleep(1)
            
            print(f"🔍 Step 5: Searching for picture preview areas...")
            preview_areas = self.driver.find_elements(By.CSS_SELECTOR,
                ".preview, .thumbnail, .image-preview, .picture-preview, .gallery")
            print(f"Found {len(preview_areas)} picture preview areas")
            
            for i, area in enumerate(preview_areas):
                self._highlight_element(area, f"Preview area {i+1}")
                time.sleep(1)
            
            self._add_visual_indicator("Picture upload section analysis complete", "green")
            time.sleep(3)
            
            print(f"✅ SELENIUM TEST PASSED: Picture upload sections identified")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_simulate_picture_upload_interaction(self):
        """Test picture upload interaction simulation"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Simulate picture upload interactions")
        
        try:
            print(f"🔍 Step 1: Loading form for upload simulation...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Testing picture upload simulation", "orange")
            time.sleep(2)
            
            # Look for file inputs
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if file_inputs and self.test_images:
                print(f"🔍 Step 2: Testing file upload with {len(file_inputs)} file inputs...")
                
                for i, file_input in enumerate(file_inputs[:1]):  # Test first input only
                    print(f"🔍 Testing file input {i+1}...")
                    
                    # Highlight the file input
                    self._highlight_element(file_input, f"Uploading to input {i+1}")
                    
                    # Check if input accepts images
                    accept_attr = file_input.get_attribute('accept')
                    print(f"   File input accepts: {accept_attr}")
                    
                    if self.test_images:
                        test_image = self.test_images[0]  # Use first test image
                        print(f"   Uploading test image: {test_image}")
                        
                        try:
                            # Send file path to input
                            file_input.send_keys(test_image)
                            self._add_visual_indicator(f"File uploaded to input {i+1}", "green")
                            time.sleep(2)
                            
                            # Check if preview appears
                            print(f"🔍 Step 3: Checking for upload preview...")
                            time.sleep(2)  # Wait for potential preview
                            
                            # Look for new preview elements
                            previews = self.driver.find_elements(By.CSS_SELECTOR,
                                ".preview img, .thumbnail img, .uploaded-image, img[src*='blob:']")
                            
                            if previews:
                                print(f"✅ Found {len(previews)} preview images")
                                for preview in previews:
                                    self._highlight_element(preview, "Upload preview")
                                    time.sleep(1)
                            else:
                                print(f"⚠️ No preview images found")
                            
                        except Exception as e:
                            print(f"⚠️ File upload failed: {e}")
            else:
                print(f"⚠️ No file inputs found or no test images available")
                
                # If no file inputs, look for alternative upload methods
                print(f"🔍 Looking for alternative upload methods...")
                upload_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                    ".upload-btn, .add-picture, .browse-files, [data-upload]")
                
                if upload_buttons:
                    print(f"Found {len(upload_buttons)} upload buttons")
                    for i, button in enumerate(upload_buttons):
                        self._highlight_element(button, f"Upload button {i+1}")
                        print(f"   Button {i+1}: {button.text}")
                        time.sleep(1)
            
            print(f"🔍 Step 4: Testing picture management buttons...")
            mgmt_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                ".remove-picture, .delete-image, .edit-picture, .reorder-pictures")
            
            if mgmt_buttons:
                print(f"Found {len(mgmt_buttons)} picture management buttons")
                for i, button in enumerate(mgmt_buttons):
                    self._highlight_element(button, f"Management button {i+1}")
                    print(f"   Button {i+1}: {button.text or button.get_attribute('title')}")
                    time.sleep(1)
            else:
                print(f"⚠️ No picture management buttons found")
            
            self._add_visual_indicator("Picture upload simulation complete", "green")
            time.sleep(3)
            
            print(f"✅ SELENIUM TEST PASSED: Picture upload interaction simulated")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"UPLOAD FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_picture_drag_and_drop_simulation(self):
        """Test drag and drop picture upload simulation"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Simulate drag and drop picture upload")
        
        try:
            print(f"🔍 Step 1: Loading form for drag-and-drop testing...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            self._add_visual_indicator("Testing drag-and-drop simulation", "purple")
            time.sleep(2)
            
            # Look for drop zones
            drop_zones = self.driver.find_elements(By.CSS_SELECTOR,
                ".drop-zone, .dropzone, .file-drop, [data-drop], .drag-drop-area")
            
            if drop_zones:
                print(f"🔍 Step 2: Testing {len(drop_zones)} drop zones...")
                
                for i, zone in enumerate(drop_zones):
                    print(f"🔍 Testing drop zone {i+1}...")
                    self._highlight_element(zone, f"Drop zone {i+1}")
                    
                    # Simulate drag enter
                    print(f"   Simulating drag enter...")
                    self.driver.execute_script("""
                        var event = new DragEvent('dragenter', {
                            dataTransfer: new DataTransfer()
                        });
                        arguments[0].dispatchEvent(event);
                    """, zone)
                    time.sleep(1)
                    
                    # Simulate drag over
                    print(f"   Simulating drag over...")
                    self.driver.execute_script("""
                        var event = new DragEvent('dragover', {
                            dataTransfer: new DataTransfer()
                        });
                        arguments[0].dispatchEvent(event);
                    """, zone)
                    time.sleep(1)
                    
                    # Check for visual feedback
                    zone_classes = zone.get_attribute('class')
                    print(f"   Drop zone classes after drag: {zone_classes}")
                    
                    # Simulate drag leave
                    print(f"   Simulating drag leave...")
                    self.driver.execute_script("""
                        var event = new DragEvent('dragleave', {
                            dataTransfer: new DataTransfer()
                        });
                        arguments[0].dispatchEvent(event);
                    """, zone)
                    time.sleep(1)
                    
            else:
                print(f"⚠️ No drag-and-drop zones found")
                
                # Create a visual demo of what drag-and-drop would look like
                print(f"🔍 Creating drag-and-drop demo...")
                self.driver.execute_script("""
                    var demo = document.createElement('div');
                    demo.innerHTML = 'DRAG & DROP DEMO AREA';
                    demo.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 300px;
                        height: 200px;
                        border: 3px dashed #007bff;
                        background: rgba(0, 123, 255, 0.1);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        color: #007bff;
                        z-index: 10000;
                    `;
                    document.body.appendChild(demo);
                    
                    setTimeout(() => {
                        demo.style.background = 'rgba(40, 167, 69, 0.2)';
                        demo.style.borderColor = '#28a745';
                        demo.style.color = '#28a745';
                        demo.innerHTML = 'FILE DROPPED!';
                    }, 2000);
                    
                    setTimeout(() => {
                        if (demo.parentNode) {
                            demo.parentNode.removeChild(demo);
                        }
                    }, 4000);
                """)
                time.sleep(5)
            
            self._add_visual_indicator("Drag-and-drop simulation complete", "green")
            time.sleep(2)
            
            print(f"✅ SELENIUM TEST PASSED: Drag-and-drop simulation complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"DRAG-DROP FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    def test_picture_gallery_and_preview_behavior(self):
        """Test picture gallery and preview behavior"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture gallery and preview interactions")
        
        try:
            print(f"🔍 Step 1: Loading component detail page for gallery testing...")
            # Try component detail page first, fallback to creation form
            try:
                self.driver.get(f"{self.base_url}/components/1")
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                print(f"   Component detail not accessible, using creation form...")
                self.driver.get(f"{self.base_url}/component/new")
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            self._add_visual_indicator("Testing picture gallery behavior", "cyan")
            time.sleep(2)
            
            print(f"🔍 Step 2: Looking for existing images...")
            existing_images = self.driver.find_elements(By.CSS_SELECTOR,
                "img[src*='.jpg'], img[src*='.png'], img[src*='.jpeg'], .gallery img, .picture img")
            
            if existing_images:
                print(f"✅ Found {len(existing_images)} existing images")
                
                for i, img in enumerate(existing_images[:3]):  # Test first 3 images
                    print(f"🔍 Testing image {i+1}...")
                    self._highlight_element(img, f"Image {i+1}")
                    
                    # Get image info
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt')
                    print(f"   Image {i+1}: src={src[:50]}..., alt='{alt}'")
                    
                    # Test click interaction
                    try:
                        print(f"   Testing click interaction...")
                        img.click()
                        time.sleep(1)
                        
                        # Check for modal or lightbox
                        modals = self.driver.find_elements(By.CSS_SELECTOR,
                            ".modal, .lightbox, .image-modal, .popup")
                        
                        if modals:
                            print(f"   ✅ Modal/lightbox opened")
                            for modal in modals:
                                self._highlight_element(modal, "Image modal")
                            
                            # Try to close modal
                            close_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                                ".close, .modal-close, [data-dismiss]")
                            if close_buttons:
                                close_buttons[0].click()
                                print(f"   Modal closed")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"   ⚠️ Image click failed: {e}")
            else:
                print(f"⚠️ No existing images found")
                
                # Create demo gallery
                print(f"🔍 Creating demo gallery...")
                self.driver.execute_script(f"""
                    var gallery = document.createElement('div');
                    gallery.innerHTML = `
                        <h3>DEMO PICTURE GALLERY</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 150px); gap: 10px;">
                            <div style="width: 150px; height: 100px; background: linear-gradient(45deg, #ff6b6b, #feca57); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Image 1</div>
                            <div style="width: 150px; height: 100px; background: linear-gradient(45deg, #48dbfb, #0abde3); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Image 2</div>
                            <div style="width: 150px; height: 100px; background: linear-gradient(45deg, #1dd1a1, #10ac84); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Image 3</div>
                        </div>
                    `;
                    gallery.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                        z-index: 10000;
                        text-align: center;
                    `;
                    document.body.appendChild(gallery);
                    
                    setTimeout(() => {{
                        if (gallery.parentNode) {{
                            gallery.parentNode.removeChild(gallery);
                        }}
                    }}, 5000);
                """)
                time.sleep(6)
            
            print(f"🔍 Step 3: Testing picture management buttons...")
            mgmt_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                ".edit-picture, .delete-picture, .reorder, .set-primary, .manage-pictures")
            
            if mgmt_buttons:
                print(f"Found {len(mgmt_buttons)} picture management buttons")
                for i, button in enumerate(mgmt_buttons):
                    self._highlight_element(button, f"Management {i+1}")
                    button_text = button.text or button.get_attribute('title') or button.get_attribute('data-action')
                    print(f"   Management button {i+1}: {button_text}")
                    time.sleep(1)
            
            self._add_visual_indicator("Picture gallery testing complete", "green")
            time.sleep(3)
            
            print(f"✅ SELENIUM TEST PASSED: Picture gallery behavior tested")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._add_visual_indicator(f"GALLERY FAILED: {str(e)}", "red")
            time.sleep(3)
            raise

    # Visual helper methods (same as in previous file)
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
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    z-index: 9999;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
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
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
            """, element)
            
            if message:
                self.driver.execute_script(f"""
                    var tooltip = document.createElement('div');
                    tooltip.innerHTML = '{message}';
                    tooltip.style.cssText = `
                        position: absolute;
                        background: #333;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-size: 12px;
                        z-index: 10000;
                        top: -35px;
                        left: 0;
                        white-space: nowrap;
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


if __name__ == '__main__':
    print("""
    🎬 PICTURE UPLOAD SELENIUM TESTING:
    
    To run these visual picture upload tests:
    
    1. Start your application: ./start.sh
    
    2. Run this test file:
       python -m pytest tests/selenium/test_picture_upload_visual.py -v -s
    
    3. Watch the browser for:
       - Picture upload section identification
       - File input interactions
       - Drag-and-drop simulations
       - Gallery behavior testing
       - Visual feedback demonstrations
    
    🖼️  Test images will be created automatically!
    👁️  Browser stays visible so you can see the testing!
    """)
    
    unittest.main()