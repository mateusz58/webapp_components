#!/usr/bin/env python3
"""
Comprehensive Component Creation Workflow Debug Test
This test follows the entire component creation workflow with extensive logging
to debug the picture URL generation issue in the API endpoint.

Workflow being tested:
1. Navigate to /component/new
2. Fill form with variants and pictures
3. JavaScript calls /api/component/create
4. API creates component + variants + pictures
5. API sets session status and returns loading page URL
6. JavaScript redirects to loading page
7. Loading page polls /api/component/creation-status/<id>
8. Background verification completes
9. Loading page redirects to component detail
10. Verify pictures are visible
"""
import logging
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'/tmp/component_creation_debug_{int(time.time())}.log')
    ]
)
logger = logging.getLogger(__name__)

# Add selenium directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Add config path for direct import
config_path = current_dir / 'config'
sys.path.insert(0, str(config_path))

from ..utils.driver_manager import DriverManager
from ..pages.component_form_page import ComponentFormPage
from ..pages.component_detail_page import ComponentDetailPage
from ..config.test_config import TestConfig


class ComponentCreationWorkflowDebugTest:
    """Debug test for complete component creation workflow"""
    
    def __init__(self):
        self.driver = None
        self.component_id = None
        self.test_results = {}
        self.api_logs = []
        self.test_session = f"DEBUG_{int(time.time())}"
        
    def setup(self):
        """Initialize test environment with enhanced logging"""
        logger.info("=" * 100)
        logger.info("🚀 STARTING COMPREHENSIVE COMPONENT CREATION WORKFLOW DEBUG TEST")
        logger.info("=" * 100)
        logger.info(f"📋 Test Session: {self.test_session}")
        logger.info(f"🌐 Target URL: {TestConfig.APP_URL}/component/new")
        logger.info(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create driver with enhanced capabilities
        logger.info("🔧 Creating Chrome driver with debug capabilities...")
        self.driver = DriverManager.create_chrome_driver()
        
        # Enable performance logging
        self.driver.execute_cdp_cmd('Network.enable', {})
        self.driver.execute_cdp_cmd('Runtime.enable', {})
        
        # Navigate to application
        logger.info("🌐 Opening component creation form...")
        self.driver.get(f"{TestConfig.APP_URL}/component/new")
        
        # Wait for page load and log initial state
        form_page = ComponentFormPage(self.driver)
        form_page.wait_for_element("body")
        
        # Log page state
        page_title = self.driver.title
        current_url = self.driver.current_url
        logger.info(f"✅ Page loaded successfully")
        logger.info(f"📄 Page Title: {page_title}")
        logger.info(f"🔗 Current URL: {current_url}")
        
        # Check for JavaScript errors
        js_errors = self.driver.get_log('browser')
        if js_errors:
            logger.warning(f"⚠️  Found {len(js_errors)} JavaScript console messages:")
            for error in js_errors[-5:]:  # Show last 5
                logger.warning(f"   JS: {error['level']} - {error['message']}")
        else:
            logger.info("✅ No JavaScript errors detected on page load")
        
        return form_page
    
    def create_test_component_with_extensive_logging(self, form_page):
        """Create component with detailed logging at each step"""
        timestamp = int(time.time())
        product_number = f"DEBUG-{timestamp}"
        description = f"Debug test component created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        logger.info("-" * 60)
        logger.info("📝 STEP 1: FILLING COMPONENT FORM")
        logger.info("-" * 60)
        
        # Fill basic info
        logger.info(f"✏️  Setting Product Number: {product_number}")
        logger.info(f"✏️  Setting Description: {description}")
        form_page.fill_essential_info(product_number, description)
        
        logger.info("🔧 Selecting Component Type: alloverprints")
        form_page.select_component_type("alloverprints")
        
        logger.info("🚚 Selecting Supplier: SAB")
        form_page.select_supplier("SAB")
        
        logger.info("🏷️  Adding keywords...")
        form_page.add_keywords(["debug", "automation", "test", "workflow"])
        
        # Add variants with pictures
        logger.info("-" * 60)
        logger.info("🎨 STEP 2: ADDING VARIANTS WITH PICTURES")
        logger.info("-" * 60)
        
        variants = ["Red", "Green"]
        for i, color in enumerate(variants, 1):
            logger.info(f"🎨 Adding Variant {i}/2: {color}")
            success = form_page.add_variant(color, create_image=True)
            if success:
                logger.info(f"✅ Variant {color} added successfully")
            else:
                logger.error(f"❌ Failed to add variant {color}")
            time.sleep(3)  # Allow processing time
        
        # Log form state before submission
        logger.info("-" * 60)
        logger.info("🔍 STEP 3: PRE-SUBMISSION FORM STATE")
        logger.info("-" * 60)
        
        # Count variant cards
        variant_cards = self.driver.find_elements("css selector", "[data-variant-id]")
        logger.info(f"📊 Variant cards found: {len(variant_cards)}")
        
        # Count file inputs
        file_inputs = self.driver.find_elements("css selector", "input[type='file']")
        logger.info(f"📁 File inputs found: {len(file_inputs)}")
        
        # Check for files attached
        for i, file_input in enumerate(file_inputs):
            files = file_input.get_attribute('files')
            logger.info(f"📁 File input {i+1}: {files}")
        
        # Monitor network requests during submission
        logger.info("-" * 60)
        logger.info("📤 STEP 4: FORM SUBMISSION WITH NETWORK MONITORING")
        logger.info("-" * 60)
        
        # Enable network monitoring
        self.driver.execute_cdp_cmd('Network.enable', {})
        
        # Submit form
        component_id = form_page.submit_form()
        
        # Monitor for the API call
        time.sleep(2)  # Allow API call to complete
        
        # Check network requests
        try:
            performance_logs = self.driver.get_log('performance')
            api_requests = []
            
            for log in performance_logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    if '/api/component/create' in url:
                        status = message['message']['params']['response']['status']
                        logger.info(f"🌐 API Call Detected: {url} - Status: {status}")
                        api_requests.append({'url': url, 'status': status})
            
            if api_requests:
                logger.info(f"✅ Found {len(api_requests)} API requests")
            else:
                logger.warning("⚠️  No API requests detected in performance logs")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not analyze network requests: {e}")
        
        # Cleanup form page resources
        form_page.cleanup()
        
        return component_id, product_number
    
    def monitor_loading_page_workflow(self):
        """Monitor the loading page workflow with detailed logging"""
        current_url = self.driver.current_url
        logger.info("-" * 60)
        logger.info("⏳ STEP 5: LOADING PAGE WORKFLOW MONITORING")
        logger.info("-" * 60)
        logger.info(f"🔗 Current URL: {current_url}")
        
        if "loading" in current_url:
            logger.info("✅ Successfully redirected to loading page")
            
            # Monitor status polling
            start_time = time.time()
            max_wait = 30  # 30 seconds max
            
            while time.time() - start_time < max_wait:
                # Check page content
                try:
                    page_source = self.driver.page_source
                    if "Ready" in page_source:
                        logger.info("✅ Loading page shows 'Ready' status")
                        break
                    elif "Error" in page_source:
                        logger.error("❌ Loading page shows 'Error' status")
                        break
                    else:
                        logger.info("⏳ Loading page still processing...")
                except Exception as e:
                    logger.warning(f"⚠️  Could not check page content: {e}")
                
                time.sleep(2)
            
            # Wait for final redirect
            logger.info("⏳ Waiting for redirect to component detail page...")
            final_wait_start = time.time()
            
            while time.time() - final_wait_start < 15:
                new_url = self.driver.current_url
                if new_url != current_url and "component/" in new_url and "loading" not in new_url:
                    logger.info(f"✅ Redirected to component detail: {new_url}")
                    # Extract component ID
                    if "/component/" in new_url:
                        self.component_id = new_url.split("/component/")[-1].split("/")[0]
                        logger.info(f"🆔 Component ID extracted: {self.component_id}")
                    break
                time.sleep(1)
            
        else:
            logger.warning("⚠️  Not on loading page - checking for direct redirect")
            if "component/" in current_url and "loading" not in current_url:
                self.component_id = current_url.split("/component/")[-1].split("/")[0]
                logger.info(f"🆔 Direct redirect to component {self.component_id}")
    
    def debug_api_state(self):
        """Debug the API state by checking database and files"""
        if not self.component_id:
            logger.error("❌ No component ID available for API debugging")
            return
        
        logger.info("-" * 60)
        logger.info("🔍 STEP 6: API STATE DEBUGGING")
        logger.info("-" * 60)
        
        try:
            # Call the API to get fresh component data
            api_url = f"{TestConfig.APP_URL}/api/components/{self.component_id}/variants"
            logger.info(f"🌐 Checking API endpoint: {api_url}")
            
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ API Response Status: {response.status_code}")
                logger.info(f"📊 Component ID: {data.get('component_id')}")
                logger.info(f"📊 Variants Count: {len(data.get('variants', []))}")
                
                # Log each variant and its pictures
                for i, variant in enumerate(data.get('variants', []), 1):
                    logger.info(f"🎨 Variant {i}: {variant.get('name')} (ID: {variant.get('id')})")
                    logger.info(f"   SKU: {variant.get('sku', 'NO SKU')}")
                    
                    images = variant.get('images', [])
                    logger.info(f"   Images: {len(images)} found")
                    
                    for j, image in enumerate(images, 1):
                        logger.info(f"     Image {j}: {image.get('name', 'NO NAME')}")
                        logger.info(f"       URL: {image.get('url', 'NO URL')}")
                        logger.info(f"       Order: {image.get('order', 'NO ORDER')}")
                
            else:
                logger.error(f"❌ API Request Failed: {response.status_code}")
                logger.error(f"❌ Response Text: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ API debugging failed: {e}")
    
    def test_picture_visibility_with_debug(self, detail_page):
        """Test picture visibility with comprehensive debugging"""
        logger.info("-" * 60)
        logger.info("🖼️  STEP 7: PICTURE VISIBILITY TESTING")
        logger.info("-" * 60)
        
        # Initial wait for page stabilization
        time.sleep(3)
        
        # Comprehensive picture check
        results = detail_page.comprehensive_picture_check()
        
        # Log detailed results
        logger.info("📊 PICTURE VISIBILITY RESULTS:")
        logger.info(f"   Main Image Status: {results['main_image']['status']}")
        logger.info(f"   Picture Count: {results['picture_count']['count']}")
        logger.info(f"   Gallery Status: {results['gallery']['status']}")
        
        # Check switching functionality
        if 'switching_test' in results:
            switching_results = results['switching_test']
            logger.info(f"   Variant Switching Tests: {len(switching_results)}")
            
            for switch_test in switching_results:
                variant_name = switch_test.get('variant_name', 'Unknown')
                main_status = switch_test['main_image']['status']
                logger.info(f"     {variant_name}: {main_status}")
        
        return results
    
    def analyze_test_results(self, immediate_results, product_number):
        """Analyze and report test results"""
        logger.info("-" * 60)
        logger.info("📊 STEP 8: FINAL RESULTS ANALYSIS")
        logger.info("-" * 60)
        
        success = True
        issues = []
        
        # Check main image
        main_status = immediate_results["main_image"]["status"]
        if main_status not in ["VISIBLE"]:
            success = False
            issues.append(f"Main image not visible: {main_status}")
        
        # Check picture count
        picture_count = immediate_results["picture_count"]["count"]
        if picture_count < 2:  # We added 2 variants with pictures
            success = False
            issues.append(f"Expected 2+ pictures, found {picture_count}")
        
        # Final verdict
        logger.info("=" * 100)
        if success:
            logger.info("🎉 TEST PASSED - COMPONENT CREATION WORKFLOW SUCCESSFUL!")
            logger.info(f"✅ Component: {product_number} (ID: {self.component_id})")
            logger.info(f"✅ Main Image: {main_status}")
            logger.info(f"✅ Picture Count: {picture_count}")
        else:
            logger.error("❌ TEST FAILED - ISSUES DETECTED!")
            logger.error(f"🔧 Component: {product_number} (ID: {self.component_id})")
            for issue in issues:
                logger.error(f"   - {issue}")
        logger.info("=" * 100)
        
        return success
    
    def run(self):
        """Execute the complete debug test workflow"""
        try:
            # Setup
            form_page = self.setup()
            
            # Create component with extensive logging
            self.component_id, product_number = self.create_test_component_with_extensive_logging(form_page)
            if not self.component_id:
                logger.error("❌ Failed to create component")
                return False
            
            # Monitor loading workflow
            self.monitor_loading_page_workflow()
            
            # Debug API state
            self.debug_api_state()
            
            # Create detail page instance
            detail_page = ComponentDetailPage(self.driver)
            
            # Test picture visibility
            immediate_results = self.test_picture_visibility_with_debug(detail_page)
            
            # Analyze results
            test_passed = self.analyze_test_results(immediate_results, product_number)
            
            return test_passed
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            logger.error(f"❌ Stacktrace:\n{traceback.format_exc()}")
            return False
        
        finally:
            # Keep browser open for inspection
            if self.driver:
                logger.info("⏳ Keeping browser open for 20 seconds for manual inspection...")
                time.sleep(20)
                DriverManager.quit_driver(self.driver)


def main():
    """Main test execution"""
    test = ComponentCreationWorkflowDebugTest()
    success = test.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()