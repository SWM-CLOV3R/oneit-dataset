from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import json

def product_29cm_crawler(url, header=None):
    # Selenium WebDriver setting
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    options.add_argument("referer=https://product.29cm.co.kr")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options)

    driver.get(url) 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-4bcxzt.ejuizc34"))
        )
    except TimeoutException as e:
        driver.quit()
        print(url, "페이지 접근에서 문제 발생")
        return None

    html = driver.page_source

    driver.quit()

    return html


def product_kko_crawler(url, header=None):
    # Selenium WebDriver 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    options.add_argument("referer=https://gift.kakao.com/home")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options) 
    driver.get(url + "?tab=detail") 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.txt_price"))
        )
    except TimeoutException as e:
        driver.quit()
        print(url, "페이지 접근에서 문제 발생")
        return None


    html = driver.page_source

    driver.quit()

    return html


if __name__ == "__main__":
    url = "https://product.29cm.co.kr/catalog/2628109"
    print(type(product_29cm_crawler(url)))
    

