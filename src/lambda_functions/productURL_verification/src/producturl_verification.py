from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def product_valid_kko(url, headers=None):
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
        print(url, "404 error")
        driver.quit()
        return 0
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("span.cmp_coverbadge.type_pc"):
        print(url, soup.select_one("span.cmp_coverbadge.type_pc").get_text().replace("\n", " "))
        driver.quit()
        return 0
    
    driver.quit()
    return 1

def product_valid_29cm(url, headers=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    # options.add_argument("--no-sandbox") # 샌드박스 모드를 비활성화 -> 호환성 문제 해결 but 보안 기능 비활성화 
    # options.add_argument("--disable-dev-shm-usage") # 공유 메모리 사용을 비활성화
    options.add_argument("referer=https://product.29cm.co.kr")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options)

    driver.get(url) 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 5).until(                      
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-ckmsfc.e1fpjmur2"))
        )
    except TimeoutException as e:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        if soup.select_one("div.css-1pc4k5l.e1q7e96n0"): 
            print(url, "판매 중지")
        if soup.select_one("div.css-1oyhyes.erkjrr60") :
            print(url, "404 링크")
        driver.quit()
        return 0
    driver.quit()
    return 1
