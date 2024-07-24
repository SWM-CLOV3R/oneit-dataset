from youtube_crawling import get_video_by_keys, get_product_urls
from shopkko_crawling import get_kko_product_info, get_kko_product_reviews
from shop29cm_crawling import get_29cm_product_info, get_29cm_product_reviews
from preprocess import remove_non_numeric,remove_extra_spaces
from normalized_category import search_category

import sys
import os
import pandas as pd
from time import gmtime, strftime, sleep
import re

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)

from config import DATA_PATH

# 데이터셋 초기 업로드
# 기존 DB에 있는 데이터인지 확인하는 작업 아직 없음
def get_product_data(keyword_lst, mall_lst):
    relevance_data = get_video_by_keys(keyword_lst, 30)
    current_data = get_video_by_keys(keyword_lst, 80, order="date")

    data = pd.concat([relevance_data, current_data])
    data.reset_index(inplace=True, drop=True)
    data = data.groupby("id").agg({"searchQ": ", ".join,
                                                    "date" : "first", 
                                                    "title" : "first", 
                                                    "description" : "first", 
                                                    "channel" : "first", 
                                                    "tags" : "first", 
                                                    "type" : "first", 
                                                    "view" : "first"})
    data.reset_index(inplace=True)

    data["searchQ"] = data["searchQ"].apply(lambda x: x.split(", "))

    products = get_product_urls(data)
    products.drop_duplicates(subset=["productURL"],inplace=True)
    products.reset_index(drop=True, inplace=True)


    product_shoppingmall = []
    for url in products["productURL"]:
        if "29cm" in url : product_shoppingmall.append("29cm")
        elif any(shop in url for shop in ["gift.kakao", "kko.to"]): product_shoppingmall.append("카카오 선물하기")
        elif "coupang" in url: product_shoppingmall.append("쿠팡")
        elif "wconcept" in url: product_shoppingmall.append("wconcept")
        elif "smartstore" in url: product_shoppingmall.append("네이버")
        elif any(shop in url for shop in ["sivillage", "lotteon", "hmall"]): product_shoppingmall.append("백화점/홈쇼핑 몰")
        elif "oliveyoung" in url: product_shoppingmall.append("올리브영")
        elif any(shop in url for shop in ["eqlstore", "collecionb", "ohou.se"]): product_shoppingmall.append("인테리어/오브제 몰")
        elif "kurly" in url: product_shoppingmall.append("마켓컬리")
        elif "wconcept" in url: product_shoppingmall.append("29cm")
        elif "makers.kakao" in url: product_shoppingmall.append("")
        else: product_shoppingmall.append("기타 쇼핑몰")

    products["shoppingmall"] = product_shoppingmall
    
    video_ids = []
    urls = []
    product_info = []
    malls = []
    for idx, url in enumerate(products["productURL"]):
        if products["shoppingmall"][idx] == "카카오 선물하기":
            try: 
                temp_info =  get_kko_product_info(url)
                product_info.append(temp_info)
                urls.append(url)
                malls.append(products["shoppingmall"][idx])
                video_ids.append(products["videoID"][idx])
            except:
                print(f"excepted : {idx}")
                product_info.append(None)
                urls.append(url)
                malls.append(products["shoppingmall"][idx])
                video_ids.append(products["videoID"][idx])
        elif products["shoppingmall"][idx] == "29cm":
            try: 
                temp_info =  get_29cm_product_info(url)
                product_info.append(temp_info)
                urls.append(url)
                malls.append(products["shoppingmall"][idx])
                video_ids.append(products["videoID"][idx])
            except:
                print(f"excepted : {idx}")
                product_info.append(None)
                urls.append(url)
                malls.append(products["shoppingmall"][idx])
                video_ids.append(products["videoID"][idx])  
    
    products = pd.DataFrame({"videoID":video_ids, "productURL":urls, "productInfo":product_info, "shoppingmall":malls})

    products.dropna(subset=["productInfo"], inplace=True)
    products.reset_index(drop=True, inplace=True)
    product_InfoDF = pd.DataFrame(columns=["videoID", "productURL","shoppingmall", "product_name", "original_price", "current_price", "discount_rate", "brand_name", "brand_description", "brand_link_inshop", "thumbnail", "category"])
    for idx in range(len(products)):
        item = products["productInfo"].iloc[idx]
        item["videoID"] = products["videoID"].iloc[idx]
        item["productURL"] = products["productURL"].iloc[idx]
        item["shoppingmall"] = products["shoppingmall"].iloc[idx]
        try:
            tempDF = pd.DataFrame([item])[["videoID", "productURL", "shoppingmall", "product_name", "original_price", "current_price", "discount_rate", "brand_name", "brand_description", "brand_link_inshop", "thumbnail", "category"]]      
        except:
            item["brand_description"] = None
            tempDF = pd.DataFrame([item])[["product_name", "original_price", "current_price", "discount_rate", "brand_name", "brand_description", "brand_link_inshop", "thumbnail", "category"]]      
        product_InfoDF = pd.concat([product_InfoDF,tempDF])
    product_InfoDF.reset_index(inplace=True, drop=True)
    
    temp_data = data[["id", "searchQ", "title"]]
    temp_data.columns = ["videoID", "searchQ", "title"]
    product_InfoDF = pd.merge(product_InfoDF, temp_data, on="videoID", how="left")
    product_InfoDF.columns = ["video_id", "product_url", "product_name", "original_price",
                            "current_price", "discount_rate", "brand_name", "brand_description",
                            "brand_link_inshop", "thumbnail", "category", "search_key", "video_title"]
    product_InfoDF = product_InfoDF[["product_url", "product_name", 
                                    "original_price", "current_price", "discount_rate", 
                                    "brand_name", "brand_description", "brand_link_inshop", 
                                    "thumbnail", "category", 
                                    "search_key", "video_id", "video_title"]]
    product_InfoDF["original_price"] = product_InfoDF["original_price"].apply(remove_non_numeric)
    product_InfoDF["current_price"] = product_InfoDF["current_price"].apply(remove_non_numeric)

    product_info_lst = []
    for idx in range(len(product_InfoDF)):
        product_name = product_InfoDF.product_name[idx]
        brand_name = product_InfoDF.brand_name[idx]
        product_info_lst.append(search_category(product_name, brand_name))
        sleep(5)
    product_info_lst   

    path = DATA_PATH + "product_rawdata"+ strftime("%Y-%m-%d_%H:%M", gmtime()) + ".csv"
    product_InfoDF.to_csv(path)

    

def update_product_data_info():
    return
