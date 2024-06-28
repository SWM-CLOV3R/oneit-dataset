from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def get_29cm_product_info(url):
    # Selenium WebDriver 설정
    driver = webdriver.Chrome() 
    driver.get(url) 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.css-4bcxzt.ejuizc34'))
        )
    except TimeoutException as e:
        driver.quit()
        print(url, '페이지 접근에서 문제 발생')
        return None

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 값 가져오기
    # 1. 상품명
    try:
        product_name = soup.select_one('#pdp_product_name').get_text().strip()
    except:
        driver.quit()
        print(url, '판매 중단')
        return None

    # 2. 가격
    if soup.select_one('p.css-1bci2fm.ejuizc31'): # 할인할 때
        original_price = soup.select_one('p.css-1bci2fm.ejuizc31').get_text().strip()
        current_price = soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip()
        discount_rate = soup.select_one('span.css-1jsmahk.ejuizc32').get_text().strip()
    else: # 할인 안할 때
        current_price = soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip()
        original_price = current_price
        discount_rate = '0%'
    
    # 3. 브랜드 정보
    brand_name = soup.select_one('h3.css-1dncbyk.e1kth5844').get_text().strip()
    brand_description = soup.select_one('p.css-8e7eit.e1kth5845').get_text().strip()
    brand_link_inshop = soup.select_one('a.css-k95f3n.e1kth5841')['href']

    # 4. 상품 대표 이미지
    try:
        thumbnail = soup.select_one('div.css-122y91a.e3e1mx64').select_one('img')['src']
    except:
        thumbnail = None

    # 5. 상품 카테고리
    category_wrapper = soup.select('li.css-1vtc84p.e1mxp6e91')
    category = []
    for cat in category_wrapper:
        category.append(cat.select_one('span.css-96h8o6.e1w312mf1').get_text())
    if len(category) > 0: category = '/'.join(category)
    else: category = None

    product_info_table = dict(product_name=product_name, 
                              original_price=original_price, current_price=current_price, discount_rate=discount_rate,
                              brand_name=brand_name,brand_description=brand_description,brand_link_inshop=brand_link_inshop,
                              thumbnail=thumbnail, category=category)
    
    # 6. 상품상세 정보 표
    product_info_lst= soup.select_one('table.e1hw6jas2.css-1x7jfi1.exbpx9h0').select('tr')
    for product_info in product_info_lst:
        info_name , info_val = product_info.select_one('th').get_text().strip(), product_info.select_one('td').get_text().strip()
        if '상세페이지' in info_val: continue
        product_info_table[info_name] = info_val

    # 브라우저 닫기
    driver.quit()

    return product_info_table

