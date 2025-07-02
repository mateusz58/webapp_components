#!/usr/bin/env python3
"""
Specific test for loading indicator visibility during component creation redirect
"""
import logging
import sys
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.driver_manager import DriverManager
from pages.component_form_page import ComponentFormPage
from pages.component_detail_page import ComponentDetailPage
from config.test_config import TestConfig

class LoadingIndicatorTest:
    """Test loading indicator during component creation redirect"""
    
    def __init__(self):
        self.driver = None
        self.component_id = None
        self.redirect_timing = {}
    
    def setup(self):
        """Initialize test environment"""
        logger.info("🚀 === TESTING LOADING INDICATOR VISIBILITY ===")
        
        # Create driver
        self.driver = DriverManager.create_chrome_driver()
        
        # Navigate to application
        logger.info("🌐 Opening application...")
        self.driver.get(f"{TestConfig.APP_URL}/component/new")
        
        # Wait for page load
        form_page = ComponentFormPage(self.driver)
        form_page.wait_for_element("body")
        logger.info("✅ Component form loaded")
        
        return form_page
    
    def create_component_and_capture_redirect(self, form_page):
        """Create component and capture the exact redirect moment"""
        timestamp = int(time.time())
        product_number = f"LOADING-TEST-{timestamp}"
        description = f"Loading indicator test component created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Fill form quickly
        form_page.fill_essential_info(product_number, description)
        form_page.select_component_type("alloverprints")
        form_page.select_supplier("SAB")
        
        # Add one variant with picture
        form_page.add_variant("Red", create_image=True)
        time.sleep(2)  # Give time for image upload
        
        # Prepare to capture redirect timing
        logger.info("📤 About to submit form - capturing redirect timing...")
        
        # Record pre-submit state
        pre_submit_url = self.driver.current_url
        logger.info(f"🔗 Pre-submit URL: {pre_submit_url}")
        
        # Submit form (without waiting for redirect)
        submit_btn = form_page.wait_for_element("#submitBtn")
        form_page.scroll_to_element(submit_btn)
        logger.info("🖱️  Clicking submit button...")
        form_page.driver.execute_script("arguments[0].click();", submit_btn)
        
        # Capture the exact moment of redirect
        redirect_start = time.time()
        
        # Wait for URL change and capture timing
        logger.info("⏱️  Waiting for redirect...")
        form_page.wait_for_url_change(pre_submit_url, timeout=10)
        
        redirect_end = time.time()
        redirect_time = redirect_end - redirect_start
        
        # IMMEDIATELY capture URL with parameters before JavaScript cleanup
        immediate_url = self.driver.current_url
        logger.info(f"🔗 Immediate redirect URL: {immediate_url}")
        logger.info(f"⏱️  Redirect took: {redirect_time:.3f} seconds")
        
        # Check for loading parameter immediately
        if 'loading=true' in immediate_url:
            logger.info("✅ Loading parameter found immediately after redirect!")
        else:
            logger.warning("⚠️  Loading parameter not found in immediate URL")
        
        # Get final URL after potential cleanup
        final_url = self.driver.current_url
        logger.info(f"🔗 Final URL: {final_url}")
        
        # Extract component ID
        try:
            component_id = int(final_url.split('/')[-1].split('?')[0])
            logger.info(f"🆔 Component ID: {component_id}")
        except:
            component_id = None
            logger.error("❌ Could not extract component ID")
        
        # Store timing data
        self.redirect_timing = {
            'redirect_time': redirect_time,
            'pre_submit_url': pre_submit_url,
            'immediate_url': immediate_url,
            'final_url': final_url,
            'component_id': component_id,
            'loading_param_found': 'loading=true' in immediate_url
        }
        
        return component_id, product_number
    
    def test_immediate_loading_state(self):
        """Test loading state immediately after redirect"""
        logger.info("🔍 Testing IMMEDIATE loading state after redirect...")
        
        # Capture state within 100ms of redirect
        immediate_checks = []
        
        # Check every 100ms for the first 2 seconds, then extend for auto-refresh
        for i in range(50):  # Extended to 5 seconds to catch auto-refresh
            check_time = time.time()
            
            # Check URL parameters
            current_url = self.driver.current_url
            has_loading_param = 'loading=true' in current_url
            
            # Check for loading indicator elements
            loading_elements = self.check_loading_indicators()
            
            # Check Alpine.js loading state
            alpine_loading = self.check_alpine_loading_state()
            
            # Check CSS loading state
            css_loading = self.check_css_loading_state()
            
            # Check if images are actually visible on page
            images_visible = self.check_images_visible()
            
            check_result = {
                'timestamp': check_time,
                'interval': i * 100,  # milliseconds
                'url': current_url,
                'has_loading_param': has_loading_param,
                'loading_elements': loading_elements,
                'alpine_loading': alpine_loading,
                'css_loading': css_loading,
                'images_visible': images_visible
            }
            
            immediate_checks.append(check_result)
            
            # Log significant findings
            if has_loading_param:
                logger.info(f"✅ Loading parameter found at {i*100}ms")
            if loading_elements['visible']:
                logger.info(f"✅ Loading indicator visible at {i*100}ms")
            if alpine_loading.get('imagesLoading') == True:
                logger.info(f"✅ Alpine loading state TRUE at {i*100}ms")
            if images_visible['count'] > 0:
                logger.info(f"✅ Images visible ({images_visible['count']}) at {i*100}ms")
            
            time.sleep(0.1)  # 100ms intervals
        
        return immediate_checks
    
    def check_loading_indicators(self):
        """Check for various loading indicator elements"""
        try:
            # Check for Alpine.js loading state
            loading_spinner = None
            loading_message = None
            loading_container = None
            
            try:
                from selenium.webdriver.common.by import By
                loading_container = self.driver.find_element(By.CSS_SELECTOR, ".image-loading-state")
                container_visible = loading_container.is_displayed()
            except:
                container_visible = False
            
            try:
                from selenium.webdriver.common.by import By
                loading_spinner = self.driver.find_element(By.CSS_SELECTOR, ".spinner-border")
                spinner_visible = loading_spinner.is_displayed()
            except:
                spinner_visible = False
            
            try:
                from selenium.webdriver.common.by import By
                # Check for any element with loading text
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Loading')]")
                loading_text_visible = any(el.is_displayed() for el in elements)
            except:
                loading_text_visible = False
            
            return {
                'visible': container_visible or spinner_visible or loading_text_visible,
                'container': container_visible,
                'spinner': spinner_visible,
                'text': loading_text_visible
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking loading indicators: {e}")
            return {'visible': False, 'error': str(e)}
    
    def check_alpine_loading_state(self):
        """Check Alpine.js component loading state"""
        try:
            alpine_state = self.driver.execute_script("""
                try {
                    // Wait a moment for Alpine to initialize
                    if (typeof Alpine === 'undefined') {
                        return { error: 'Alpine not available' };
                    }
                    
                    // Find the Alpine component element
                    const element = document.querySelector('[x-data="componentDetailApp()"]') || 
                                   document.querySelector('[x-data="componentDetail()"]') ||
                                   document.querySelector('[x-data]');
                    
                    if (!element) {
                        return { error: 'No Alpine element found' };
                    }
                    
                    // Try multiple methods to get Alpine data
                    let component = null;
                    
                    // Method 1: Direct Alpine access
                    if (element._x_dataStack && element._x_dataStack.length > 0) {
                        component = element._x_dataStack[0];
                    }
                    
                    // Method 2: Alpine.$data method
                    if (!component && Alpine.$data) {
                        component = Alpine.$data(element);
                    }
                    
                    // Method 3: Check if Alpine data is in a different location
                    if (!component && element.__x) {
                        component = element.__x.$data;
                    }
                    
                    if (!component) {
                        return { error: 'Could not access Alpine component data' };
                    }
                    
                    return {
                        imagesLoading: component.imagesLoading,
                        loadingMessage: component.loadingMessage,
                        componentImages: component.componentImages ? component.componentImages.length : 0,
                        variants: component.variants ? component.variants.length : 0,
                        hasComponent: true
                    };
                } catch (e) {
                    return { error: 'Exception: ' + e.message };
                }
            """)
            
            return alpine_state
            
        except Exception as e:
            return {'error': str(e)}
    
    def check_css_loading_state(self):
        """Check CSS-based loading state"""
        try:
            # Check body data attribute
            body_loading = self.driver.execute_script("""
                return document.body.getAttribute('data-initial-loading');
            """)
            
            return {
                'body_data_loading': body_loading,
                'has_css_loading': body_loading == 'true'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def check_images_visible(self):
        """Check if images are actually visible on the page"""
        try:
            image_info = self.driver.execute_script("""
                // Find all image elements in the gallery
                const galleryImages = document.querySelectorAll('.image-gallery img, .variant-images img, .component-images img');
                const visibleImages = Array.from(galleryImages).filter(img => {
                    const rect = img.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 && img.complete && img.naturalHeight > 0;
                });
                
                return {
                    total: galleryImages.length,
                    visible: visibleImages.length,
                    loading: Array.from(galleryImages).some(img => !img.complete)
                };
            """)
            
            return {
                'count': image_info['visible'],
                'total': image_info['total'],
                'loading': image_info['loading']
            }
            
        except Exception as e:
            return {'count': 0, 'total': 0, 'loading': False, 'error': str(e)}
    
    def analyze_loading_behavior(self, immediate_checks):
        """Analyze the loading behavior over time"""
        logger.info("📊 === ANALYZING LOADING BEHAVIOR ===")
        
        # Find when loading param appears/disappears
        loading_param_times = []
        loading_visible_times = []
        alpine_loading_times = []
        images_visible_times = []
        
        for check in immediate_checks:
            if check['has_loading_param']:
                loading_param_times.append(check['interval'])
            if check['loading_elements']['visible']:
                loading_visible_times.append(check['interval'])
            if check.get('alpine_loading', {}).get('imagesLoading') == True:
                alpine_loading_times.append(check['interval'])
            if check.get('images_visible', {}).get('count', 0) > 0:
                images_visible_times.append(check['interval'])
        
        # Log findings
        logger.info(f"🔗 Loading parameter present at: {loading_param_times}ms")
        logger.info(f"👁️  Loading indicator visible at: {loading_visible_times}ms")
        logger.info(f"🔄 Alpine loading state true at: {alpine_loading_times}ms")
        logger.info(f"🖼️  Images visible at: {images_visible_times}ms")
        
        # Analyze issues
        issues = []
        
        # Check if loading parameter was found in the initial redirect
        initial_param_found = self.redirect_timing.get('loading_param_found', False)
        
        if not initial_param_found and not loading_param_times:
            issues.append("Loading parameter never detected in URL (neither in redirect nor ongoing checks)")
        elif initial_param_found:
            logger.info("✅ Loading parameter was found in initial redirect URL")
        
        if not loading_visible_times:
            issues.append("Loading indicator never visible")
        
        if not alpine_loading_times:
            issues.append("Alpine loading state never activated")
        
        if (initial_param_found or loading_param_times) and not loading_visible_times:
            issues.append("Loading parameter present but indicator not visible")
        
        # Return analysis
        has_issues = len(issues) > 0
        
        if has_issues:
            logger.error("🚨 LOADING INDICATOR ISSUES FOUND:")
            for issue in issues:
                logger.error(f"  - {issue}")
        else:
            logger.info("✅ Loading indicator working correctly")
        
        return {
            'has_issues': has_issues,
            'issues': issues,
            'loading_param_times': loading_param_times,
            'loading_visible_times': loading_visible_times,
            'alpine_loading_times': alpine_loading_times
        }
    
    def run(self):
        """Run the complete test"""
        try:
            # Setup
            form_page = self.setup()
            
            # Create component and capture redirect
            component_id, product_number = self.create_component_and_capture_redirect(form_page)
            if not component_id:
                logger.error("❌ Failed to create component")
                return False
            
            # Test immediate loading state
            immediate_checks = self.test_immediate_loading_state()
            
            # Analyze behavior
            analysis = self.analyze_loading_behavior(immediate_checks)
            
            # Final screenshot
            self.driver.save_screenshot("/tmp/loading_test_final.png")
            logger.info("📸 Final screenshot saved: /tmp/loading_test_final.png")
            
            return not analysis['has_issues']
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False
        
        finally:
            # Keep browser open for inspection
            if self.driver:
                logger.info("⏳ Keeping browser open for 15 seconds for inspection...")
                time.sleep(15)
                DriverManager.quit_driver(self.driver)

def main():
    """Main test execution"""
    test = LoadingIndicatorTest()
    success = test.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()