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