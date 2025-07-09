#!/usr/bin/env python3
"""
Visual Selenium Test: Component Detail Layout from Daily User Perspective

This test evaluates the component detail page layout from the perspective of 
someone who uses the application many hours every day, focusing on:
- Reduced scrolling and eye strain
- Efficient information access
- Screen real estate usage  
- Visual hierarchy and readability
- Workflow efficiency

Test Components:
- Component 2 (as suggested by user)
- Component 217 (with brand associations)
- Different screen sizes (desktop, tablet, mobile)
"""

import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

class DailyUserLayoutTest:
    """Test component detail layout from daily user perspective"""
    
    def __init__(self):
        self.base_url = "http://localhost:6002"
        self.driver = None
        self.test_results = []
        
    def setup_driver(self, window_size=(1920, 1080)):
        """Setup Chrome driver with specific window size"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(window_size[0], window_size[1])
            print(f"✅ Chrome driver initialized with {window_size[0]}x{window_size[1]} resolution")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def capture_layout_screenshot(self, component_id, test_name, delay=3):
        """Capture full page screenshot with highlighting"""
        try:
            url = f"{self.base_url}/component/{component_id}"
            print(f"📸 Loading {url} for {test_name}")
            
            self.driver.get(url)
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "component-detail"))
            )
            
            # Additional wait for Alpine.js and dynamic content
            time.sleep(delay)
            
            # Take screenshot
            screenshot_path = f"/tmp/component_{component_id}_{test_name.replace(' ', '_').lower()}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"   📸 Screenshot saved: {screenshot_path}")
            
            return screenshot_path, url
            
        except Exception as e:
            print(f"   ❌ Screenshot failed: {e}")
            return None, url
    
    def evaluate_layout_metrics(self, component_id, test_name):
        """Evaluate layout from daily user perspective"""
        print(f"\n🔍 EVALUATING: {test_name} (Component {component_id})")
        print("-" * 60)
        
        metrics = {
            'test_name': test_name,
            'component_id': component_id,
            'url': f"{self.base_url}/component/{component_id}",
            'metrics': {}
        }
        
        try:
            # Load page
            self.driver.get(metrics['url'])
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "component-detail"))
            )
            time.sleep(2)
            
            # 1. SCROLLING ANALYSIS
            print("   📏 Analyzing scrolling requirements...")
            body_height = self.driver.execute_script("return document.body.scrollHeight")
            window_height = self.driver.execute_script("return window.innerHeight")
            viewport_usage = (window_height / body_height) * 100
            
            metrics['metrics']['body_height'] = body_height
            metrics['metrics']['window_height'] = window_height
            metrics['metrics']['viewport_usage'] = round(viewport_usage, 1)
            metrics['metrics']['scrolling_required'] = body_height > window_height
            
            print(f"      Body height: {body_height}px")
            print(f"      Window height: {window_height}px") 
            print(f"      Viewport usage: {viewport_usage:.1f}%")
            print(f"      Scrolling required: {'Yes' if body_height > window_height else 'No'}")
            
            # 2. LAYOUT STRUCTURE ANALYSIS
            print("   🏗️ Analyzing layout structure...")
            
            # Check for two-column layout
            grid_elements = self.driver.find_elements(By.CLASS_NAME, "component-content-grid")
            two_column_layout = len(grid_elements) > 0
            
            # Check information sections
            gallery_elements = self.driver.find_elements(By.CLASS_NAME, "component-content__gallery")
            info_elements = self.driver.find_elements(By.CLASS_NAME, "component-content__info")
            tabs_elements = self.driver.find_elements(By.CLASS_NAME, "info-tabs")
            
            metrics['metrics']['two_column_layout'] = two_column_layout
            metrics['metrics']['gallery_section'] = len(gallery_elements) > 0
            metrics['metrics']['info_section'] = len(info_elements) > 0
            metrics['metrics']['tabs_available'] = len(tabs_elements) > 0
            
            print(f"      Two-column layout: {'Yes' if two_column_layout else 'No'}")
            print(f"      Gallery section: {'Found' if len(gallery_elements) > 0 else 'Missing'}")
            print(f"      Info section: {'Found' if len(info_elements) > 0 else 'Missing'}")
            print(f"      Tabs available: {'Yes' if len(tabs_elements) > 0 else 'No'}")
            
            # 3. INFORMATION ACCESSIBILITY
            print("   ℹ️ Analyzing information accessibility...")
            
            # Check if key information is visible without scrolling
            above_fold_elements = self.driver.execute_script("""
                var elements = document.querySelectorAll('.component-header, .component-content__gallery, .nav-tabs-modern');
                var aboveFold = 0;
                elements.forEach(function(el) {
                    var rect = el.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top <= window.innerHeight) {
                        aboveFold++;
                    }
                });
                return aboveFold;
            """)
            
            metrics['metrics']['key_elements_above_fold'] = above_fold_elements
            print(f"      Key elements above fold: {above_fold_elements}")
            
            # 4. BRAND INFORMATION ACCESSIBILITY
            print("   🏷️ Checking brand information accessibility...")
            try:
                brands_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Brands')]")
                brands_tab.click()
                time.sleep(1)
                
                brand_content = self.driver.find_elements(By.CLASS_NAME, "brand-card")
                empty_brand_state = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'No Brands Associated')]")
                
                metrics['metrics']['brands_tab_functional'] = True
                metrics['metrics']['brand_content_available'] = len(brand_content) > 0 or len(empty_brand_state) > 0
                
                print(f"      Brands tab functional: Yes")
                print(f"      Brand content: {'Available' if len(brand_content) > 0 else 'Empty state shown'}")
                
            except Exception as e:
                metrics['metrics']['brands_tab_functional'] = False
                metrics['metrics']['brand_content_available'] = False
                print(f"      Brands tab functional: No ({str(e)[:50]}...)")
            
            # 5. VISUAL HIERARCHY ASSESSMENT
            print("   👁️ Assessing visual hierarchy...")
            
            # Check contrast and readability
            contrast_elements = self.driver.execute_script("""
                var elements = document.querySelectorAll('h1, h2, h3, .nav-link, .brand-name');
                return elements.length;
            """)
            
            metrics['metrics']['hierarchy_elements'] = contrast_elements
            print(f"      Hierarchy elements found: {contrast_elements}")
            
            # 6. WORKFLOW EFFICIENCY
            print("   ⚡ Evaluating workflow efficiency...")
            
            # Test tab switching speed
            start_time = time.time()
            try:
                tabs = self.driver.find_elements(By.CSS_SELECTOR, ".nav-tabs-modern .nav-link")
                for i, tab in enumerate(tabs[:3]):  # Test first 3 tabs
                    tab.click()
                    time.sleep(0.5)
                
                tab_switching_time = time.time() - start_time
                metrics['metrics']['tab_switching_time'] = round(tab_switching_time, 2)
                metrics['metrics']['tabs_responsive'] = tab_switching_time < 3.0
                
                print(f"      Tab switching time: {tab_switching_time:.2f}s")
                print(f"      Tabs responsive: {'Yes' if tab_switching_time < 3.0 else 'No'}")
                
            except Exception as e:
                metrics['metrics']['tab_switching_time'] = None
                metrics['metrics']['tabs_responsive'] = False
                print(f"      Tab switching test failed: {str(e)[:50]}...")
            
            # 7. OVERALL DAILY USER SCORE
            score = self.calculate_daily_user_score(metrics['metrics'])
            metrics['metrics']['daily_user_score'] = score
            
            print(f"\n   📊 DAILY USER SCORE: {score}/100")
            self.print_score_breakdown(score)
            
        except Exception as e:
            print(f"   ❌ Layout evaluation failed: {e}")
            metrics['metrics']['error'] = str(e)
        
        return metrics
    
    def calculate_daily_user_score(self, metrics):
        """Calculate overall score from daily user perspective (0-100)"""
        score = 0
        
        # Viewport efficiency (30 points)
        if metrics.get('viewport_usage', 0) > 80:
            score += 30
        elif metrics.get('viewport_usage', 0) > 60:
            score += 20
        elif metrics.get('viewport_usage', 0) > 40:
            score += 10
        
        # Layout structure (25 points)
        if metrics.get('two_column_layout'):
            score += 15
        if metrics.get('gallery_section') and metrics.get('info_section'):
            score += 10
        
        # Information accessibility (20 points)
        if metrics.get('key_elements_above_fold', 0) >= 2:
            score += 10
        if metrics.get('brands_tab_functional'):
            score += 10
        
        # Workflow efficiency (15 points)
        if metrics.get('tabs_responsive'):
            score += 10
        if metrics.get('tabs_available'):
            score += 5
        
        # Reduced scrolling (10 points)
        if not metrics.get('scrolling_required', True):
            score += 10
        elif metrics.get('viewport_usage', 0) > 70:
            score += 5
        
        return min(score, 100)
    
    def print_score_breakdown(self, score):
        """Print detailed score breakdown"""
        if score >= 90:
            print("      🟢 EXCELLENT - Ideal for daily use")
        elif score >= 70:
            print("      🟡 GOOD - Suitable for daily use with minor improvements")
        elif score >= 50:
            print("      🟠 FAIR - Usable but may cause fatigue in daily use")
        else:
            print("      🔴 POOR - Not suitable for daily use, major improvements needed")
    
    def run_comprehensive_test(self):
        """Run comprehensive layout test from daily user perspective"""
        print("🚀 COMPONENT DETAIL LAYOUT - DAILY USER PERSPECTIVE TEST")
        print("=" * 70)
        print("Evaluating layout efficiency for users who spend hours daily in the app")
        print("=" * 70)
        
        # Test scenarios
        test_scenarios = [
            {
                'component_id': 2,
                'name': 'Component 2 - User Suggested Test Case',
                'window_size': (1920, 1080),
                'description': 'Primary test case suggested by user'
            },
            {
                'component_id': 217,
                'name': 'Component 217 - With Brand Data',
                'window_size': (1920, 1080),
                'description': 'Component with brand associations to test full functionality'
            },
            {
                'component_id': 2,
                'name': 'Component 2 - Laptop Screen',
                'window_size': (1366, 768),
                'description': 'Common laptop resolution for daily work'
            },
            {
                'component_id': 2,
                'name': 'Component 2 - Large Desktop',
                'window_size': (2560, 1440),
                'description': 'Large desktop monitor for power users'
            }
        ]
        
        all_results = []
        
        for scenario in test_scenarios:
            print(f"\n🎯 TESTING: {scenario['name']}")
            print(f"   Resolution: {scenario['window_size'][0]}x{scenario['window_size'][1]}")
            print(f"   {scenario['description']}")
            
            # Setup driver for this scenario
            if not self.setup_driver(scenario['window_size']):
                continue
            
            try:
                # Capture screenshot
                screenshot, url = self.capture_layout_screenshot(
                    scenario['component_id'], 
                    scenario['name']
                )
                
                # Evaluate metrics
                metrics = self.evaluate_layout_metrics(
                    scenario['component_id'],
                    scenario['name']
                )
                
                metrics['scenario'] = scenario
                metrics['screenshot'] = screenshot
                all_results.append(metrics)
                
            except Exception as e:
                print(f"   ❌ Test scenario failed: {e}")
                
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
        
        # Generate comprehensive report
        self.generate_daily_user_report(all_results)
        
        return all_results
    
    def generate_daily_user_report(self, results):
        """Generate comprehensive daily user experience report"""
        print("\n" + "=" * 70)
        print("📊 DAILY USER EXPERIENCE REPORT")
        print("=" * 70)
        
        total_score = 0
        scenario_count = 0
        
        for result in results:
            if 'metrics' in result and 'daily_user_score' in result['metrics']:
                score = result['metrics']['daily_user_score']
                total_score += score
                scenario_count += 1
                
                print(f"\n🎯 {result['test_name']}")
                print(f"   Score: {score}/100")
                print(f"   Viewport Usage: {result['metrics'].get('viewport_usage', 'N/A')}%")
                print(f"   Two-Column Layout: {'✅' if result['metrics'].get('two_column_layout') else '❌'}")
                print(f"   Scrolling Required: {'❌' if result['metrics'].get('scrolling_required') else '✅'}")
                print(f"   Brands Functional: {'✅' if result['metrics'].get('brands_tab_functional') else '❌'}")
        
        if scenario_count > 0:
            avg_score = total_score / scenario_count
            print(f"\n🏆 OVERALL DAILY USER SCORE: {avg_score:.1f}/100")
            
            if avg_score >= 80:
                print("🟢 VERDICT: Layout is EXCELLENT for daily use")
                print("   ✅ Users can work efficiently for hours without strain")
                print("   ✅ Information is well-organized and accessible")
                print("   ✅ Minimal scrolling required")
            elif avg_score >= 60:
                print("🟡 VERDICT: Layout is GOOD for daily use")
                print("   ✅ Generally efficient but some improvements possible")
                print("   ⚠️ May benefit from minor UX enhancements")
            else:
                print("🔴 VERDICT: Layout needs IMPROVEMENT for daily use")
                print("   ❌ May cause user fatigue during extended use")
                print("   ❌ Requires significant scrolling or navigation")
                print("   🔧 Recommend layout redesign")
        
        print("\n💡 RECOMMENDATIONS FOR DAILY USERS:")
        print("   1. Two-column layout reduces vertical scrolling")
        print("   2. Sticky gallery keeps images visible while browsing info")
        print("   3. Compact workflow section saves vertical space")
        print("   4. Responsive design adapts to different screen sizes")
        print("   5. Brands tab integration improves information access")
        
        return avg_score if scenario_count > 0 else 0

def main():
    """Run the daily user perspective test"""
    tester = DailyUserLayoutTest()
    
    print("⚠️ IMPORTANT: This test requires Chrome browser and component detail pages to be accessible")
    print("🔧 Make sure the application is running on http://localhost:6002")
    
    try:
        results = tester.run_comprehensive_test()
        print(f"\n✅ Test completed. {len(results)} scenarios evaluated.")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    finally:
        if tester.driver:
            tester.driver.quit()

if __name__ == "__main__":
    main()