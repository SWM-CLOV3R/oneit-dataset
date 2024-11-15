import os
import sys
import requests
# import shutil

import google.generativeai as genai
from IPython.display import Image
from IPython.core.display import HTML

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..', '..')))
from secret import GEMINI_API_KEY

# def download_image(image_url, save_path):
#     # 이미지 URL에서 데이터를 가져옵니다.
#     response = requests.get(image_url, stream=True)
    
#     # 요청이 성공했는지 확인합니다.
#     if response.status_code == 200:
#         # 바이너리 형식으로 데이터를 받아 파일로 저장합니다.
#         with open(save_path, 'wb') as file:
#             shutil.copyfileobj(response.raw, file)
#         print(f"Image successfully downloaded: {save_path}")
#     else:
#         print(f"Failed to retrieve image. Status code: {response.status_code}")

# # 예시 URL과 저장 경로
# image_url = "https://example.com/path_to_image.jpg"
# save_path = "downloaded_image.jpg"

# download_image(image_url, save_path)


class TagCreator:
    def __init__(self):
        self.config = genai.configure(api_key=GEMINI_API_KEY)
        generation_config = {
                                "temperature": 1.5,
                                "top_p": 0.95,
                                "top_k": 64,
                                "max_output_tokens": 300,
                                "response_mime_type": "text/plain",
                            }
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", 
                                           generation_config=generation_config)
        
        # self.prompt = '''
        #                 다음은 제품 상세 정보가 담긴 이미지와 상품에 대한 리뷰야. 이미지와 리뷰를 참고해서 제품의 특징을 보여줄 수 있는 태그를 만들어줘.
        #                 답변은 다른 말 붙이지 말고 잘 어울리는 태그만 나열해줘.
        #                 태그는 선물 관점에서 도움이 되는 태그로 구성해줘. 선물을 주는 대상과의 관계, 선물을 주는 이유, 선물로 구매하기 좋은 이유, 계절 등이 될 수 있어
        #                 태그 예시는 다음과 같아. 아래 예시 외에도 잘 어울리는 태그가 있다면 추가해줘.
        #                 #음식 #간식 #건강 #요리 #특색있는 #유니크 #운동 #심플 #커스텀 #봄 #여름 #생일 #졸업 #집들이 #결혼 #출산 #격려 #감사 #부모님 #친구 #선배 #상사 #애인
        #             '''    
        self.prompt = '''
                        다음은 제품 상세 정보가 담긴 이미지와 상품에 대한 리뷰야. 이미지와 리뷰를 참고해서 제품의 특징을 보여줄 수 있는 태그를 골라줘.
                        답변은 다른 말 붙이지 말고 잘 어울리는 태그만 나열해줘. 태그는 선물 관점에서 도움이 되는 태그로 구성해줘.
                        태그 예시는 다음과 같아. 다음 예시 중에서 적절한 태그를 골라서 답변해주면 돼.
                        #남성 #여성 #원색 #파스텔톤 #무채색 #심플 #유니크 #캐주얼 #집 #야외 #디자인중심 #실용성중심 #달달한 #달달하지않은 #요리 #건강 #스킨케어 #색조화장 #화장관심없음 #헤어케어 #향기
                      '''
    
    def create_tags(self, img_urls:list):#, reviews:str) -> str:
        try:
            if len(img_urls) == 1:
                img_response = requests.get(img_urls[0])
                img_path = './details/img.jpg'
                input_img_lst = [img_path]
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                
                image = Image(img_path)
                    
                result = self.model.generate_content([image,self.prompt]).text#([image, reviews, self.prompt]).text

            elif len(img_urls) > 1:
                input_img_lst = []
                for i, img in enumerate(img_urls):
                    img_response = requests.get(img)
                    img_path = f'./details/img{i+1}.jpg'
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                        input_img_lst.append(Image(img_path))
                
                result = self.model.generate_content(input_img_lst + [self.prompt]).text#(input_img_lst + [reviews, self.prompt]).text

        finally:
            # 다운로드한 이미지 파일들을 삭제합니다.
            for img_path in input_img_lst:
                if os.path.exists(img_path):
                    os.remove(img_path)

        return result

if __name__ == '__main__':
    hi = TagCreator()
    result = hi.create_tags(['https://st.kakaocdn.net/product/gift/editor/20240905214929_cf9d736138bf4404840a4f10a4f30e65.png'])#'')
    print(result)