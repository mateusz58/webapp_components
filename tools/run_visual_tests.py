#!/usr/bin/env python3
"""
🎬 Visual Selenium Test Runner
Run Selenium tests with VISIBLE browser to watch automation in action!
"""

import subprocess
import sys
import time
import requests
from urllib.parse import urlparse

def check_application_running(url="http://localhost:6002"):
    """Check if the application is running"""
    print(f"🔍 Checking if application is running at {url}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Application is running!")
            return True
        else:
            print(f"⚠️ Application responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Application is not running: {e}")
        return False

def run_visual_test(test_path, test_name="Visual Selenium Test"):
    """Run a specific visual test"""
    print(f"\n🎬 Starting {test_name}...")
    print(f"📁 Test path: {test_path}")
    print(f"👁️  Browser will open - watch the automation!")
    print(f"⏱️  Tests may take 30-60 seconds to complete")
    
    # Run the test with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        test_path, 
        "-v", "-s",  # Verbose and no capture (shows print statements)
        "--tb=short"  # Short traceback on failures
    ]
    
    try:
        print(f"\n🚀 Running command: {' '.join(cmd)}")
        print(f"=" * 60)
        
        result = subprocess.run(cmd, check=False)
        
        print(f"=" * 60)
        if result.returncode == 0:
            print(f"✅ {test_name} completed successfully!")
        else:
            print(f"⚠️ {test_name} completed with issues (return code: {result.returncode})")
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main visual test runner"""
    print("""
🎬 VISUAL SELENIUM TEST RUNNER
=====================================
This will run Selenium tests with a VISIBLE browser
so you can watch the automation in action!

Requirements:
- Application running at http://localhost:6002
- Chrome/Chromium browser installed
- Virtual environment activated
""")
    
    # Check if application is running
    if not check_application_running():
        print(f"""
❌ Application is not running!

Please start your application first:
    ./start.sh

Then run this script again.
""")
        return False
    
    # Menu of available visual tests
    visual_tests = [
        {
            "name": "Component Creation Workflow",
            "path": "tests/selenium/test_component_creation_workflow.py",
            "description": "Watch form navigation, filling, and validation"
        },
        {
            "name": "Picture Upload Visual Testing", 
            "path": "tests/selenium/test_picture_upload_visual.py",
            "description": "Watch picture upload interactions and gallery behavior"
        },
        {
            "name": "Comprehensive Workflows",
            "path": "tests/selenium/test_comprehensive_component_workflows.py", 
            "description": "Watch complete user workflows and responsive design"
        },
        {
            "name": "All Visual Tests",
            "path": "tests/selenium/test_component_creation_workflow.py tests/selenium/test_picture_upload_visual.py",
            "description": "Run multiple visual tests in sequence"
        }
    ]
    
    print(f"\n📋 Available Visual Tests:")
    for i, test in enumerate(visual_tests, 1):
        print(f"  {i}. {test['name']}")
        print(f"     {test['description']}")
    
    # Get user choice
    try:
        choice = input(f"\n🎯 Choose a test to run (1-{len(visual_tests)}, or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            print(f"👋 Goodbye!")
            return True
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(visual_tests):
            selected_test = visual_tests[choice_num - 1]
            
            print(f"\n🎬 You selected: {selected_test['name']}")
            print(f"📝 Description: {selected_test['description']}")
            
            # Confirm before running
            confirm = input(f"\n▶️  Ready to start? Browser will open automatically (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                print(f"\n🚀 Starting visual test in 3 seconds...")
                time.sleep(3)
                
                # Run the selected test
                success = run_visual_test(selected_test['path'], selected_test['name'])
                
                if success:
                    print(f"\n🎉 Visual test completed successfully!")
                    print(f"💡 You can run this test again anytime with:")
                    print(f"   python run_visual_tests.py")
                else:
                    print(f"\n⚠️  Visual test completed with issues")
                    print(f"💡 Check the output above for details")
                
                return success
            else:
                print(f"❌ Test cancelled by user")
                return True
        else:
            print(f"❌ Invalid choice: {choice}")
            return False
            
    except ValueError:
        print(f"❌ Invalid input. Please enter a number.")
        return False
    except KeyboardInterrupt:
        print(f"\n👋 Goodbye!")
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n👋 Goodbye!")
        sys.exit(0)