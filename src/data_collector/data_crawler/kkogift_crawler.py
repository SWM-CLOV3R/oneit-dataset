from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import json
import re
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir)))
from base_crawler import Crawler

class KkoGiftCrawler(Crawler):
    def fetch_content(self):
        self.options.add_argument('referer=https://gift.kakao.com')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'performance' : 'ALL'}

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=self.options,
                                  desired_capabilities=capabilities)
        driver.get(self.url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.txt_total'))
            )
        except TimeoutException as e:
            driver.quit()
            print(self.url, '페이지 접근에서 문제 발생')
            return None
        
        content = dict()
        content['page_source'] = driver.page_source

        logs = driver.get_log('performance')
        for log in logs:
            log_json = json.loads(log["message"])["message"]
            if 'Network.responseReceived' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['response']['url']
                    if self.url.split("/")[-1] in request_url:# or '=' in request_url:
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        content[request_url] = response_body
                except:
                    pass
        driver.quit()

        return content

    def parse_content(self, content):
        item_info = json.loads([value for key, value in content.items() if "product-detail/v2/products/"+self.url.split('/')[-1] in key][0]['body'])

        # 제품명
        name = item_info['itemDetails']['item']['displayName']

        # 가격 정보
        original_price = int(item_info['itemDetails']['item']['basicPrice'])
        current_price = int(item_info['itemDetails']['item']['sellingPrice'])
        
        # 브랜드
        brand = (item_info['itemDetails']['brand']['name'], None)
        try:
            brand_other = json.loads([value for key, value in content.items() if "brandProducts" in key][0]['body'])
        except:brand_other = None
        # 제품군 카테고리 (쇼핑몰 규정)
        category_inmall = item_info['itemDetails']['item']['supplyChannelCategoryName']
    
        # 옵션 정보
        option_info = json.loads([value for key, value in content.items() if "options" in key][0]['body'])
        if option_info['type'] == 'NONE': 
            option = None
            custom = None
        elif option_info['type'] == 'COMBINATION':
            option = dict()
            option_combi = option_info['combinationOptions']
            for i in range(len(option_info['names'])):
                tmp = set()
                for j in range(len(option_combi)):
                    tmp.add(option_combi[j]['value'])
                option[option_info['names'][i]] = list(tmp)
                option_combi = option_combi[0]['options']
            custom = None
        elif option_info['type'] == 'COMBINATION_CUSTOM':
            option = dict()
            option_combi = option_info['combinationOptions']
            for i in range(len(option_info['names'])):
                tmp = set()
                for j in range(len(option_combi)):
                    tmp.add(option_combi[j]['value'])
                option[option_info['names'][i]] = list(tmp)
                option_combi = option_combi[0]['options']
            try: custom = [option_info['customs']['name']]
            except: custom = [option_info['customs'][0]['name']]
        
        elif option_info['type'] == 'SIMPLE':
            option = dict()
            tmp = set()
            option_combi = option_info['simpleOptions']
            for opt in option_combi:
                tmp.add(opt['name'])
            option[option_info['names'][0]] = list(tmp)
            custom = None
        else: 
            option = None
            custom = None

        # 성별
        gender = None
        
        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        thumbnail_urls.append(item_info['itemDetails']['item']['imageUrl'])
        thumbnail_urls += item_info['itemDetails']['item']['productOptionalImages']
        detail_urls = re.findall(r'src="(https?://[^"]+)"', item_info['itemDetails']['item']['productDetailDescription'])

        # 리뷰수, 리뷰
        review_info = json.loads([value for key, value in content.items() if "review" in key and 'sortProperty' in key][0]['body'])
        review_count = review_info['reviewList']['totalCount']
        review = [review['content'] for review in review_info['reviewList']['contents']]

        # 평균 평점, 위시리스트 담은 수
        avg_rating = json.loads([value for key, value in content.items() if "review" in key and 'stat' in key][0]['body'])['averageProductRating']
        wish_count = json.loads([value for key, value in content.items() if "wish" in key][0]['body'])['wishCount']
        
        # 관련있는 제품 리스트
        try:
            recommend = json.loads([value for key, value in content.items() if "recommends" in key][0]['body'])
        except:
            recommend = None

        # 배송 정보, 공지
        # notice = json.loads([value for key, value in content.items() if "notice" in key][0]['body'])['giftNotices']

        info_table = dict(name=name,
                          original_price=original_price, current_price=current_price,
                          brand=brand, brand_other=brand_other,
                          category_inmall=category_inmall,
                          option=option, custom=custom, gender=gender,
                          thumbnail_urls=thumbnail_urls, detail_urls=detail_urls,
                          review=review, review_count=review_count,
                          rate_avg=avg_rating, wish_count=wish_count,
                          recommend=recommend)#, notice=notice)
        return info_table
    
    def is_invalid(self, content):
        soup = BeautifulSoup(content['page_source'], 'html.parser')
        button = soup.find("em", class_="circle_badge")
        if button:
            button_val = button.get_text()
            if '종료' in button_val or '중단' in button_val or '품절' in button_val:
                return True
        return False
    
if __name__ == '__main__':
    url = 'https://gift.kakao.com/product/2383657' # two option 
    url = 'https://gift.kakao.com/product/8535337' #one option
 
    crawler = KkoGiftCrawler(url)
    content = crawler.run()
    print(content)
    # print(content)
    # print(content['brand'])
    # print(content['brand'][0])
    # print(content)
    # print(content['detail_urls'])
