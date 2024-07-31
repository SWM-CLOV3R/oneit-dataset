import os
import sys
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from get_category import search_category
from preprocess import remove_non_numeric, delete_info_from_product_name

def product_29cm_info(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 값 파싱
    # 1. 상품명
    try:
        product_name = soup.select_one('#pdp_product_name').get_text().strip()
    except:
        return None

    # 2. 가격
    if soup.select_one('p.css-1bci2fm.ejuizc31'): # 할인할 때
        original_price = remove_non_numeric(soup.select_one('p.css-1bci2fm.ejuizc31').get_text().strip())
        current_price = remove_non_numeric(soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip())
        discount_rate = remove_non_numeric(soup.select_one('span.css-1jsmahk.ejuizc32').get_text().strip())
    else: # 할인 안할 때
        current_price = remove_non_numeric(soup.select_one('span.css-4bcxzt.ejuizc34').get_text().strip())
        original_price = current_price
        discount_rate = 0

    # 3. 브랜드 정보
    try:
        brand_name = soup.select_one('h3.css-1dncbyk.eezztd84').get_text().strip()
        brand_description = soup.select_one('p.css-8e7eit.eezztd85').get_text().strip()
        brand_link_inshop = soup.select_one('a.css-12w33mp.eezztd81')['href']
    except:
        brand_name = None
        brand_description = None
        brand_link_inshop = None
        print('HTML class 이름이 변경된 것으로 추측됨')
        
    # 4. 상품 대표 이미지
    try:
        thumbnail = soup.select_one('div.css-122y91a.e3e1mx64').select_one('img')['src']
    except:
        thumbnail = None

    # 5. 상품 카테고리
    category = search_category(product_name, brand_name)


    product_info_table = dict(product_name=delete_info_from_product_name(product_name), 
                              original_price=original_price, current_price=current_price, discount_rate=discount_rate,
                              brand_name=brand_name,
                              thumbnail=thumbnail, category=category)
    
    # 6. 상품상세 정보 표
    product_info_lst= soup.select_one('table.e1hw6jas2.css-1x7jfi1.exbpx9h0').select('tr')
    for product_info in product_info_lst:
        info_name , info_val = product_info.select_one('th').get_text().strip(), product_info.select_one('td').get_text().strip()
        if '상세페이지' in info_val: continue
        product_info_table[info_name] = info_val

    return product_info_table


def product_kko_info(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 값 가져오기
    # 0. 상태 확인
    status = soup.select_one('product-stamp')
    if status.get_text():
        return None
    
    # 1. 상품명
    product_name = soup.select_one('h2.tit_subject').get_text()
    # 2. 가격
    if soup.select_one('span.txt_sale'): # 할인 함
        discount_rate = remove_non_numeric(soup.select_one('span.txt_sale').get_text())
        original_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_price').get_text())
        current_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text())
    else: # 할인 안 함
        current_price = remove_non_numeric(soup.select_one('div.info_product.clear_g').select_one('span.txt_total').get_text())
        original_price = current_price
        discount_rate = 0
        
    # 3. 브랜드 정보
    brand_name = soup.select_one('span.txt_shopname').get_text()
    brand_link_inshop = 'https://gift.kakao.com' + soup.select_one('a.link_shopname')['href']
    
    # 4. 상품 대표 이미지
    try:
        thumbnail = soup.select_one('swiper-slide.cont_slide.swiper-slide-active').select_one('img')['src']
    except:
        thumbnail = None
    
    # 5. 상품 카테고리
    category = search_category(product_name, brand_name)

    product_info_table = dict(product_name=delete_info_from_product_name(product_name), 
                              original_price=original_price, current_price=current_price, discount_rate=discount_rate,
                              brand_name=brand_name,
                              thumbnail=thumbnail, category=category)

    # 6. 상품상세 정보 표
    product_info_lst= soup.select_one('table.tbl_detail').select('tr')
    for product_info in product_info_lst:
        info_name , info_val = product_info.select_one('th').get_text(), product_info.select_one('td').get_text()
        if info_val == '상품상세설명 참조': continue
        product_info_table[info_name] = info_val

    return product_info_table

