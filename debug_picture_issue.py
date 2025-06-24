#!/usr/bin/env python3
"""
Debug script to analyze the picture visibility issue by inspecting HTTP responses.
This script tests the actual data flow without requiring browser automation.
"""

import requests
import json
import time
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PictureDebugger:
    def __init__(self):
        self.app_url = "http://localhost:6002"
        self.session = requests.Session()
        
    def test_app_accessibility(self):
        """Test if the application is accessible"""
        try:
            response = self.session.get(self.app_url)
            if response.status_code == 200:
                logger.info("✅ Application is accessible")
                return True
            else:
                logger.error(f"❌ Application returned status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot access application: {e}")
            return False
    
    def get_component_list(self):
        """Get the list of existing components"""
        try:
            response = self.session.get(f"{self.app_url}/components")
            if response.status_code == 200:
                logger.info("✅ Component list page accessible")
                # Look for component links in the response
                component_links = []
                if '/component/' in response.text:
                    import re
                    # Find component detail links
                    pattern = r'/component/(\d+)'
                    matches = re.findall(pattern, response.text)
                    component_links = list(set(matches))  # Remove duplicates
                    logger.info(f"Found {len(component_links)} components: {component_links}")
                return component_links
            else:
                logger.error(f"❌ Component list returned status code: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting component list: {e}")
            return []
    
    def analyze_component_detail(self, component_id):
        """Analyze a component detail page for picture data"""
        url = f"{self.app_url}/component/{component_id}"
        logger.info(f"Analyzing component {component_id}...")
        
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"❌ Component {component_id} returned status code: {response.status_code}")
                return None
            
            html_content = response.text
            
            # Analyze the JavaScript data in the template
            variant_data = self.extract_variant_data(html_content)
            
            # Check for picture URLs
            picture_urls = self.extract_picture_urls(html_content)
            
            # Test picture URL accessibility
            accessible_urls = self.test_picture_urls(picture_urls)
            
            result = {
                'component_id': component_id,
                'has_variants': len(variant_data) > 0,
                'variant_count': len(variant_data),
                'total_pictures': sum(len(v.get('images', [])) for v in variant_data),
                'picture_urls': picture_urls,
                'accessible_pictures': accessible_urls,
                'variants': variant_data
            }
            
            logger.info(f"Component {component_id} analysis:")
            logger.info(f"  - Variants: {result['variant_count']}")
            logger.info(f"  - Total pictures: {result['total_pictures']}")
            logger.info(f"  - Accessible pictures: {len(accessible_urls)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing component {component_id}: {e}")
            return None
    
    def extract_variant_data(self, html_content):
        """Extract variant data from the JavaScript in the template"""
        import re
        
        # Look for the variants array in the JavaScript
        pattern = r'variants:\s*\[(.*?)\]'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if not match:
            logger.warning("No variants data found in JavaScript")
            return []
        
        variants_text = match.group(1)
        
        # Count variants by looking for variant objects
        variant_pattern = r'\{\s*id:\s*(\d+).*?images:\s*\[(.*?)\]'
        variant_matches = re.findall(variant_pattern, variants_text, re.DOTALL)
        
        variants = []
        for variant_id, images_text in variant_matches:
            # Count images in this variant
            image_pattern = r'\{\s*id:\s*(\d+).*?url:\s*[\'"]([^\'"]+)[\'"]'
            image_matches = re.findall(image_pattern, images_text, re.DOTALL)
            
            variant_info = {
                'id': int(variant_id),
                'image_count': len(image_matches),
                'images': [{'id': int(img_id), 'url': url} for img_id, url in image_matches]
            }
            variants.append(variant_info)
        
        return variants
    
    def extract_picture_urls(self, html_content):
        """Extract all picture URLs from the HTML content"""
        import re
        
        # Look for WebDAV URLs
        webdav_pattern = r'http://31\.182\.67\.115/webdav/components/[^\s\'"<>]+'
        webdav_urls = re.findall(webdav_pattern, html_content)
        
        # Look for any other picture URLs
        general_pattern = r'[\'"]([^\'"]*\.(?:jpg|jpeg|png|gif|webp))[\'"]'
        general_urls = re.findall(general_pattern, html_content, re.IGNORECASE)
        
        all_urls = list(set(webdav_urls + general_urls))
        return [url for url in all_urls if 'webdav' in url or 'components' in url]
    
    def test_picture_urls(self, urls):
        """Test if picture URLs are accessible"""
        accessible = []
        
        for url in urls:
            try:
                # Use HEAD request to check accessibility without downloading
                response = self.session.head(url, timeout=5)
                if response.status_code == 200:
                    accessible.append(url)
                    logger.info(f"✅ Picture accessible: {url}")
                else:
                    logger.warning(f"⚠️  Picture not accessible (status {response.status_code}): {url}")
            except Exception as e:
                logger.warning(f"⚠️  Picture check failed: {url} - {e}")
        
        return accessible
    
    def simulate_component_creation_flow(self):
        """Simulate the component creation flow to understand the timing"""
        logger.info("=== Simulating Component Creation Flow ===")
        
        # Step 1: Get the new component form
        try:
            form_response = self.session.get(f"{self.app_url}/component/new")
            if form_response.status_code != 200:
                logger.error(f"❌ Cannot access new component form: {form_response.status_code}")
                return
            
            logger.info("✅ New component form accessible")
            
            # Extract CSRF token if needed
            csrf_token = self.extract_csrf_token(form_response.text)
            
        except Exception as e:
            logger.error(f"❌ Error accessing new component form: {e}")
            return
        
        # For debugging purposes, let's analyze the form structure
        self.analyze_form_structure(form_response.text)
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from form"""
        import re
        pattern = r'name=[\'"]csrf_token[\'"].*?value=[\'"]([^\'"]+)[\'"]'
        match = re.search(pattern, html_content)
        if match:
            token = match.group(1)
            logger.info(f"✅ CSRF token found: {token[:20]}...")
            return token
        else:
            logger.warning("⚠️  No CSRF token found")
            return None
    
    def analyze_form_structure(self, html_content):
        """Analyze the structure of the component creation form"""
        import re
        
        logger.info("Analyzing form structure...")
        
        # Look for form fields
        field_patterns = {
            'product_number': r'name=[\'"]product_number[\'"]',
            'description': r'name=[\'"]description[\'"]',
            'component_type_id': r'name=[\'"]component_type_id[\'"]',
            'supplier_id': r'name=[\'"]supplier_id[\'"]',
            'variant_fields': r'name=[\'"][^\'\"]*variant[^\'\"]*[\'"]',
            'file_inputs': r'type=[\'"]file[\'"].*?name=[\'"]([^\'"]+)[\'"]'
        }
        
        for field_name, pattern in field_patterns.items():
            matches = re.findall(pattern, html_content)
            if matches:
                logger.info(f"✅ Found {field_name}: {len(matches) if isinstance(matches, list) else 1}")
                if field_name in ['variant_fields', 'file_inputs']:
                    for match in matches[:3]:  # Show first 3
                        logger.info(f"    - {match}")
            else:
                logger.warning(f"⚠️  {field_name} not found")
    
    def run_comprehensive_debug(self):
        """Run comprehensive debugging analysis"""
        logger.info("=== Starting Comprehensive Picture Debug Analysis ===")
        
        # Test 1: Basic accessibility
        if not self.test_app_accessibility():
            return
        
        # Test 2: Get existing components
        component_ids = self.get_component_list()
        
        if not component_ids:
            logger.info("No existing components found - analyzing form structure")
            self.simulate_component_creation_flow()
            return
        
        # Test 3: Analyze existing components
        logger.info(f"Analyzing {len(component_ids)} existing components...")
        
        results = []
        for component_id in component_ids[:3]:  # Analyze first 3 components
            result = self.analyze_component_detail(component_id)
            if result:
                results.append(result)
        
        # Test 4: Summary analysis
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results):
        """Generate a summary report of the analysis"""
        logger.info("=== SUMMARY REPORT ===")
        
        if not results:
            logger.info("❌ No components analyzed")
            return
        
        total_components = len(results)
        components_with_variants = sum(1 for r in results if r['has_variants'])
        components_with_pictures = sum(1 for r in results if r['total_pictures'] > 0)
        total_pictures = sum(r['total_pictures'] for r in results)
        total_accessible = sum(len(r['accessible_pictures']) for r in results)
        
        logger.info(f"📊 Components analyzed: {total_components}")
        logger.info(f"📊 Components with variants: {components_with_variants}")
        logger.info(f"📊 Components with pictures: {components_with_pictures}")
        logger.info(f"📊 Total pictures found: {total_pictures}")
        logger.info(f"📊 Accessible pictures: {total_accessible}")
        
        if total_pictures > 0:
            accessibility_rate = (total_accessible / total_pictures) * 100
            logger.info(f"📊 Picture accessibility rate: {accessibility_rate:.1f}%")
            
            if accessibility_rate < 100:
                logger.warning("⚠️  Some pictures are not accessible!")
            else:
                logger.info("✅ All pictures are accessible")
        
        # Detailed breakdown
        for result in results:
            component_id = result['component_id']
            if result['total_pictures'] > 0:
                accessible_count = len(result['accessible_pictures'])
                rate = (accessible_count / result['total_pictures']) * 100
                status = "✅" if rate == 100 else "⚠️ "
                logger.info(f"{status} Component {component_id}: {accessible_count}/{result['total_pictures']} pictures accessible ({rate:.0f}%)")

if __name__ == "__main__":
    debugger = PictureDebugger()
    results = debugger.run_comprehensive_debug()
    
    if results:
        print(f"\n🔍 Analysis complete - checked {len(results)} components")
        print("📝 Check the log output above for detailed findings")
    else:
        print("\n❌ Analysis failed or no data found")
        print("💡 Make sure the application is running and has some test components")