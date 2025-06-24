"""
Selenium test configuration
"""
import os

class TestConfig:
    """Test configuration settings"""
    
    # Application settings
    APP_URL = "http://localhost:6002"
    
    # Browser settings
    BROWSER = "chrome"
    HEADLESS = False  # Set to True for CI/CD
    WINDOW_SIZE = (1920, 1080)
    
    # Timeouts
    DEFAULT_TIMEOUT = 10
    PAGE_LOAD_TIMEOUT = 30
    IMPLICIT_WAIT = 5
    
    # Screenshots
    SCREENSHOT_DIR = "/tmp"
    SAVE_SCREENSHOTS = True
    
    # Test data
    TEST_IMAGE_SIZE = (400, 400)
    TEST_COLORS = {
        'red': '#FF0000',
        'blue': '#0000FF', 
        'green': '#00FF00',
        'yellow': '#FFFF00',
        'purple': '#800080',
        'orange': '#FFA500'
    }
    
    # File paths
    TEMP_IMAGE_DIR = os.getcwd()  # Current directory for better Chrome access
    
    @classmethod
    def get_screenshot_path(cls, name):
        """Get full path for screenshot"""
        timestamp = int(__import__('time').time())
        return f"{cls.SCREENSHOT_DIR}/{name}_{timestamp}.png"