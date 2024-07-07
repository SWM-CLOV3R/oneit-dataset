import os
import sys
import urllib.request

from env import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

def get_category_in_naver(product_name):
    encText = urllib.parse.quote(product_name)
    url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=1"  # JSON 결과
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        informations = eval(response_body.decode('utf-8'))
        try:
            cat_info = []
            for c in ["category1","category2","category3","category4"]:
                temp = rr["items"][0][c].replace("\\","")
                cat_info.append(temp)
            category = ' > '.join(cat_info)
            return category
        except:
            print("Error : No Results -> " + product_name)
    else:
        print("Error : No Response ->" + product_name)

    return None