import pymysql
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from productprice_update import *

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
            init_query = "UPDATE product SET status = %s"
            cursor.execute(init_query, ("OLD"))

            select_query = "SELECT idx, raw, status, mall_name FROM product"
            cursor.execute(select_query)
            results = cursor.fetchall()
            
            # 결과 출력
            for row in results:
                idx, html, status, mall_name = row
                if status == "UPDATED" : continue
                if mall_name == "29cm":
                    check = product_29cm_info(html)
                elif mall_name == "카카오톡 선물하기":
                    check = product_kko_info(html)
                update_query = """
                                UPDATE product
                                SET current_price = %s, discount_rate = %s, status = 'UPDATED'
                                WHERE idx = %s
                                """
                cursor.execute(update_query, (check["current_price"], check["discount_rate"], idx))
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
    lambda_handler() 
    end = time.time()
    print(end - start)