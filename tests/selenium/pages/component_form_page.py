"""
Component form page object
"""
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from pages.base_page import BasePage
from utils.image_generator import ImageGenerator
from config.test_config import TestConfig

logger = logging.getLogger(__name__)

class ComponentFormPage(BasePage):
    """Component creation/edit form page"""
    
    def __init__(self, driver):
        super().__init__(driver)
        self.image_generator = ImageGenerator()
    
    def fill_essential_info(self, product_number, description):
        """Fill essential component information"""
        logger.info("📝 Filling essential information...")
        
        # Product number
        logger.info(f"✏️  Product Number: {product_number}")
        product_input = self.wait_for_element("#product_number")
        self.scroll_to_element(product_input)
        self.highlight_element(product_input, 'blue')
        self.slow_type(product_input, product_number)
        
        # Description
        logger.info(f"✏️  Description: {description}")
        desc_input = self.wait_for_element("#description")
        self.scroll_to_element(desc_input)
        self.highlight_element(desc_input, 'blue')
        self.slow_type(desc_input, description)
    
    def select_component_type(self, type_name="alloverprints"):
        """Select component type"""
        logger.info("🔧 Selecting component type...")
        
        type_select = Select(self.wait_for_element("#component_type_id"))
        type_select.select_by_visible_text(type_name)
        logger.info(f"✅ Selected component type: {type_name}")
    
    def select_supplier(self, supplier_code="SAB"):
        """Select supplier"""
        logger.info("🚚 Selecting supplier...")
        
        supplier_select = Select(self.wait_for_element("#supplier_id"))
        supplier_select.select_by_visible_text(supplier_code)
        logger.info(f"✅ Selected supplier: {supplier_code}")
    
    def add_keywords(self, keywords=None):
        """Add keywords to component"""
        if keywords is None:
            keywords = ["automation", "test", "selenium", "component"]
        
        logger.info("🏷️  Adding keywords...")
        keyword_input = self.wait_for_element("#keyword_input")
        self.scroll_to_element(keyword_input)
        self.highlight_element(keyword_input, 'blue')
        
        for keyword in keywords:
            logger.info(f"  + Adding keyword: {keyword}")
            keyword_input.clear()
            keyword_input.send_keys(keyword)
            keyword_input.send_keys(Keys.ENTER)
            time.sleep(0.5)  # Wait for keyword to be added
        
        logger.info(f"✅ Added {len(keywords)} keywords")
    
    def add_variant(self, color_name, create_image=True):
        """Add a single variant with color and picture"""
        logger.info(f"🎨 Adding variant: {color_name}")
        
        # Scroll to variants section
        try:
            variants_section = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Component Variants')]/parent::*")
        except:
            variants_section = self.wait_for_element("#variants_container")
        self.scroll_to_element(variants_section)
        
        # Click "Add Variant" button
        add_variant_btn = self.wait_for_element("#add_variant_btn")
        self.highlight_element(add_variant_btn, 'green')
        add_variant_btn.click()
        logger.info("✅ Clicked Add Variant button")
        
        # Wait for new variant form to appear
        time.sleep(2)
        
        # Find the newest variant (should be last one)
        variant_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-variant-id]")
        if not variant_cards:
            logger.error("❌ No variant cards found")
            return False
        
        # Get the variant ID
        latest_variant = variant_cards[-1]
        variant_id = latest_variant.get_attribute("data-variant-id")
        logger.info(f"🆔 Working with variant ID: {variant_id}")
        
        # Select color
        self._select_color(variant_id, color_name)
        
        # Upload picture if requested
        if create_image:
            image_path = self._create_and_upload_image(variant_id, color_name)
            if not image_path:
                logger.warning(f"⚠️  Failed to create/upload image for {color_name}")
        
        time.sleep(1)
        return True
    
    def _select_color(self, variant_id, color_name):
        """Select color for variant"""
        logger.info(f"🎨 Setting color: {color_name}")
        
        # Find color select for this variant
        color_selectors = [
            f"select[name*='color'][name*='{variant_id}']",
            f"select[data-variant-id='{variant_id}']",
            "select[name*='color']:last-of-type"
        ]
        
        for selector in color_selectors:
            try:
                color_select_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                color_select = Select(color_select_element)
                
                # Try to select by visible text (e.g., "Red")
                try:
                    color_select.select_by_visible_text(color_name)
                    logger.info(f"✅ Selected existing color: {color_name}")
                    return
                except:
                    # Try to select by value
                    for option in color_select.options:
                        if color_name.lower() in option.text.lower():
                            color_select.select_by_visible_text(option.text)
                            logger.info(f"✅ Selected color: {option.text}")
                            return
            except NoSuchElementException:
                continue
        
        logger.error(f"❌ Could not set color {color_name} for variant {variant_id}")
    
    def _create_and_upload_image(self, variant_id, color_name):
        """Create and upload image for variant"""
        # Generate image
        color_code = TestConfig.TEST_COLORS.get(color_name.lower(), '#888888')
        image_path = self.image_generator.create_test_image(color_name, color_code)
        
        if not image_path:
            return None
        
        # Upload the image
        return self._upload_image(variant_id, image_path)
    
    def _upload_image(self, variant_id, image_path):
        """Upload image for variant"""
        logger.info(f"📁 Uploading picture: {os.path.basename(image_path)}")
        
        # Find file input for this variant
        file_input_selectors = [
            f"input[type='file'][name*='variant_images'][name*='{variant_id}']",
            f"input[type='file'][data-variant-id='{variant_id}']",
            "input[type='file'][name*='variant_images']:last-of-type",
            "input[type='file'][accept*='image']:last-of-type"
        ]
        
        for selector in file_input_selectors:
            try:
                file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                if file_input.is_enabled():
                    self.scroll_to_element(file_input)
                    file_input.send_keys(image_path)
                    logger.info(f"✅ File uploaded using selector: {selector}")
                    time.sleep(1)  # Wait for upload processing
                    return image_path
            except NoSuchElementException:
                continue
        
        logger.error(f"❌ Could not upload file for variant {variant_id}")
        return None
    
    def submit_form(self):
        """Submit the component form"""
        logger.info("📤 Submitting form...")
        
        current_url = self.get_current_url()
        logger.info(f"🔗 Current URL: {current_url}")
        
        # Find submit button
        submit_btn = self.wait_for_element("#submitBtn")
        self.scroll_to_element(submit_btn)
        
        # Use JavaScript click to avoid interception
        logger.info(f"🖱️  Clicking submit button via JavaScript: #submitBtn")
        self.driver.execute_script("arguments[0].click();", submit_btn)
        
        # Wait for submission and redirect
        logger.info("⏳ Waiting for form submission and redirect...")
        if self.wait_for_url_change(current_url, timeout=15):
            new_url = self.get_current_url()
            logger.info(f"✅ Redirected to: {new_url}")
            
            # Extract component ID from URL
            if "/component/" in new_url:
                component_id = new_url.split("/component/")[-1].split("/")[0]
                logger.info(f"🆔 Component ID: {component_id}")
                return component_id
        
        logger.error("❌ Form submission failed or no redirect occurred")
        return None
    
    def cleanup(self):
        """Clean up resources"""
        self.image_generator.cleanup_images()