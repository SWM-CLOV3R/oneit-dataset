import re

def remove_non_numeric(input_string):
    # 숫자가 아닌 모든 문자를 찾는 정규 표현식 패턴
    pattern = r"[^0-9]"
    # 숫자가 아닌 모든 문자를 빈 문자열로 대체
    cleaned_string = re.sub(pattern, "", input_string)
    return int(cleaned_string)

def remove_extra_spaces(text):
    return re.sub(r"\s+", " ", text).strip()

def delete_info_from_product_name(product_name):
    patterns = [r"\(.*?\)", r"\[.*?\]", r"\{.*?\}", r"<.*?>", r"\".*?\"", r"\".*?\"", r"\d+종\s*택1", r"\d+종 중 택1", r"\d+종세트", r"\S*세트", r"출시"]
    for pattern in patterns:
        product_name = re.sub(pattern, "", product_name)
    
    product_name = remove_extra_spaces(product_name)
    return product_name

def split_product_name_by_special_characters(product_name):
    parts = re.split(r"[^a-zA-Z0-9\s가-힣]", product_name)
    parts = [part.strip() for part in parts if part.strip()]
    return parts