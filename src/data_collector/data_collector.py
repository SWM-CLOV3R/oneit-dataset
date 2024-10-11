from sqlalchemy import create_engine, text
from sqlalchemy import Column, Integer, Text, JSON, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import json
import os
import sys
from time import sleep

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..', '..')))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

from data_crawler.cm29_crawler import CM29Crawler
from data_crawler.kkogift_crawler import KkoGiftCrawler
from data_crawler.musinsa_crawler import MusinsaCralwer
from generation.description_generator import DescriptionCreator
from generation.tagging import TagCreator
from get_source.youtube_resource import YoutubeResource

from preprocess import delete_info_from_product_name, remove_extra_spaces
from category_normalize import search_category
from secret import *

Base = declarative_base()
class RawContent(Base):
    __tablename__ = 'raw_content'
    idx = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text)
    content = Column(JSON)

def get_crawler(url:str):
    if '29cm' in url:
        return CM29Crawler(url)
    elif  'kko.to' in url or 'gift.kakao.com' in url:
        return KkoGiftCrawler(url)
    elif 'musinsa' in url:
        return MusinsaCralwer(url)
    else:
        raise ValueError(f"지원하지 않는 URL입니다: {url}")
    
def get_product_data(url:str):
    # DB설정
    connection_url = f"mysql+mysqldb://{LOCAL_USER_NAME}:{LOCAL_PASSWORD}@localhost:{PORT}/{TEST_DATABASE}"
    engine = create_engine(connection_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # URL이 이미 존재하는지 확인
        existing_product = session.execute(
            text("SELECT idx FROM product WHERE product_url = :url"),
            {"url": url}
        ).fetchone()

        if existing_product:
            print(f"URL {url}은 이미 존재합니다.")
            product_idx = existing_product[0]

            existing_raw_content = session.execute(
                text("SELECT idx FROM raw_content WHERE url = :url"),
                {"url": url}
            ).fetchone()           
        
        else:
            result = session.execute(
                text("INSERT INTO product (product_url, status) VALUES (:url, 'ACTIVE')"),
                {"url": url}
            )
            session.commit()
            product_idx = result.lastrowid

        # 크롤링 수행
        crawler = get_crawler(url)
        
        crawler.cookie_maker()
        content = crawler.fetch_content()

        if not content:
            print(f'no contents in page: {url}')
            return

        # Raw content 테이블에 컨텐츠 넣기
        existing_raw_content = session.execute(
                text("SELECT idx FROM raw_content WHERE url = :url"),
                {"url": url}
            ).fetchone()
            
        if existing_raw_content:
            raw_content_idx = existing_raw_content[0]
        else:
            raw_content = json.dumps(content)
            new_raw_content = RawContent(url=url, content=raw_content)
            session.add(new_raw_content)
            session.commit()
            raw_content_idx = result.lastrowid

        # 컨텐츠 파싱
        product_info =  crawler.parse_content(content)
        
        update_query =  """
                            UPDATE product 
                            SET
                                name = :name,
                                brand_name = :brand_name,
                                original_price = :original_price,
                                current_price = :current_price,
                                mall_name = :mall_name,
                                thumbnail_url = :thumbnail_url,
                                details_url = :details_url,
                                gender = :gender,
                                category_inmall = :category_inmall,
                                option_lst = :option_lst,
                                custom = :custom,
                                reviews = :reviews,
                                review_count = :review_count,
                                rate_avg = :rate_avg,
                                wish_count = :wish_count,
                                recommend = :recommend,
                                brand_other = :brand_other,
                                raw_response_idx = :raw_response_idx
                            WHERE idx = :idx
                        """

        session.execute(text(update_query), {
            "name": remove_extra_spaces(delete_info_from_product_name(product_info['name'])),
            "brand_name": product_info['brand'][0],
            "original_price": product_info['original_price'],
            "current_price": product_info['current_price'],
            "mall_name": crawler.__class__.__name__.replace('Crawler', ''),
            "thumbnail_url": str(product_info['thumbnail_urls']),
            "details_url": str(product_info['detail_urls']),
            "gender": product_info['gender'],# if product_info['gender'] else None,
            "category_inmall": product_info['category_inmall'],
            "option_lst": json.dumps(product_info['option']), # if product_info['option'] else None,
            "custom": ', '.join(product_info['custom']) if product_info['custom'] else None,
            "reviews": json.dumps(product_info['review']),
            "review_count": product_info['review_count'],
            "rate_avg": product_info['rate_avg'],# if product_info['custom'] else None,
            "wish_count": product_info['wish_count'],# if product_info['custom'] else None,
            "recommend": json.dumps(product_info['recommend']),
            "brand_other": json.dumps(product_info['brand_other']),
            "raw_response_idx": raw_content_idx,
            "idx": product_idx
        })

        session.commit()
        print(f"제품 정보 파싱 완료. (idx: {product_idx})")

        # 카테고리 정규화
        norm_category = search_category(product_info['name'], product_info['brand'][0])
        if norm_category:
            # category_display_name 업데이트
            update_category_query = """
                UPDATE product 
                SET category_display_name = :category_display_name
                WHERE idx = :idx
            """
            session.execute(text(update_category_query), {
                "category_display_name": norm_category,
                "idx": product_idx
            })

            # 대분류 찾기
            main_category = norm_category.split('>')[0].strip()

            # category 테이블에서 대분류에 해당하는 category_idx 찾기
            category_query = """
                SELECT idx FROM category
                WHERE name = :main_category
            """
            category_result = session.execute(text(category_query), {
                "main_category": main_category
            }).fetchone()

            if category_result:
                category_idx = category_result[0]
                # product 테이블의 category_idx 업데이트
                update_category_idx_query = """
                    UPDATE product 
                    SET category_idx = :category_idx
                    WHERE idx = :idx
                """
                session.execute(text(update_category_idx_query), {
                    "category_idx": category_idx,
                    "idx": product_idx
                })

        session.commit()
        print(f"카테고리 정보 업데이트 완료. (idx: {product_idx})")
    
        # description 생성 + DB 업데이트
        reviews = product_info['review']
        description = DescriptionCreator().creat_description(product_info['detail_urls'])#, reviews)
        update_description_query = """
            UPDATE product 
            SET description = :description
            WHERE idx = :idx
        """
        session.execute(text(update_description_query), {
            "description": description,
            "idx": product_idx
        })
        session.commit()
        print(f"상품 요약 정보 업데이트 완료. (idx: {product_idx})")

        # tagging + DB 업데이트
        tag_lst = TagCreator().create_tags(product_info['detail_urls'])#, reviews)
        update_tag_query = """
            UPDATE product 
            SET tag_lst = :tag_lst
            WHERE idx = :idx
        """
        session.execute(text(update_tag_query), {
            "tag_lst": tag_lst,
            "idx": product_idx
        })
        session.commit()
        print(f"태그 리스트 업데이트 완료. (idx: {product_idx})")
    

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        session.rollback()

    session.close()
    


def get_content(maxCount:int, order:str):
    # DB설정
    connection_url = f"mysql+mysqldb://{LOCAL_USER_NAME}:{LOCAL_PASSWORD}@localhost:{PORT}/{TEST_DATABASE}"
    engine = create_engine(connection_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    tot_prodcut_urls = []
    youtube = YoutubeResource()
    search_keyword = ["#선물추천", "선물언박싱", "생일선물언박싱", "#카카오톡선물하기"]
    for keyword in search_keyword:
        video_lst = youtube.get_resource_info(keyword, maxCount, order)
        for vid, vinfo in video_lst.items():
            try:
                # 비디오 ID가 이미 존재하는지 확인
                existing_source = session.execute(
                    text("SELECT idx FROM source WHERE content_id = :content_id"),
                    {"content_id": vid}
                ).fetchone()

                if existing_source:
                    print(f"비디오 ID {vid}는 이미 존재합니다.")
                    continue
                
                else:
                    parsed_vinfo_dict = youtube.parse_resource_info(vinfo)
                    product_urls = str(youtube.get_product_url(parsed_vinfo_dict))
                    # 새로운 소스 추가
                    source_insert_query = """
                        INSERT INTO source (type, content_id, search_key, product_urls, content)
                        VALUES (:type, :content_id, :search_key, :product_urls, :content)
                    """
                    result = session.execute(text(source_insert_query), {
                        "type": "youtube",
                        "content_id": vid,
                        "search_key": keyword,
                        "product_urls": product_urls,
                        "content": json.dumps(vinfo)
                    })
                    session.commit()
                    print(f"새로운 소스가 추가되었습니다. (video_id: {vid})")
                    
                    tot_prodcut_urls += eval(product_urls)
                    # for url in eval(product_urls):
                    #     get_product_data(url)
                
            except Exception as e:
                print(f"소스 추가 중 오류 발생: {str(e)}")
                session.rollback()
                continue
            
        sleep(1)
    session.close()
    return tot_prodcut_urls

def run_collector(maxcount=10, order= 'relevance'):
    product_candidates = get_content(maxcount, order)
    print(len(product_candidates))
    for url in product_candidates:
        get_product_data(url)



if __name__ == '__main__':
    # run_collector(30, order='relevance')
    run_collector(50, order='date')


