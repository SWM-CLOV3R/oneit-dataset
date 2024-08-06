import pymysql
import time
from datetime import datetime as dt
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from product_update import update_product_info

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
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            query = """
                        SELECT idx, product_url, updated_at, status FROM product 
                        WHERE TIMESTAMPDIFF(DAY, updated_at, NOW()) >= 1 OR status = "INVALID"
                    """
            cursor.execute(query, (current_time,))
            need_update = cursor.fetchall()
            
            for row in need_update:
                idx, product_url, updated_at, status = row

                if status == "INVALID": mode="price"
                elif updated_at.date() < dt.now().date(): mode = "price"
                else: mode = "verification"
                
                updated_info = update_product_info(mode, product_url)

                if updated_info == -1:
                    update_query = """
                                    UPDATE product 
                                    SET status = %s,
                                        updated_at = NOW()
                                    WHERE idx = %s"""
                    cursor.execute(update_query, ("INVALID", idx))

                elif mode == "price":
                    original_price, current_price, discount_rate = updated_info
                    update_query = """
                                    UPDATE product
                                    SET original_price = %s,
                                        current_price = %s,
                                        discount_rate = %s,
                                        updated_at = NOW()
                                    WHERE idx = %s"""
                    cursor.execute(update_query, (original_price, current_price, discount_rate, idx))

                
                connection.commit()

        return {
            "statusCode": 200,
            "body": "Status updated successfully"
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
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
