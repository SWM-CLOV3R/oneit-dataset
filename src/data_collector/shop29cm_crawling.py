from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from preprocess import remove_non_numeric

def get_29cm_product_info(url):
    # Selenium WebDriver setting
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    # options.add_argument('--no-sandbox') # 샌드박스 모드를 비활성화 -> 호환성 문제 해결 but 보안 기능 비활성화 
    # options.add_argument('--disable-dev-shm-usage') # 공유 메모리 사용을 비활성화
    options.add_argument("referer=https://product.29cm.co.kr")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options)

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
    try:
        brand_name = soup.select_one('h3.css-1dncbyk.eezztd84').get_text().strip()
        brand_description = soup.select_one('p.css-8e7eit.eezztd85').get_text().strip()
        brand_link_inshop = soup.select_one('a.css-12w33mp.eezztd81')['href']
    except:
        brand_name = None
        brand_description = None
        brand_link_inshop = None
        print(url, 'HTML class 이름이 변경된 것으로 추측됨')
        
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


def get_29cm_product_reviews(url):
    # Selenium WebDriver 설정
    options = webdriver.ChromeOptions()
    options.add_argument("referer=https://product.29cm.co.kr/")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options) 
    driver.get(url) 
    driver.find_element(By.XPATH, '//*[@id="__next"]/div[5]/div[2]/div[2]/div[1]/div/div[2]/button').click()

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'span.css-1f0l480.ex98du3'))#'div.css-70qvj9.ex98du4'))# 'section.e6fth966.css-1w043rb.ex98du0'))
        )
    except TimeoutException as e:
        driver.quit()

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 값 가져오기
    review_count = remove_non_numeric(soup.select_one('span.css-1f0l480.ex98du3').get_text())
    review_pages = int(soup.select_one('div.e13i1jpn4.css-1oq0g9s.ej7aofc0').select_one('ul.css-16vmvyd.ej7aofc1').select('li')[-1].get_text())
    if review_pages > 5:
        review_pages = 5

    review_lst = []
    for i in range(1, review_pages+1):
        driver.find_element(By.XPATH, f'//*[@id="__next"]/div[7]/section[5]/div[3]/div/ul/li[{i}]/button').click()

        review_wrapper = soup.select_one('section.e6fth966.css-1w043rb.ex98du0').select_one('ul.css-0.e13i1jpn1')

        for review in review_wrapper.select('li'):
            star_wrapper = review.select_one('div.css-18biwo.e8ryq2d0').select('i.css-9nop8.e8ryq2d1')
            star_rate = 0
            for star in star_wrapper:
                if star.select_one('i.css-jcf0hl.e8ryq2d2') : star_rate += 1
            created_at = review.select_one('span.css-1riowxi.eji1c1x6').get_text()
            review_text = review.select_one('p.css-1yblk9b.eji1c1x8').get_text()
            review_lst.append(dict(star_rate=star_rate,created_at=created_at,review_text=review_text))
            # sleep(3)      

    # 브라우저 닫기
    driver.quit()

    return review_count, review_lst

if __name__ == "__main__":
    print("test sample")
    url = "https://product.29cm.co.kr/catalog/552913"
    result = get_29cm_product_info(url)
    print(result)