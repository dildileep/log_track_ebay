API_URL = "https://some-ml-model-api-endpoint/api/health"
fail_count = 0
CHECK_INTERVAL = 60

def check_api():
    global fail_count
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            logging.info("API is healthy")
            fail_count = 0
        else:
            fail_count += 1
            logging.warning(f"API returned non-200: {res.status_code}")
    except Exception as e:
        fail_count += 1
        logging.error(f"Exception in healthcheck: {str(e)}")
        
    
    if fail_count >= 3:
        alert_msg = f"ALERT!! API failed {fail_count} times continous"
        print(alert_msg)
        logging.critical(alert_msg)
        # we can call any sns notifications  here for email or such
        fail_count = 0


check_api()
time.sleep(CHECK_INTERVAL)