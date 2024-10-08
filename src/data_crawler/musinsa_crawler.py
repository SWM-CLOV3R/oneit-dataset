from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

import time
import json
import re

from base_crawler import Crawler

class MusinsaCralwer(Crawler):
    def fetch_content(self):
        self.options.add_argument('referer=https://www.musinsa.com/main/musinsa/recommend')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'performance' : 'ALL'}

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=self.options,
                                  desired_capabilities=capabilities)
        driver.get(self.url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.text-lg.font-semibold.text-black.font-pretendard'))
                # EC.presence_of_element_located((By.CSS_SELECTOR, 'span.stext-body_13px_med.font-pretendard'))
            )
        except TimeoutException as e:
            driver.quit()
            print(self.url, '페이지 접근에서 문제 발생')
            return None
        
        # time.sleep(50)
        page_source = driver.page_source
        response = dict()

        logs = driver.get_log('performance')
        for log in logs:
            log_json = json.loads(log["message"])["message"]
            
            if 'Network.responseReceived' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['response']['url']
                    if 'facebook.com' in request_url or 'twitter.com' in request_url or 'daum.net' in request_url: continue
                    elif 'google' in request_url or 't.co/1/' in request_url : continue
                    elif self.url.split("/")[-1] in request_url or 'goods-detail' in request_url or 'content' in request_url or 'liketypes' in request_url:
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        response[request_url] = response_body
                except:
                    pass

        product_info = driver.execute_script("""
                                                let scripts = document.getElementsByTagName('script');
                                                let scriptContents = [];
                                                for (let script of scripts) {
                                                    scriptContents.push(script.innerHTML);
                                                }
                                                return scriptContents;
                                            """)

        response['product_info'] = product_info
        driver.get('https://www.musinsa.com/review/goods/'+self.url.split('/')[-1])
        logs = driver.get_log('performance')
        for log in logs:
            log_json = json.loads(log["message"])["message"]
            
            if 'Network.responseReceived' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['response']['url']
                    # if 'facebook.com' in request_url or 'twitter.com' in request_url or 'daum.net' in request_url: continue
                    if 'google' in request_url or 'static.msscdn.net' in request_url : continue
                    elif 'list' in request_url:
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        response[request_url] = response_body
                except:
                    pass

        driver.quit()

        # DB에 저장
        return page_source, response
    
    def parse_content(self, page_source, response):
        product_info = json.loads([source for source in response['product_info'] if 'thumbnailImage' in source][0].split('product.state =')[-1].strip()[:-1])

        # 제품명
        name = product_info['goodsNm']

        # 가격 정보
        original_price = product_info['goodsPrice']['originPrice']
        current_price = product_info['goodsPrice']['salePrice']

        # 브랜드
        brand = (product_info['brandInfo']['brandName'], product_info['brandInfo']['brandName'] if product_info['brandInfo']['brandEnglishName'] else None)
        # brand_other = change_val_response([value for key, value in response.items() if 'additional' in key and 'photo' not in key][0])['data']['brandBestProductList']
        
        # 제품군 카테고리 (쇼핑몰 규정)
        category_inmall = product_info['baseCategoryFullPath']

        # 옵션 정보
        option_info = json.loads([value for key, value in response.items() if 'option' in key][0]['body'])['data']
        if len(option_info['basic'])==0: option = None
        else:
            option = dict()
            for i in range(len(option_info['basic'])): 
                tmp = set()
                for j in range(len(option_info['basic'][i]['optionValues'])):
                    tmp.add(option_info['basic'][i]['optionValues'][j]['name'])
                option[option_info['basic'][i]['name']] = tmp
        if len(option_info['extra']) == 0: custom = None
        else:
            custom = []
            for i in range(len(option_info['extra'])):
                custom.append(option_info['extra'][i]['name'])
        print(option)
        print(custom)


        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        for item in product_info['goodsImages']:
            thumbnail_urls.append(item['imageUrl'])
        detail_urls = re.findall(r'src="([^"]+)"', product_info['goodsContents'])
        for i in range(len(detail_urls)):
            if not detail_urls[i].startswith('http'):
                detail_urls[i] = 'https:' + detail_urls[i]

        # # 리뷰수, 리뷰
        review_info = json.loads([value for key, value in response.items() if 'review' in key and 'list' in key and 'similar' not in key][0]['body'])
        review = review_info['data']['list']
        review_count = product_info['goodsReview']['totalCount']

        # 평균 평점, 위시리스트 담은 수
        rate_avg = product_info['goodsReview']['satisfactionScore']
        wish_count = None
        wish_info = json.loads([value for key, value in response.items() if 'liketypes' in key and 'goods' in key][0]['body'])['data']['contents']['items']
        for w in wish_info:
            if w['relationId'] == self.url.split('/')[-1]:
                wish_count = w['count']

        # # 관련있는 제품 리스트
        # recommend = change_val_response([value for key, value in response.items() if 'recommends' in key][0])['data']['related_purchase_items']

        # # 베송 정보, 공지
        # notice = change_val_response([value for key, value in response.items() if 'notice' in key][0])['data']['noticeList']
        # DB에 저장

        return 
    

if __name__ == '__main__':
    url = 'https://www.musinsa.com/products/4148425'
    url = 'https://www.musinsa.com/products/4379830'
    crawler = MusinsaCralwer(url)
    info = crawler.run()
