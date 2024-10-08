from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

import json
import re

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
        
        page_source = driver.page_source

        logs = driver.get_log('performance')
        response = dict()
        for log in logs:
            log_json = json.loads(log["message"])["message"]
            if 'Network.responseReceived' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['response']['url']
                    if self.url.split("/")[-1] in request_url and '_=' in request_url:
                        # print(request_url)
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        # print(request_id,request_url, response_body,"\n")
                        response[request_url] = response_body
                except:
                    pass
        driver.quit()

        return page_source, response

    def parse_content(self, page_source, response):
        item_info = json.loads([value for key, value in response.items() if "product-detail/v2/products/"+self.url.split('/')[-1] in key][0]['body'])
 
        # 제품명
        name = item_info['itemDetails']['item']['displayName']

        # 가격 정보
        original_price = int(item_info['itemDetails']['item']['basicPrice'])
        current_price = int(item_info['itemDetails']['item']['sellingPrice'])
        
        # 브랜드
        brand = item_info['itemDetails']['brand']['name']
        brand_other = json.loads([value for key, value in response.items() if "brandProducts" in key][0]['body'])

        # 제품군 카테고리 (쇼핑몰 규정)
        category_inmall = item_info['itemDetails']['item']['supplyChannelCategoryName']
        
        # 옵션 정보
        option = None
        custom = None
        option_info = json.loads([value for key, value in response.items() if "options" in key][0]['body'])
        if option_info['type'] == 'NONE': 
            option = []
        elif option_info['type'] == 'COMBINATION':
            option = dict()
            option_combi = option_info['combinationOptions']
            for i in range(len(option_info['names'])):
                tmp = set()
                for j in range(len(option_combi)):
                    tmp.add(option_combi[j]['value'])
                option[option_info['names'][i]] = tmp
                option_combi = option_combi[0]['options']
        elif option_info['type'] == 'COMBINATION_CUSTOM':
            custom = [option_info['customs']['name']]

        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        thumbnail_urls.append(item_info['itemDetails']['item']['imageUrl'])
        thumbnail_urls += item_info['itemDetails']['item']['productOptionalImages']
        detail_urls = re.findall(r'src="(https?://[^"]+)"', item_info['itemDetails']['item']['productDetailDescription'])

        # 리뷰수, 리뷰
        review_count = json.loads([value for key, value in response.items() if "review" in key and 'sortProperty' in key][0]['body'])['reviewList']['totalCount']
        review = json.loads([value for key, value in response.items() if "review" in key and 'sortProperty' in key][0]['body'])['reviewList']['contents']

        # 평균 평점, 위시리스트 담은 수
        avg_rating = json.loads([value for key, value in response.items() if "review" in key and 'stat' in key][0]['body'])['averageProductRating']
        wish_count = json.loads([value for key, value in response.items() if "wish" in key][0]['body'])['wishCount']
        
        # 관련있는 제품 리스트
        recommend = json.loads([value for key, value in response.items() if "recommends" in key][0]['body'])

        # 배송 정보, 공지
        notice = json.loads([value for key, value in response.items() if "notice" in key][0]['body'])['giftNotices']

        return
    
if __name__ == '__main__':
    url = 'https://gift.kakao.com/product/2383657' # two option 
    url = 'https://gift.kakao.com/product/8535337' #one option
    one_options = 'https://gift.kakao.com/product/7290915'
    custom = 'https://gift.kakao.com/product/9946004'
    crawler = KkoGiftCrawler(url)
    content = crawler.run()
