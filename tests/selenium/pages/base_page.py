"""
Base page object for common functionality
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.test_config import TestConfig

logger = logging.getLogger(__name__)

class BasePage:
    """Base page class with common functionality"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def wait_for_element(self, selector, timeout=None):
        """Wait for element to be present"""
        if timeout is None:
            timeout = TestConfig.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    
    def wait_for_clickable(self, selector, timeout=None):
        """Wait for element to be clickable"""
        if timeout is None:
            timeout = TestConfig.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
    
    def scroll_to_element(self, element):
        """Scroll element into view"""
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)
    
    def highlight_element(self, element, color='red'):
        """Highlight element for visibility"""
        self.driver.execute_script(f"arguments[0].style.border='3px solid {color}'", element)
        time.sleep(0.3)
    
    def slow_type(self, element, text, delay=0.05):
        """Type text slowly"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(delay)
    
    def take_screenshot(self, name):
        """Take and save screenshot"""
        if TestConfig.SAVE_SCREENSHOTS:
            screenshot_path = TestConfig.get_screenshot_path(name)
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        return None
    
    def get_current_url(self):
        """Get current page URL"""
        return self.driver.current_url
    
    def wait_for_url_change(self, current_url, timeout=None):
        """Wait for URL to change from current"""
        if timeout is None:
            timeout = TestConfig.DEFAULT_TIMEOUT
        
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.current_url != current_url
            )
            return True
        except TimeoutException:
            return False