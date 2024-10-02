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
from preprocess import change_val_response, change_val_document

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
            )
        except TimeoutException as e:
            driver.quit()
            print(self.url, '페이지 접근에서 문제 발생')
            return None
        
        page_source = driver.page_source

        logs = driver.get_log('performance')
        response = dict()

        product_info = driver.execute_script("""
                                                let scripts = document.getElementsByTagName('script');
                                                let scriptContents = [];
                                                for (let script of scripts) {
                                                    scriptContents.push(script.innerHTML);
                                                }
                                                return scriptContents;
                                            """)

        response['product_info'] = product_info
        driver.quit()

        # DB에 저장
        return page_source, response
    
    def parse_content(self, page_source, response):
        product_info = json.loads([source for source in response['product_info'] if 'thumbnailImage' in source][0].split('product.state =')[-1].strip()[:-1])
        print(product_info)
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
        # option_info = json.loads(response['product_info'])


        # 이미지 (thumbnail, details)
        thumbnail_urls = []
        for item in product_info['goodsImages']:
            thumbnail_urls.append(item['imageUrl'])
        detail_urls = re.findall(r'src="([^"]+)"', product_info['goodsContents'])
        for i in range(len(detail_urls)):
            if not detail_urls[i].startswith('http'):
                detail_urls[i] = 'https:' + detail_urls[i]

        # # 리뷰수, 리뷰
        # review_info = change_val_response([value for key, value in response.items() if 'reviews' in key and 'photo' not in key][0])['data']# 값은 하나만 나옴
        # review = review_info['results']
        # review_count = review_info['count']

        # # 평균 평점
        # rate_avg = review_info['averagePoint']

        # wish = change_val_response([value for key, value in response.items() if 'additional' in key][0])['data']['brandBestProductList']
        # wish_count = None
        # for w in wish:
        #     if str(w['itemNo']) == self.url.split('/')[-1]:
        #         wish_count = w['heartCount']
                
        # # 관련있는 제품 리스트
        # recommend = change_val_response([value for key, value in response.items() if 'recommends' in key][0])['data']['related_purchase_items']

        # # 베송 정보, 공지
        # notice = change_val_response([value for key, value in response.items() if 'notice' in key][0])['data']['noticeList']
        # DB에 저장

        return 
    

if __name__ == '__main__':
    url = 'https://www.musinsa.com/products/4148425'
    crawler = MusinsaCralwer(url)
    info = crawler.run()
