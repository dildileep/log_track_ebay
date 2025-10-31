import logging as log
import time
import requests 

log_count=0
URL = "https://www.google.com"
# Logging setup
log.basicConfig(
    level=log.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        log.FileHandler("url_healthcheck.log"),
        log.StreamHandler()

    ]
)
def requstcheck():
    global log_count
    res=requests.get(URL,timeout=10,verify=False)
    if res.status_code==200:
        log_count=0
        log.info(f"the URL {URL} is working fine")
        print(log)
while True:
    requstcheck()
    time.sleep(20)

#print(a)