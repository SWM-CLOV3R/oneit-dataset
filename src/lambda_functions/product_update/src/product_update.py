import os
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from lambda_functions.product_update.src.preprocess import remove_non_numeric, delete_info_from_product_name


def update_product_info(mode, url, headers=None):
    if "29cm" in url:
        return get_29cm_info(mode, url, headers)
    elif "gift.kakao" in url:
        return get_kko_info(mode, url, headers)
    return -1

def get_29cm_info(mode, url, headers=None):
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
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        if soup.select_one("div.css-1pc4k5l.e1q7e96n0"): 
            print(url, "판매 중지")
        if soup.select_one("div.css-1oyhyes.erkjrr60") :
            print(url, "404 링크")
        driver.quit()
        return -1
    
    driver.quit()

    if mode == "price": 
        soup = BeautifulSoup(html, 'html.parser')

        # 가격 불러오기
        try:
            if soup.select_one('p.css-1bci2fm.ejuizc31'): # 할인할 때
                current_price = remove_non_numeric(soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip())
                original_price = remove_non_numeric(soup.select_one('p.css-1bci2fm.ejuizc31').get_text().strip())
                discount_rate = remove_non_numeric(soup.select_one('span.css-1jsmahk.ejuizc32').get_text().strip())
            else: # 할인 안할 때
                current_price = remove_non_numeric(soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip())
                original_price = current_price
                discount_rate = 0
            return [original_price, current_price, discount_rate]
        except:
            print(url, "가격 정보 불러오기 실패")
            return -1

    elif mode == "verification": return 1
    
    return -1


def get_kko_info(mode, url, headers=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    options.add_argument("referer=https://gift.kakao.com/home")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options) 
    driver.get(url) 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.txt_price"))
        )
    except TimeoutException as e:
        print(url, "404 링크")
        driver.quit()
        return -1
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("span.cmp_coverbadge.type_pc"):
        print(url, soup.select_one("span.cmp_coverbadge.type_pc").get_text().replace("\n", " "))
        driver.quit()
        return 0
    
    driver.quit()

    if mode == "price":
        soup = BeautifulSoup(html, 'html.parser')

        # 가격 불러오기
        try:
            if soup.select_one('span.txt_sale'): # 할인 함
                current_price = remove_non_numeric(soup.select_one('span.txt_sale').get_text())
                original_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_price').get_text())
                current_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text())
            else: # 할인 안 함
                current_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text())
                original_price = current_price
                discount_rate = 0
            return [original_price, current_price, discount_rate]
        except:
            print(url, "가격 정보 불러오기 실패")
            return -1

    elif mode == "verification": return 1

    return -1
 