"""
Test image generation utilities
"""
import os
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from config.test_config import TestConfig

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Generates test images for component variants"""
    
    def __init__(self):
        self.created_images = []
    
    def create_test_image(self, color_name, color_code, size=None):
        """Create a test image with specified color"""
        if size is None:
            size = TestConfig.TEST_IMAGE_SIZE
            
        try:
            # Create image
            img = Image.new('RGB', size, color_code)
            
            # Add text and graphics
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Add color name text
            text = f"TEST\\n{color_name.upper()}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            # Add text with shadow
            draw.text((x+2, y+2), text, fill='black', font=font, align='center')
            draw.text((x, y), text, fill='white', font=font, align='center')
            
            # Add border
            draw.rectangle([0, 0, size[0]-1, size[1]-1], outline='white', width=3)
            
            # Save to file in current directory (more accessible to Chrome)
            filename = f"test_image_{color_name.lower()}_{int(time.time())}.jpg"
            temp_path = os.path.join(TestConfig.TEMP_IMAGE_DIR, filename)
            img.save(temp_path, 'JPEG', quality=95)
            os.chmod(temp_path, 0o644)  # Ensure readable permissions
            
            # Track created image
            self.created_images.append(temp_path)
            
            logger.info(f"📸 Created test image: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create image for {color_name}: {e}")
            return None
    
    def cleanup_images(self):
        """Clean up created test images"""
        for image_path in self.created_images:
            try:
                if os.path.exists(image_path):
                    os.unlink(image_path)
                    logger.info(f"🗑️  Deleted test image: {image_path}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to delete {image_path}: {e}")
        
        # Also clean any test_image_* files in current directory
        try:
            for file in os.listdir(TestConfig.TEMP_IMAGE_DIR):
                if file.startswith("test_image_") and file.endswith(".jpg"):
                    file_path = os.path.join(TestConfig.TEMP_IMAGE_DIR, file)
                    os.unlink(file_path)
                    logger.info(f"🗑️  Deleted remaining test image: {file}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to clean remaining images: {e}")
        
        self.created_images.clear()