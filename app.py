# ============================================
# app.py - JWT Capture API for Render Docker
# ============================================

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import re
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ============== HARDCODED COOKIES ==============
FIXED_COOKIES = {
    'sso': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5YWE0NjczYi02OTIzLTQ4NTUtOWZjOS1mZjU2YjA0ZGJkZjMiLCJqdGkiOiIwNTVjNWE1Y2VkZDk0OTY1NzFiZDNjZThmM2Q3Mzc2ODU2NjVjNDJjYTZkNzkxN2U0ZGQ2MjE1MzEzNTEwZjQ5YmQwMDNhM2MwODY3ZGY5NCIsImlhdCI6MTc4MjUzNzE5My4yMzI2OTksIm5iZiI6MTc4MjUzNzE5My4yMzI3MDEsImV4cCI6MTc4MjYyMzU5My4xOTAyMTIsInN1YiI6IjEwMDkyNDA5Iiwic2NvcGVzIjpbInZpZXctdXNlciJdfQ.gNE9X2uBu6_asyEyETaGLjnCBC6XwTeVHJ0cB8FNli3JKiz_Xsr6RzFLF5tx7mufrI8Pk9G2iBvCSGriiNeIRxFFCgQ_gqhIWDHOTNE5ACG2gMyXHXvqkcuNaN9pPAqlHxTZWIYN3A4Ewy21FwSJhnxsPmWsxjdhF-QOQ3Aj11fkWIHoUD8Df_O1GP4HMu2FVToGWozT8wa7HXsrK5aAvbF4KG9SF6IjO0XUag9DAZjPEwUm6ZlXepOuUr3CR4CW86YSwZUMGWH1PR7RngAQXulyu6tOoqPL87DX5J-BS0xSr_RoC28T3deHvXlb0F6wL4Fv6V4OMDvH9rrXMhsQNdngWpzIaSO6cPn-GiGnOfkS69rleuH2rn_pQnsQvmReE71-YTcbCz2XjcB3h6aJtaFPPOD13cHi7IdidDGkNk0YbX52G6R1ozRoH2mE72AhHLFkW0pIG9VNsyvHU-MAb70ut5Yer6zVRfKrH3UGCBG830rDYBx8r7288sEu7VFgPm3Z3AqH65I6pmuTPpR0UJ4HhJlGphVOwXhO6LYZ6BezV246tTHJ77_q7nLURdoiL6gEHFwA5lnZokXre5vXdnkshOdyM5c6_Y2KgI72VjADfPunOK8o_5C36BLLXorItbgOtBytHY4vkm2BPnxF1M9E1Qy9NsQI2GDu_5oJbaw',
    
    'citizen': '%7B%22id%22%3A10149701%2C%22username%22%3A%2201626044535%22%2C%22name%22%3A%22%E0%A6%AE%E0%A7%8B%E0%A6%B8%E0%A6%BE%E0%A6%83%20%E0%A6%B6%E0%A6%BF%E0%A6%B2%E0%A7%8D%E0%A6%AA%E0%A7%80%20%E0%A6%86%E0%A6%95%E0%A7%8D%E0%A6%A4%E0%A6%BE%E0%A6%B0%22%2C%22name_en%22%3Anull%2C%22photo%22%3Anull%2C%22phone%22%3A%2201626044535%22%2C%22email%22%3Anull%2C%22father_name%22%3A%22%E0%A6%AE%E0%A7%8B%E0%A6%83%20%E0%A6%86%E0%A6%AC%E0%A7%8D%E0%A6%A6%E0%A7%81%E0%A6%B2%20%E0%A6%B9%E0%A7%87%E0%A6%95%E0%A6%BF%E0%A6%AE%22%2C%22father_name_en%22%3Anull%2C%22mother_name_en%22%3Anull%2C%22spouse_name%22%3Anull%2C%22religion%22%3Anull%2C%22occupation%22%3Anull%2C%22nationality%22%3Anull%2C%22mother_name%22%3A%22%E0%A6%AE%E0%A7%8B%E0%A6%B8%E0%A6%BE%E0%A6%83%20%E0%A6%B0%E0%A6%BE%E0%A6%A8%E0%A7%81%20%E0%A6%86%E0%A6%95%E0%A7%8D%E0%A6%A4%E0%A6%BE%E0%A6%B0%20%E0%A6%96%E0%A6%BE%E0%A6%A4%E0%A7%81%E0%A6%A8%22%2C%22nid%22%3A%221461347922%22%2C%22dob%22%3A%221967-08-28%22%2C%22address%22%3A%22%E0%A6%AC%E0%A6%BE%E0%A6%B2%E0%A6%BF%E0%A7%9F%E0%A6%BE%2C%20%E0%A6%AC%E0%A6%BE%E0%A6%B2%E0%A6%BF%E0%A7%9F%E0%A6%BE%2C%20%E0%A6%B8%E0%A6%BE%E0%A6%A4%E0%A7%8D%E0%A6%AF%E0%A6%BE%E0%A6%9F%E0%A6%BF-2410%2C%20%E0%A6%AA%E0%A7%82%E0%A6%B0%E0%A7%8D%E0%A6%AC%E0%A6%A7%E0%A6%B2%E0%A6%BE%2C%20%E0%A6%A8%E0%A7%87%E0%A6%A4%E0%A7%8D%E0%A6%B0%E0%A6%95%E0%A7%8B%E0%A6%A8%E0%A6%BE%2C%22%2C%22present_address%22%3Anull%2C%22gender%22%3Anull%2C%22progressPoint%22%3A40%7D',
    
    'cf_clearance': '2EEySUtlpIoq0e202DkIdekLck_n7aieSnaAwIiSXdw-1782546876-1.2.1.1-flcoha5IXjchjal4pg0JFSonTMB7hjXXGP5REZZSP5qHl1mBqqt7SB_A0WV2gz3PQ.aZad2Q6dtaHxAKMCWlsEQTf2s1SXOiyygChxhvvQt72RQ2LMmD913Z4_AtRGzyU8K3gURVVKDC8CPvdFjgRh1Hqs_hhNvoSdy1WtSG8xu95_bC_9g2DHVphVvoDetV9najnh27XqiDQfajBW9FsNCP7nk6XJ3rTxZkhNbC7Ho5AfGq6FUVkOn1fccHiKvjxcmpUwCYqJrTOWEaJRNNs4mhAniSn.38QJVm2uonXJO_eWkKVG4eVcyZw4QsqH935Hh6c2ImkayzNjXpAmIuuw'
}

# ============== CHROME SETUP (DOCKER AUTO-DETECT) ==============
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,800')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # ✅ Docker image-এ Chrome auto-detect
    driver = webdriver.Chrome(options=chrome_options)
    
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
        app.logger.info("Chrome started successfully")
        
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
                    app.logger.info(f"Cookie set: {name}")
                except Exception as e:
                    app.logger.warning(f"Cookie error {name}: {e}")
        
        # Step 2: Navigate to payment
        driver.get('https://portal.ldtax.gov.bd/citizen/representative-payment')
        time.sleep(3)
        
        current_url = driver.current_url
        app.logger.info(f"Current URL: {current_url}")
        
        if 'login' in current_url:
            return {'success': False, 'error': 'Cookies expired - need fresh cookies'}
        
        # Step 3: Fill dropdowns
        dropdown_fields = [
            ('division_id', params['division_id'], 2),
            ('district_id', params['district_id'], 2),
            ('upazila_id', params['upazila_id'], 2),
            ('mouja_id', params['mouja_id'], 2),
        ]
        
        for field_name, value, wait in dropdown_fields:
            app.logger.info(f"Selecting {field_name} = {value}")
            if not click_react_select(driver, field_name, value, wait):
                return {'success': False, 'error': f'Failed to select {field_name}'}
        
        # Step 4: Fill text fields
        try:
            khotian = driver.find_element(By.NAME, 'khotian_no')
            khotian.clear()
            khotian.send_keys(params['khotian_no'])
            app.logger.info(f"Khotian: {params['khotian_no']}")
        except Exception as e:
            return {'success': False, 'error': f'Khotian field error: {e}'}
        
        try:
            holding = driver.find_element(By.NAME, 'holding_no')
            holding.clear()
            holding.send_keys(params['holding_no'])
            app.logger.info(f"Holding: {params['holding_no']}")
        except Exception as e:
            return {'success': False, 'error': f'Holding field error: {e}'}
        
        # Step 5: Click search
        try:
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                if 'অনুসন্ধান' in btn.text:
                    btn.click()
                    app.logger.info("Search button clicked")
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
        app.logger.info(f"URL after search: {current_url}")
        
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
        app.logger.info(f"Found {len(links)} JWT links")
        
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
        app.logger.error(f"Capture error: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        if driver:
            driver.quit()
            app.logger.info("Driver closed")

# ============== API ENDPOINTS ==============
@app.route('/')
def home():
    return jsonify({
        'status': 'JWT Capture API is running',
        'cookies_loaded': list(FIXED_COOKIES.keys()),
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
