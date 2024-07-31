import pymysql
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from producturl_verification import *

def lambda_handler(event, context):
    connection = pymysql.connect(
        host=os.environ.get("HOST"),
        user=os.environ.get("USER_NAME"),
        password=os.environ.get("PASSWORD"),
        database=os.environ.get("TEST_DATABASE"),
        port=int(os.environ.get("PORT"))
    )

    try:
        with connection.cursor() as cursor:
            query = "UPDATE product SET status = %s"
            cursor.execute(query, ("OLD"))
            # 데이터 가져올 SQL 쿼리
            query = "SELECT product_url, status, mall_name FROM product"
            
            # 쿼리 실행
            cursor.execute(query)
            
            # 결과 가져오기
            results = cursor.fetchall()
            
            # 결과 출력
            for row in results:
                url, status, mall_name= row
                if mall_name == "29cm":
                    check = product_valid_29cm(url)
                elif mall_name == "카카오톡 선물하기":
                    check = product_valid_kko(url)
                status = "UPDATED" if check else "INVALID"
                query =  "UPDATE product SET status = %s WHERE product_url = %s"
                cursor.execute(query, (status, url))
                connection.commit()

        return {
            "statusCode": 200,
            "body": "Status updated successfully"
        }

    finally:
        # 연결 종료
        connection.close()

# local에서 실행 확인
if __name__ == "__main__":
    start = time.time()
    lambda_handler() # 125건 기준 : 278.9550790786743초 -> max 5분
    end = time.time()
    print(end - start)