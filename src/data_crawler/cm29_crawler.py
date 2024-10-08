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

class CM29Crawler(Crawler):
    def fetch_content(self):
        self.options.add_argument('referer=https://product.29cm.co.kr')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'performance' : 'ALL'}

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=self.options,
                                  desired_capabilities=capabilities)
        driver.get(self.url)
        # time.sleep(10)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="pdp_product_price"]'))
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
            if 'Network.requestWillBeSent' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['request']['url']
                    if 'log.' in request_url or 'google' in request_url: continue
                    elif self.url.split('/')[-1] in request_url or '-api' in request_url or 'img.29cm' in request_url or 'flag' in request_url:
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        response[request_url] = response_body
                        # if 'img' in request_url:
                        # print(request_url)
                            # print(response_body)
                        
                except:
                    pass

        img_urls = driver.execute_script("""
                                            let images = document.getElementsByTagName('img');
                                            let imgSrcs = [];
                                            for (let i = 0; i < images.length; i++) {
                                                imgSrcs.push(images[i].src);
                                            }
                                            return imgSrcs;
                                        """)
        response['img_urls'] = img_urls

        product_info = driver.execute_script("""
                                                return document.getElementById('__NEXT_DATA__').innerHTML;
                                            """)
        response['product_info'] = product_info
        driver.quit()

        # DB에 저장

        return page_source, response
    
    def parse_content(self, page_source, response):
        item_info  = json.loads(response['product_info'])['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']

        # 제품명
        name = item_info['itemName']
        
        # 가격 정보
        price_info = json.loads([value for key, value in response.items() if 'display-price' in key][0]['body'])['data']['price']
        # print(price_info)
        original_price = price_info['totalDiscountedItemPrice']
        current_price = price_info['totalItemConsumerPrice']

        # 브랜드
        brand = (item_info['frontBrand']['brandNameKor'] if item_info['frontBrand']['brandNameKor'] else None, item_info['frontBrand']['brandNameEng'] if item_info['frontBrand']['brandNameEng'] else None)
        brand_other = json.loads([value for key, value in response.items() if 'product-detail' in key][0]['body'])['data']['brandBestProductList']

        
        # 제품군 카테고리 (쇼핑몰 규정)
        category_info = item_info['frontCategoryInfo'][0]
        category_inmall = []
        for k in category_info.keys():
            if 'Name' in k:
                category_inmall.append(category_info[k])
        category_inmall = '>'.join(category_inmall)

        # 옵션 정보
        option_info = item_info['optionItems']
        if len(option_info['layout']) == 0:
            option = None
            custom = None
        else:
            option = dict()
            option_combi = option_info['list']
            for i in range(item_info['optionType']):
                tmp = set()
                for j in range(len(option_combi)):
                    tmp.add(option_combi[j]['title'])
                option[option_info['layout'][i]] = tmp
                option_combi = option_combi[0]['list']
            if item_info['optionType'] < len(option_info['layout']):
                custom = option_info['layout'][item_info['optionType']:]
            else:
                custom = None

        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        detail_urls = []
        for i in response['img_urls']:
            if 'width=700' in i:
                thumbnail_urls.append(i)
            elif 'width=300' in i or 'next-contents' in i or 'next-product' in i: continue
            else:
                detail_urls.append(i)
                
        # 리뷰수, 리뷰
        review_info = json.loads([value for key, value in response.items() if 'reviews' in key and 'photo' not in key][0]['body'])['data']# 값은 하나만 나옴
        review = review_info['results']
        review_count = review_info['count']
    
        # 평균 평점
        rate_avg = review_info['averagePoint']

        wish_count = None
        for w in brand_other:
            if str(w['itemNo']) == self.url.split('/')[-1]:
                wish_count = w['heartCount']
                
        # 관련있는 제품 리스트
        recommend = json.loads([value for key, value in response.items() if 'recommends' in key][0]['body'])['data']['related_purchase_items']

        # 베송 정보, 공지
        notice = json.loads([value for key, value in response.items() if 'notice' in key][0]['body'])['data']['noticeList']
        # DB에 저장
        return 
    
    
if __name__ == '__main__':
    url = 'https://product.29cm.co.kr/catalog/2835491'
    url = 'https://product.29cm.co.kr/catalog/2340880'
    url = 'https://product.29cm.co.kr/catalog/2606849'
    crawler = CM29Crawler(url)
    info = crawler.run()
