import re
import requests

def check_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return True
        else:
            # print(f"URL returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        # print(f"URL check failed: {e}")
        return False
    
def get_final_url(short_url):
    try:
        response = requests.head(short_url, allow_redirects=True, timeout=5)
        return response.url
    except requests.exceptions.RequestException as e:
        print(f"Failed to expand URL: {short_url} -> {e}")
        return short_url
    

def extract_urls(text):
    # URL을 찾기 위한 정규 표현식 패턴
    url_pattern = re.compile(r'(https?://[^\s]+?)(?=\s|https?://|$)')
    # 패턴에 맞는 모든 URL을 찾기
    urls = url_pattern.findall(text)
    
    return urls

def remove_non_numeric(input_string):
    # 숫자가 아닌 모든 문자를 찾는 정규 표현식 패턴
    pattern = r'[^0-9]'
    # 숫자가 아닌 모든 문자를 빈 문자열로 대체
    cleaned_string = re.sub(pattern, '', input_string)
    return int(cleaned_string)

def remove_extra_spaces(text):
    return re.sub(r'\s+', ' ', text).strip()

def delete_info_from_product_name(product_name):
    patterns = [r'\(.*?\)', r'\[.*?\]', r'\{.*?\}', r'<.*?>', r'\".*?\"', r'\'.*?\'', r'\d+종\s*택1', r'\d+종 중 택1', r'\d+종세트', r'\S*세트', r'출시']
    for pattern in patterns:
        product_name = re.sub(pattern, '', product_name)
    
    product_name = remove_extra_spaces(product_name)
    return product_name

def split_product_name_by_special_characters(product_name):
    parts = re.split(r'[^a-zA-Z0-9\s가-힣]', product_name)
    parts = [part.strip() for part in parts if part.strip()]
    return parts