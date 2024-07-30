import pymysql
import os

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
            # 데이터 가져올 SQL 쿼리
            query = "SELECT product_url, status, mall_name FROM product"
            
            # 쿼리 실행
            cursor.execute(query)
            
            # 결과 가져오기
            results = cursor.fetchall()
            
            # 결과 출력
            for row in results:
                print(f"Product URL: {row[0]}, Status: {row[1]}")

        return {
            "statusCode": 200,
            "body": "Status updated successfully"
        }
    finally:
        # 연결 종료
        connection.close()