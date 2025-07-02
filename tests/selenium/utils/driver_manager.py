"""
WebDriver management utilities
"""
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from config.test_config import TestConfig

logger = logging.getLogger(__name__)

class DriverManager:
    """Manages WebDriver setup and configuration"""
    
    @staticmethod
    def create_chrome_driver(enable_logging=False):
        """Create and configure Chrome WebDriver"""
        try:
            # Set up Chrome options
            chrome_options = Options()
            
            if TestConfig.HEADLESS:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
            
            chrome_options.add_argument(f"--window-size={TestConfig.WINDOW_SIZE[0]},{TestConfig.WINDOW_SIZE[1]}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Enable console logging if requested
            if enable_logging:
                chrome_options.add_argument("--enable-logging")
                chrome_options.add_argument("--log-level=0")
                chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
            
            # For WSL environment
            if 'WSL' in os.environ.get('WSL_DISTRO_NAME', ''):
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
            driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
            
            logger.info("✅ Chrome driver initialized")
            if not TestConfig.HEADLESS:
                logger.info("🖥️  Browser visible - watching test execution...")
            
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create Chrome driver: {e}")
            raise
    
    @staticmethod
    def quit_driver(driver):
        """Safely quit the WebDriver"""
        try:
            if driver:
                driver.quit()
                logger.info("🔴 Browser closed")
        except Exception as e:
            logger.warning(f"⚠️  Error closing driver: {e}")