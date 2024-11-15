import os
import sys
import requests
import google.generativeai as genai
from IPython.display import Image
from IPython.core.display import HTML

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..', '..')))
from secret import GEMINI_API_KEY

class DescriptionCreator:
    def __init__(self):
        self.config = genai.configure(api_key=GEMINI_API_KEY)
        generation_config = {
                                "temperature": 1.2,
                                "top_p": 0.95,
                                "top_k": 64,
                                "max_output_tokens": 200,
                                "response_mime_type": "text/plain",
                            }
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", 
                                           generation_config=generation_config)
        
        self.prompt = '''다음은 제품 상세 정보가 담긴 이미지야. 
                         이미지를 참고해서 제품의 특징을 요약해서 매력적인 문구를 작성해줘.
                         결과는 마크다운 형식을 제외하고 반드시 일반 텍스트로 작성해줘.
                         "{제목}\n{상세 설명}"과 같은 형식으로 50자 이내의 제목과 150자 이내의 상세 설명으로 구성해줘.
                         그리고 제목은 "{특징}한 {제품 종류}"와 같은 형식으로 작성해줘.
                         '''
    
    def creat_description(self, img_urls:list):#, reviews:str) -> str:
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
    hi = DescriptionCreator()
    result = hi.creat_description(['https://img.29cm.co.kr/next-brand/2024/08/28/d681d1054e334d95b68b0d9cf226fbda_20240828140614.jpg?width=100, https://gi.esmplus.com/jsolution4/lgt_2024/tumggu/tumggu_gift.jpg, https://gi.esmplus.com/jsolution4/lgt_2024/product_page/104314.jpg, https://ai.esmplus.com/jsolution22/SP_LEGODT/legodt_notice.jpg'])#, '')
    print(result)