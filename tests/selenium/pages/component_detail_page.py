"""
Component detail page object for testing picture visibility
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class ComponentDetailPage(BasePage):
    """Component detail page with focus on Main Image Display testing"""
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def check_main_image_display(self):
        """Check specifically the Main Image Display section (.main-image-container)"""
        try:
            # Find the main image container
            main_container = self.driver.find_element(By.CSS_SELECTOR, ".main-image-container")
            
            # Check if there's an actual image displayed
            try:
                main_image = main_container.find_element(By.CSS_SELECTOR, ".main-image")
                if main_image.is_displayed():
                    image_src = main_image.get_attribute("src")
                    if image_src and image_src != "":
                        logger.info(f"✅ Main image found: {image_src}")
                        return {
                            "status": "VISIBLE",
                            "image_src": image_src,
                            "element_displayed": True
                        }
                    else:
                        logger.warning("⚠️  Main image element exists but no src")
                        return {"status": "NO_SRC", "element_displayed": True}
                else:
                    logger.warning("⚠️  Main image element not displayed")
                    return {"status": "NOT_DISPLAYED", "element_displayed": False}
            except NoSuchElementException:
                # Check if placeholder is shown instead
                try:
                    placeholder = main_container.find_element(By.CSS_SELECTOR, ".image-placeholder")
                    if placeholder.is_displayed():
                        logger.info("📭 Image placeholder is displayed (no images)")
                        return {"status": "PLACEHOLDER", "element_displayed": True}
                except NoSuchElementException:
                    logger.error("❌ Neither main image nor placeholder found")
                    return {"status": "MISSING_ELEMENTS", "element_displayed": False}
                    
        except NoSuchElementException:
            logger.error("❌ Main image container not found")
            return {"status": "NO_CONTAINER", "element_displayed": False}
            
        return {"status": "UNKNOWN", "element_displayed": False}
    
    def get_variant_chips(self):
        """Get information about variant chips"""
        try:
            variant_chips = self.driver.find_elements(By.CSS_SELECTOR, ".variant-chip")
            chip_info = []
            
            for i, chip in enumerate(variant_chips):
                if chip.is_displayed():
                    chip_text = chip.text.strip()
                    is_active = "active" in chip.get_attribute("class")
                    chip_info.append({
                        "index": i,
                        "text": chip_text,
                        "active": is_active,
                        "element": chip
                    })
            
            logger.info(f"🎨 Found {len(chip_info)} variant chips")
            return chip_info
            
        except Exception as e:
            logger.error(f"❌ Error checking variant chips: {e}")
            return []
    
    def test_variant_switching(self):
        """Test clicking variant chips to see if main image changes"""
        try:
            variant_chips = self.get_variant_chips()
            if len(variant_chips) < 2:
                logger.info("ℹ️  Not enough variants to test switching")
                return []
            
            results = []
            for chip_info in variant_chips[:3]:  # Test first 3 variants
                chip = chip_info["element"]
                logger.info(f"🔄 Testing variant chip {chip_info['index']+1}: {chip_info['text']}")
                
                # Click the chip
                self.scroll_to_element(chip)
                chip.click()
                time.sleep(2)  # Wait for Alpine.js to update
                
                # Check main image after click
                main_image_status = self.check_main_image_display()
                results.append({
                    "variant": chip_info['text'],
                    "main_image": main_image_status
                })
                
                # Take screenshot for this variant
                self.take_screenshot(f"variant_{chip_info['index']}_clicked")
                
            return results
            
        except Exception as e:
            logger.error(f"❌ Error testing variant switching: {e}")
            return []
    
    def count_all_visible_pictures(self):
        """Count all visible pictures on the page"""
        try:
            # Look for various image selectors
            image_selectors = [
                ".main-image[src]",
                ".thumbnail[src]",
                "img[src*='.jpg']",
                "img[src*='.png']",
                "img[src*='.jpeg']"
            ]
            
            all_images = set()
            for selector in image_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            src = element.get_attribute("src")
                            if src and src != "":
                                # Extract filename from URL
                                filename = src.split("/")[-1]
                                all_images.add(filename)
                except Exception:
                    continue
            
            total_count = len(all_images)
            if total_count > 0:
                logger.info(f"📊 Found {total_count} unique pictures:")
                for i, filename in enumerate(sorted(all_images), 1):
                    logger.info(f"  {i}. {filename}")
            else:
                logger.info("📊 No pictures found")
            
            return {
                "count": total_count,
                "images": list(sorted(all_images))
            }
            
        except Exception as e:
            logger.error(f"❌ Error counting pictures: {e}")
            return {"count": 0, "images": []}
    
    def check_alpine_js_data(self):
        """Check Alpine.js data state for debugging"""
        try:
            # Execute JavaScript to get Alpine.js component data
            alpine_data = self.driver.execute_script("""
                try {
                    const component = Alpine.$data(document.querySelector('[x-data]'));
                    return {
                        selectedVariant: component.selectedVariant,
                        currentImageIndex: component.currentImageIndex,
                        currentImages: component.currentImages ? component.currentImages.length : 0,
                        variants: component.variants ? component.variants.length : 0
                    };
                } catch (e) {
                    return { error: e.message };
                }
            """)
            
            logger.info(f"🔍 Alpine.js Data: {alpine_data}")
            return alpine_data
            
        except Exception as e:
            logger.error(f"❌ Error checking Alpine.js data: {e}")
            return {"error": str(e)}
    
    def comprehensive_picture_check(self):
        """Perform comprehensive picture visibility check"""
        logger.info("🔍 Performing comprehensive picture visibility check...")
        
        # Take screenshot
        self.take_screenshot("comprehensive_check")
        
        # Check main image display
        main_image_status = self.check_main_image_display()
        
        # Count all pictures
        picture_count = self.count_all_visible_pictures()
        
        # Get variant information
        variant_info = self.get_variant_chips()
        
        # Check Alpine.js state
        alpine_data = self.check_alpine_js_data()
        
        # Test variant switching
        switching_results = self.test_variant_switching()
        
        return {
            "timestamp": time.time(),
            "main_image": main_image_status,
            "picture_count": picture_count,
            "variants": variant_info,
            "alpine_data": alpine_data,
            "switching_test": switching_results
        }
    
    def wait_for_loading_complete(self, timeout=20):
        """Wait for component detail loading to complete"""
        try:
            # Check for loading indicator
            loading_selector = ".loading-indicator, .loading-overlay"
            loading_elements = self.driver.find_elements(By.CSS_SELECTOR, loading_selector)
            
            if loading_elements and loading_elements[0].is_displayed():
                logger.info("⏳ Loading indicator detected, waiting for completion...")
                # Wait for loading to disappear
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                wait = WebDriverWait(self.driver, timeout)
                wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, loading_selector)))
                logger.info("✅ Loading complete")
                
        except Exception as e:
            logger.warning(f"⚠️  Loading wait error: {e}")
    
    def check_gallery_functionality(self):
        """Test image gallery functionality"""
        logger.info("🖼️  Testing gallery functionality...")
        results = {"thumbnail_navigation": False, "main_image_updates": False}
        
        try:
            # Get thumbnails
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
            if len(thumbnails) >= 2:
                # Click second thumbnail
                initial_main_src = self.get_main_image_src()
                thumbnails[1].click()
                time.sleep(1)
                
                new_main_src = self.get_main_image_src()
                if initial_main_src != new_main_src:
                    results["thumbnail_navigation"] = True
                    results["main_image_updates"] = True
                    logger.info("✅ Gallery navigation working")
                else:
                    logger.warning("⚠️  Main image did not update on thumbnail click")
            else:
                logger.info("ℹ️  Not enough thumbnails to test navigation")
                
        except Exception as e:
            logger.error(f"❌ Gallery test error: {e}")
            
        return results
    
    def check_lightbox_functionality(self):
        """Test lightbox functionality"""
        logger.info("💡 Testing lightbox functionality...")
        results = {"opens": False, "closes": False, "navigation": False}
        
        try:
            # Try to open lightbox by clicking main image
            main_image = self.driver.find_element(By.CSS_SELECTOR, ".main-image")
            main_image.click()
            time.sleep(1)
            
            # Check if lightbox opened
            lightbox = self.driver.find_elements(By.CSS_SELECTOR, ".lightbox, .image-lightbox")
            if lightbox and lightbox[0].is_displayed():
                results["opens"] = True
                logger.info("✅ Lightbox opens")
                
                # Try navigation
                next_btn = self.driver.find_elements(By.CSS_SELECTOR, ".lightbox-next")
                if next_btn:
                    next_btn[0].click()
                    time.sleep(0.5)
                    results["navigation"] = True
                
                # Try to close
                close_btn = self.driver.find_elements(By.CSS_SELECTOR, ".lightbox-close")
                if close_btn:
                    close_btn[0].click()
                    time.sleep(0.5)
                    if not self.driver.find_element(By.CSS_SELECTOR, ".lightbox").is_displayed():
                        results["closes"] = True
                        logger.info("✅ Lightbox closes")
                        
        except Exception as e:
            logger.warning(f"⚠️  Lightbox test skipped: {e}")
            
        return results
    
    def check_loading_state_handling(self):
        """Check if page handles loading states properly"""
        logger.info("🔄 Checking loading state handling...")
        
        try:
            # Check URL for loading parameter
            current_url = self.driver.current_url
            has_loading_param = "loading=true" in current_url
            
            # Check Alpine.js loading states
            alpine_data = self.check_alpine_js_data()
            is_loading = alpine_data.get("isLoading", False) if isinstance(alpine_data, dict) else False
            
            # Check for auto-refresh mechanism
            has_refresh = self.driver.execute_script("""
                return typeof window.ComponentDetailApp !== 'undefined' && 
                       typeof window.ComponentDetailApp.startAutoRefresh === 'function';
            """)
            
            return {
                "has_loading_param": has_loading_param,
                "alpine_loading_state": is_loading,
                "has_auto_refresh": has_refresh
            }
            
        except Exception as e:
            logger.error(f"❌ Loading state check error: {e}")
            return {}
    
    def check_variant_data_consistency(self):
        """Check if variant data is consistent between UI and Alpine state"""
        logger.info("🔍 Checking variant data consistency...")
        
        try:
            # Get UI variant count
            ui_variants = self.get_variant_chips()
            ui_variant_count = len(ui_variants)
            
            # Get Alpine.js variant count
            alpine_data = self.check_alpine_js_data()
            alpine_variant_count = alpine_data.get("variants", 0) if isinstance(alpine_data, dict) else 0
            
            # Check if counts match
            counts_match = ui_variant_count == alpine_variant_count
            
            if counts_match:
                logger.info(f"✅ Variant counts match: UI={ui_variant_count}, Alpine={alpine_variant_count}")
            else:
                logger.warning(f"⚠️  Variant count mismatch: UI={ui_variant_count}, Alpine={alpine_variant_count}")
                
            return {
                "ui_count": ui_variant_count,
                "alpine_count": alpine_variant_count,
                "consistent": counts_match
            }
            
        except Exception as e:
            logger.error(f"❌ Variant consistency check error: {e}")
            return {}
    
    def get_main_image_src(self):
        """Get the current main image source"""
        try:
            main_image = self.driver.find_element(By.CSS_SELECTOR, ".main-image")
            return main_image.get_attribute("src")
        except:
            return None
    
    def check_api_endpoints(self):
        """Check if API endpoints are being called"""
        logger.info("🔌 Checking API endpoint calls...")
        
        try:
            # Execute JavaScript to check for API calls
            api_info = self.driver.execute_script("""
                // Check if fetch has been called for variants endpoint
                const logs = performance.getEntriesByType('resource');
                const apiCalls = logs.filter(log => log.name.includes('/api/components/') && log.name.includes('/variants'));
                
                return {
                    variantApiCalled: apiCalls.length > 0,
                    apiCallCount: apiCalls.length,
                    apiUrls: apiCalls.map(call => call.name)
                };
            """)
            
            if api_info["variantApiCalled"]:
                logger.info(f"✅ Variant API called {api_info['apiCallCount']} times")
            else:
                logger.info("ℹ️  No variant API calls detected")
                
            return api_info
            
        except Exception as e:
            logger.error(f"❌ API check error: {e}")
            return {}
    
    def test_responsive_behavior(self):
        """Test responsive behavior at different screen sizes"""
        logger.info("📱 Testing responsive behavior...")
        results = {}
        
        try:
            # Test mobile view
            self.driver.set_window_size(375, 667)
            time.sleep(1)
            mobile_layout = self.check_layout_at_size("mobile")
            results["mobile"] = mobile_layout
            
            # Test tablet view  
            self.driver.set_window_size(768, 1024)
            time.sleep(1)
            tablet_layout = self.check_layout_at_size("tablet")
            results["tablet"] = tablet_layout
            
            # Test desktop view
            self.driver.set_window_size(1920, 1080)
            time.sleep(1)
            desktop_layout = self.check_layout_at_size("desktop")
            results["desktop"] = desktop_layout
            
            logger.info(f"✅ Responsive test complete: {results}")
            
        except Exception as e:
            logger.error(f"❌ Responsive test error: {e}")
            
        finally:
            # Reset to default size
            self.driver.set_window_size(1280, 800)
            
        return results
    
    def check_layout_at_size(self, size_name):
        """Check layout elements at current window size"""
        try:
            # Check if key elements are visible and properly sized
            main_image = self.driver.find_element(By.CSS_SELECTOR, ".main-image-container")
            gallery = self.driver.find_element(By.CSS_SELECTOR, ".image-gallery")
            
            return {
                "size": size_name,
                "main_image_visible": main_image.is_displayed(),
                "gallery_visible": gallery.is_displayed(),
                "viewport_width": self.driver.execute_script("return window.innerWidth"),
                "viewport_height": self.driver.execute_script("return window.innerHeight")
            }
        except:
            return {"size": size_name, "error": "Layout check failed"}