#!/usr/bin/env python3
"""
Test bulk deletion functionality after CSRF token fix
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_bulk_deletion_csrf_fix():
    """Test that bulk deletion works with CSRF token fix"""
    
    # Set up Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to components page
        driver.get("http://localhost:6002/components")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Setup network monitoring with more detailed logging
        driver.execute_script("""
            window.capturedRequests = [];
            window.originalFetch = fetch;
            
            window.fetch = function(...args) {
                const request = {
                    url: args[0],
                    method: args[1]?.method || 'GET',
                    headers: args[1]?.headers || {},
                    body: args[1]?.body || null,
                    timestamp: new Date().toISOString()
                };
                
                console.log('🌐 Fetch Request:', request);
                window.capturedRequests.push(request);
                
                return window.originalFetch.apply(this, args).then(response => {
                    console.log('🌐 Fetch Response:', response.status, response.statusText);
                    return response;
                }).catch(error => {
                    console.error('🌐 Fetch Error:', error);
                    throw error;
                });
            };
            
            // Also monitor Alpine.js bulkAction calls
            window.bulkActionCalls = [];
            window.originalConsoleLog = console.log;
            console.log = function(...args) {
                if (args[0] && args[0].includes('bulkAction')) {
                    window.bulkActionCalls.push({
                        args: args,
                        timestamp: new Date().toISOString()
                    });
                }
                return window.originalConsoleLog.apply(this, args);
            };
        """)
        
        # Find component checkboxes
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not(#selectAll)")
        print(f"🔍 Found {len(checkboxes)} component checkboxes")
        
        if len(checkboxes) < 2:
            print("❌ Need at least 2 components for bulk deletion test")
            return
        
        # Select first 2 components using JavaScript
        selected_count = 0
        for i, checkbox in enumerate(checkboxes[:2]):
            if checkbox.is_displayed() and checkbox.is_enabled():
                # Scroll to checkbox
                driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                time.sleep(0.5)
                
                # Click checkbox using JavaScript
                driver.execute_script("arguments[0].click();", checkbox)
                selected_count += 1
                print(f"☑️ Selected component {selected_count}")
                
                if selected_count >= 2:
                    break
        
        print(f"✅ Selected {selected_count} components")
        
        # Wait for bulk actions to appear
        time.sleep(2)
        
        # Test the bulk deletion by calling the function directly
        print("🧪 Testing bulk deletion via JavaScript")
        
        # First check if bulk delete button exists and is clickable
        bulk_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-danger-modern")
        print(f"🔍 Found {len(bulk_buttons)} bulk delete buttons")
        
        delete_button = None
        for btn in bulk_buttons:
            if btn.is_displayed() and "Delete" in btn.text:
                delete_button = btn
                break
        
        # Check if components are properly selected in Alpine.js
        selection_check = driver.execute_script("""
            const dashboard = document.querySelector('[x-data]');
            if (dashboard && dashboard._x_dataStack) {
                const alpineData = dashboard._x_dataStack[0];
                return {
                    selectedComponents: alpineData.selectedComponents || [],
                    hasSelectedComponents: alpineData.selectedComponents && alpineData.selectedComponents.length > 0
                };
            }
            return { selectedComponents: [], hasSelectedComponents: false };
        """)
        
        print(f"🔍 Alpine.js selection status: {selection_check}")
        
        if delete_button:
            print(f"✅ Found visible bulk delete button: '{delete_button.text}'")
            
            # If no components selected in Alpine.js, try to manually add them
            if not selection_check['hasSelectedComponents']:
                print("⚠️ No components selected in Alpine.js, manually adding selection")
                # Get component IDs from checkboxes
                component_ids = driver.execute_script("""
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]:not(#selectAll)');
                    const ids = [];
                    checkboxes.forEach(cb => {
                        if (cb.checked && cb.value) {
                            ids.push(parseInt(cb.value));
                        }
                    });
                    return ids;
                """)
                
                print(f"📋 Component IDs from checkboxes: {component_ids}")
                
                # Manually set selected components in Alpine.js
                driver.execute_script(f"""
                    const dashboard = document.querySelector('[x-data]');
                    if (dashboard && dashboard._x_dataStack) {{
                        const alpineData = dashboard._x_dataStack[0];
                        alpineData.selectedComponents = {component_ids};
                        console.log('Manually set selectedComponents:', alpineData.selectedComponents);
                    }}
                """)
            
            # Trigger the Alpine.js click event properly
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('click', { bubbles: true }));
            """, delete_button)
            result = "Bulk delete button clicked with Alpine.js event"
        else:
            # Try to call bulkAction function directly
            result = driver.execute_script("""
                // Find the dashboard component
                const dashboard = document.querySelector('[x-data]');
                if (dashboard && dashboard._x_dataStack) {
                    const alpineData = dashboard._x_dataStack[0];
                    if (alpineData && alpineData.bulkAction) {
                        try {
                            alpineData.bulkAction('delete');
                            return 'Bulk action called successfully';
                        } catch (error) {
                            return 'Error calling bulk action: ' + error.message;
                        }
                    }
                }
                return 'Could not find dashboard component';
            """)
        
        print(f"📋 JavaScript result: {result}")
        
        # Handle confirmation dialog
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"🚨 Confirmation dialog: {alert_text}")
            alert.accept()
            print("✅ Confirmation accepted")
        except:
            print("⚠️ No confirmation dialog appeared")
        
        # Wait for request to complete
        time.sleep(5)
        
        # Check captured requests
        requests = driver.execute_script("return window.capturedRequests || [];")
        print(f"📊 Captured {len(requests)} requests")
        
        bulk_requests = [r for r in requests if 'bulk-delete' in r['url']]
        print(f"🗑️ Bulk delete requests: {len(bulk_requests)}")
        
        for req in bulk_requests:
            print(f"🗑️ {req['method']} {req['url']}")
            if req.get('body'):
                print(f"📦 Request body: {req['body']}")
        
        # Check bulk action calls
        bulk_action_calls = driver.execute_script("return window.bulkActionCalls || [];")
        print(f"📱 Bulk action calls: {len(bulk_action_calls)}")
        
        for call in bulk_action_calls:
            print(f"📱 {call['args']}")
        
        # Check all console logs for debugging
        console_logs = driver.get_log('browser')
        print(f"📝 All console logs: {len(console_logs)}")
        
        for log in console_logs:
            if 'bulk' in log['message'].lower() or 'fetch' in log['message'].lower():
                print(f"📝 {log['level']}: {log['message']}")
        
        # Check browser console for errors
        logs = driver.get_log('browser')
        error_logs = [log for log in logs if log['level'] == 'SEVERE']
        print(f"🔴 Console errors: {len(error_logs)}")
        
        for log in error_logs:
            print(f"🔴 {log['message']}")
        
        # Check if bulk deletion was successful
        if bulk_requests:
            print("🎉 SUCCESS: Bulk deletion request was made!")
        else:
            print("❌ FAILED: No bulk deletion request was captured")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_bulk_deletion_csrf_fix()