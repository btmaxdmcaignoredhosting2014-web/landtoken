from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import re
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ============== COOKIES ==============
FIXED_COOKIES = {
    'sso': os.environ.get('SSO_COOKIE', ''),
    'citizen': os.environ.get('CITIZEN_COOKIE', ''),
    'cf_clearance': os.environ.get('CF_CLEARANCE_COOKIE', '')
}

# ============== CHROME SETUP ==============
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # ✅ Render-এ headless লাগবে
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,800')
    # Anti-detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Render-এ Chrome pre-installed থাকে
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# ============== REACT SELECT HANDLER ==============
def click_react_select(driver, field_name, value, wait_time=3):
    try:
        inputs = driver.find_elements(By.CSS_SELECTOR, f"input[name='{field_name}']")
        for inp in inputs:
            try:
                container = inp.find_element(By.XPATH, "ancestor::div[contains(@class, 'css-b62m3t-container')]")
            except:
                container = inp.find_element(By.XPATH, "..")
            
            container.click()
            time.sleep(0.5)
            actions = ActionChains(driver)
            actions.send_keys(str(value)).pause(0.5).send_keys(u'\ue007').perform()
            time.sleep(wait_time)
            return True
    except Exception as e:
        app.logger.error(f"Dropdown error {field_name}: {e}")
    return False

# ============== MAIN JWT CAPTURE ==============
def capture_jwt(params):
    driver = None
    try:
        driver = get_driver()
        app.logger.info("Chrome started")
        
        # Step 1: Set cookies
        driver.get('https://portal.ldtax.gov.bd')
        time.sleep(2)
        
        for name, value in FIXED_COOKIES.items():
            if value:
                try:
                    driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': 'portal.ldtax.gov.bd',
                        'path': '/'
                    })
                except Exception as e:
                    app.logger.warning(f"Cookie error: {e}")
        
        # Step 2: Navigate to payment
        driver.get('https://portal.ldtax.gov.bd/citizen/representative-payment')
        time.sleep(3)
        
        if 'login' in driver.current_url:
            return {'success': False, 'error': 'Cookies expired - update SSO_COOKIE'}
        
        # Step 3: Fill dropdowns
        dropdown_fields = [
            ('division_id', params['division_id'], 2),
            ('district_id', params['district_id'], 2),
            ('upazila_id', params['upazila_id'], 2),
            ('mouja_id', params['mouja_id'], 2),
        ]
        
        for field_name, value, wait in dropdown_fields:
            if not click_react_select(driver, field_name, value, wait):
                return {'success': False, 'error': f'Failed to select {field_name}'}
        
        # Step 4: Fill text fields
        try:
            khotian = driver.find_element(By.NAME, 'khotian_no')
            khotian.clear()
            khotian.send_keys(params['khotian_no'])
        except Exception as e:
            return {'success': False, 'error': f'Khotian field error: {e}'}
        
        try:
            holding = driver.find_element(By.NAME, 'holding_no')
            holding.clear()
            holding.send_keys(params['holding_no'])
        except Exception as e:
            return {'success': False, 'error': f'Holding field error: {e}'}
        
        # Step 5: Click search
        try:
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                if 'অনুসন্ধান' in btn.text:
                    btn.click()
                    break
        except:
            driver.execute_script("""
                var btns = document.querySelectorAll('button');
                for(var i=0; i<btns.length; i++) {
                    if(btns[i].textContent.includes('অনুসন্ধান')) btns[i].click();
                }
            """)
        
        time.sleep(5)
        
        # Step 6: Extract JWT
        current_url = driver.current_url
        
        if 'holding/eyJ' in current_url:
            match = re.search(r'holding/([^.]+\.[^.]+\.[^?]+)', current_url)
            if match:
                return {
                    'success': True,
                    'jwt_token': match.group(1),
                    'jwt_link': current_url,
                    'source': 'url'
                }
        
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'holding/eyJ')]")
        for link in links:
            href = link.get_attribute('href')
            match = re.search(r'holding/([^.]+\.[^.]+\.[^?]+)', href)
            if match:
                return {
                    'success': True,
                    'jwt_token': match.group(1),
                    'jwt_link': href,
                    'source': 'link'
                }
        
        page = driver.page_source
        matches = re.findall(r'holding/([^.]+\.[^.]+\.[^?]+)', page)
        if matches:
            return {
                'success': True,
                'jwt_token': matches[0],
                'jwt_link': f"https://portal.ldtax.gov.bd/citizen/holding/{matches[0]}?representativepayment=1",
                'source': 'page_source'
            }
        
        return {'success': False, 'error': 'JWT not found', 'url': current_url}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        if driver:
            driver.quit()

# ============== API ENDPOINTS ==============
@app.route('/')
def home():
    return jsonify({
        'status': 'JWT Capture API is running',
        'endpoints': {
            'POST /capture': 'Capture JWT token',
            'GET /health': 'Health check'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/capture', methods=['POST'])
def capture():
    data = request.get_json() or request.form.to_dict()
    
    required = ['division_id', 'district_id', 'upazila_id', 'mouja_id', 'khotian_no', 'holding_no']
    missing = [f for f in required if f not in data or not data[f]]
    
    if missing:
        return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400
    
    params = {
        'division_id': int(data['division_id']),
        'district_id': int(data['district_id']),
        'upazila_id': int(data['upazila_id']),
        'mouja_id': int(data['mouja_id']),
        'khotian_no': str(data['khotian_no']),
        'holding_no': str(data['holding_no'])
    }
    
    result = capture_jwt(params)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
