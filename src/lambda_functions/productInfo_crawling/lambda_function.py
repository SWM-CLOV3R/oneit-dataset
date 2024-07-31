import os
import sys
import time
# import boto3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import pymysql

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(src_dir)
from productinfo_crawler import *

def lambda_handler(event, context):
    # Cookie 가져오기
    options = Options()
    options.add_argument("--headless") 

    driver = webdriver.Chrome(options=options)
    driver.get("https://product.29cm.co.kr/")
    driver.implicitly_wait(5)
    cookies_29cm = driver.get_cookies()

    driver.get("https://gift.kakao.com/home")
    driver.implicitly_wait(5)
    cookies_kko = driver.get_cookies()

    driver.quit()

    # # 쿠키를 header로 변환
    # header_29cm = {}
    # for cookie in cookies_29cm:
    #     header_29cm[cookie["name"]] = cookie["value"]
    # header_kko = {}
    # for cookie in cookies_29cm:
    #     header_kko[cookie["name"]] = cookie["value"]

    connection = pymysql.connect(
        host=os.environ.get("HOST"),
        user=os.environ.get("USER_NAME"),
        password=os.environ.get("PASSWORD"),
        database=os.environ.get("TEST_DATABASE"),
        port=int(os.environ.get("PORT"))
    )

    # DB 상의 정보 업데이트가 필요한 product의 idx, url등의 정보 가져오기
    try:
        with connection.cursor() as cursor:
            # 데이터 가져올 SQL 쿼리
            query = "SELECT idx, product_url, status, mall_name FROM product"
            
            # 쿼리 실행
            cursor.execute(query)
            results = cursor.fetchall()

            for row in results:
                idx, url, status, mall_name = row
                if mall_name == "29cm":
                    new_data = product_29cm_crawler(url)
                elif mall_name == "카카오톡 선물하기":
                    new_data = product_kko_crawler(url)
                query =  "UPDATE product SET raw = %s WHERE idx = %s"
                cursor.execute(query, (new_data, idx))
                connection.commit()

                # S3에 업로드하는 방식으로 변경
                # s3_client = boto3.client('s3')

        return {
            "statusCode": 200,
            "body": "Status updated successfully"
        }
    finally:
        # 연결 종료
        connection.close()
        

if __name__ == "__main__":
    
    lambda_handler(None, None)