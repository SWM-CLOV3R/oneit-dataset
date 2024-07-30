from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib import parse

from preprocess import remove_non_numeric


def get_kko_product_info(url):
    # Selenium WebDriver 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 창 띄우지 않기 옵션
    options.add_argument("referer=https://gift.kakao.com/home")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
    driver = webdriver.Chrome(options=options) 
    driver.get(url + '?tab=detail') 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.txt_price'))
        )
    except TimeoutException as e:
        driver.quit()
        print(url, '페이지 접근에서 문제 발생')
        return None


    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 값 가져오기
    # 0. 상태 확인
    status = soup.select_one('product-stamp')
    if status.get_text():
        driver.quit()
        print(url, '판매 중단')
        return None
    
    # 1. 상품명
    product_name = soup.select_one('h2.tit_subject').get_text()
    # 2. 가격
    if soup.select_one('span.txt_sale'): # 할인 함
        discount_rate = soup.select_one('span.txt_sale').get_text()
        original_price = soup.select_one('div.info_product.clear_g').select_one('span.txt_price').get_text()
        current_price = soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text()
    else: # 할인 안 함
        current_price = soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text()
        original_price = current_price
        discount_rate = '0%'
        
    # 3. 브랜드 정보
    brand_name = soup.select_one('span.txt_shopname').get_text()
    brand_link_inshop = 'https://gift.kakao.com' + soup.select_one('a.link_shopname')['href']

    
    # 4. 상품 대표 이미지
    try:
        thumbnail = soup.select_one('swiper-slide.cont_slide.swiper-slide-active').select_one('img')['src']
    except:
        thumbnail = None
    
    # 5. 상품 카테고리
    driver.get('https://gift.kakao.com/search/result?query=' + parse.quote(product_name) +'&searchType=typing_keyword') 

    # time.sleep(5)
    try:
        try:
            driver.find_element(By.XPATH, '//*[@id="mArticle"]/app-pw-result/div/div/app-search-result/app-option/div[3]/div/div/div/ul/li[2]/button').click()
        except:
            driver.find_element(By.XPATH, '//*[@id="mArticle"]/app-pw-result/div/div/app-search-result/app-option/div[2]/div/div/div/ul/li[2]/button').click()
        html_c = driver.page_source
        soup_c = BeautifulSoup(html_c, 'html.parser')
        category = soup_c.select_one('swiper-slide.list_slctcate.has_item_all.swiper-slide-active').select('li')[1].get_text().strip()
    except:
        category = None

    product_info_table = dict(product_name=product_name, 
                              original_price=original_price, current_price=current_price, discount_rate=discount_rate,
                              brand_name=brand_name,brand_link_inshop=brand_link_inshop,
                              thumbnail=thumbnail, category=category)

    # 6. 상품상세 정보 표
    product_info_lst= soup.select_one('table.tbl_detail').select('tr')
    for product_info in product_info_lst:
        info_name , info_val = product_info.select_one('th').get_text(), product_info.select_one('td').get_text()
        if info_val == '상품상세설명 참조': continue
        product_info_table[info_name] = info_val


    # 브라우저 닫기
    driver.quit()

    return product_info_table


def get_kko_product_reviews(url):
    # Selenium WebDriver 설정
    driver = webdriver.Chrome() 
    driver.get(url + '?tab=review&sortProperty=LATEST') 

    # 필요한 값이 로드될 때 까지 기다림
    try : 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.wrap_group.wrap_reviewcard'))
        )
    except TimeoutException as e:
        driver.quit()
        return None


    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 값 가져오기
    try:
        no_review = soup.select_one('div.wrap_group.wrap_noreview')
        if no_review:
            return 0, None
    except:
        pass
    
    
    review_count = remove_non_numeric(soup.select_one('div.wrap_group.wrap_reviewcard').select_one('h4.tit_group').get_text())
    review_wrapper = soup.select_one('div.wrap_group.wrap_reviewcard').select_one('ul.list_review')
    # except: 
    #     return -1, None # 판매 중지 혹은 품절 

    # 더보기 미리 클릭
    if (review_count - 1) // 20 > 0:
        if (review_count - 1) // 20 > 5 : max_click = 5
        else: max_click = (review_count - 1) // 20
        
        for press_count in range(max_click):
            try:
                driver.find_element(By.XPATH, '//*[@id="tabPanel_review"]/div/div[2]/button').click()
                # time.sleep(2)
            except:
                break
    # 리뷰 수집
    review_lst = []
    for review in review_wrapper.select('app-view-review-item'):
        star_rate = review.select_one('em.ico_detail').get_text()
        created_at = review.select('span.txt_reviewinfo')[-1].get_text()
        review_text = review.select_one('p.txt_review').get_text()
        # print(star_rate,created_at,review_text)
        review_lst.append(dict(star_rate=star_rate,created_at=created_at,review_text=review_text))
        # time.sleep(2)

    # 불러온 값이 None 일 때의 대비 아직 미완

    # 브라우저 닫기
    driver.quit()

    return review_count, review_lst

if __name__ == "__main__":
    print("test sample")
    url = "https://gift.kakao.com/product/5714345"
    result = get_kko_product_info(url)
    print(result)