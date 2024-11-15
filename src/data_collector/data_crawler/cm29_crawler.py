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

class CM29Crawler(Crawler):
    def fetch_content(self):
        self.options.add_argument('referer=https://product.29cm.co.kr')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'performance' : 'ALL'}

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=self.options,
                                  desired_capabilities=capabilities)
        driver.get(self.url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="pdp_product_price"]'))
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
            if 'Network.requestWillBeSent' in log_json['method']:
                try:
                    request_id = log_json['params']['requestId']
                    request_url = log_json['params']['request']['url']
                    if 'log.' in request_url or 'google' in request_url: continue
                    elif self.url.split('/')[-1] in request_url or '-api' in request_url or 'img.29cm' in request_url or 'flag' in request_url:
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        content[request_url] = response_body
                        
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
        content['img_urls'] = img_urls

        product_info = driver.execute_script("""
                                                return document.getElementById('__NEXT_DATA__').innerHTML;
                                            """)
        content['product_info'] = product_info
        driver.quit()

        # DB에 저장
        return content
    
    def parse_content(self, content):
        item_info  = json.loads(content['product_info'])['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']

        # 제품명
        name = item_info['itemName']
        
        # 가격 정보
        try:
            price_info = json.loads([value for key, value in content.items() if 'display-price' in key or 'promotion' in key][0]['body'])['data']['price']
        except:
            price_info = json.loads([value for key, value in content.items() if 'display-price' in key or 'promotion' in key][0]['body'])['data']['priceSummary']
        original_price = price_info['totalItemConsumerPrice']
        current_price = price_info['totalDiscountedItemPrice']

        # 브랜드
        brand = (item_info['frontBrand']['brandNameKor'] if item_info['frontBrand']['brandNameKor'] else None, item_info['frontBrand']['brandNameEng'] if item_info['frontBrand']['brandNameEng'] else None)
        brand_other = json.loads([value for key, value in content.items() if 'product-detail' in key][0]['body'])['data']['brandBestProductList']

        
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
                option[option_info['layout'][i]] = list(tmp)
                option_combi = option_combi[0]['list']
            if item_info['optionType'] < len(option_info['layout']):
                custom = option_info['layout'][item_info['optionType']:]
            else:
                custom = None
        
        # 성별
        gender = None

        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        detail_urls = []
        for i in content['img_urls']:
            if 'width=700' in i:
                thumbnail_urls.append(i)
            elif 'width=1000' in i:
                detail_urls.append(i)
            elif 'width=300' in i or 'width=100' in i :continue # or 'next-contents' in i or 'next-product' in i: continue
            else:
                detail_urls.append(i)
                
        # 리뷰수, 리뷰
        review_info = json.loads([value for key, value in content.items() if 'reviews' in key and 'photo' not in key][0]['body'])['data']# 값은 하나만 나옴
        review = [review['contents'] for review in review_info['results']]
        review_count = review_info['count']
    
        # 평균 평점
        rate_avg = review_info['averagePoint']

        wish_count = None
        for w in brand_other:
            if str(w['itemNo']) == self.url.split('/')[-1]:
                wish_count = w['heartCount']
                
        # 관련있는 제품 리스트
        try:
            recommend = json.loads([value for key, value in content.items() if 'recommends' in key][0]['body'])#['data']['related_purchase_items']
        except:
            recommend = None

        # 베송 정보, 공지
        notice = json.loads([value for key, value in content.items() if 'notice' in key][0]['body'])['data']['noticeList']

        info_table = dict(name=name, 
                          original_price=original_price, current_price=current_price,
                          brand=brand, brand_other=brand_other,
                          category_inmall=category_inmall,
                          option=option, custom=custom, gender=gender,
                          thumbnail_urls=thumbnail_urls, detail_urls=detail_urls,
                          review=review, review_count=review_count,
                          rate_avg=rate_avg, wish_count=wish_count,
                          recommend=recommend, notice=notice)
        return info_table
    
    def is_invalid(self, content):
        soup = BeautifulSoup(content['page_source'], 'html.parser')
        button = soup.find("button", {"id": "cta_purchase"})
        if button:
            button_val = button.get_text()
            if '품절' in button_val or '판매 중지' in button_val:
                return True
        return False
    
if __name__ == '__main__':
    # url = 'https://product.29cm.co.kr/catalog/2252385'#일시품절
    # url = 'https://product.29cm.co.kr/catalog/1814100'
    url = 'https://product.29cm.co.kr/catalog/2566507'
    crawler = CM29Crawler(url)
    info = crawler.run()
    # print(info)
