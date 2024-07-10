import time
import urllib.request
from crawling_func.preprocess import delete_info_from_product_name, split_product_name_by_special_characters
from crawling_func.env import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
import ssl
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)
ssl._create_default_https_context = ssl._create_unverified_context


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
        informations = eval(response_body.decode("utf-8"))
        try:
            cat_info = []
            for c in ["category1","category2","category3","category4"]:
                temp = informations["items"][0][c].replace(r"\\","")
                cat_info.append(temp)
            category = " > ".join(cat_info)
            return category
        except:
            print("Error : No Results -> " + product_name)
    else:
        print("Error : No Response ->" + product_name)

    return None

def search_category(product_name, brand_name):
    product_name = delete_info_from_product_name(product_name)
    category = get_category_in_naver(product_name)
    if not category:
        parts = split_product_name_by_special_characters(product_name)
        for p in parts:
            time.sleep(3)
            category = get_category_in_naver(brand_name + " " + p)
            if category : 
                print("-> find product success!")
                break

    return category