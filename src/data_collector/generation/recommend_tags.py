import os
import sys 
import requests
# from PIL import Image
import PIL.Image

from io import BytesIO

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..', '..')))
from secret import GPT_API_KEY, GEMINI_API_KEY

from openai import OpenAI
import google.generativeai as genai

from IPython.display import Image
from IPython.core.display import HTML

class RecommendTagCreator:
    def __init__(self):
        self.openai_prompt = {
                                'img2info' : [
                                                    {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed images of the product.'},
                                                    {'role': 'user', 'content': '당신은 제품 상세 이미지를 보고 제품의 특징을 요약해주는 마케터입니다.'},
                                                    {'role': 'user', 'content': '제품에 대한 상세 이미지를 참고해서 해당 제품만의 특징 정보를 작성해주세요'},
                                                  ],
                                'style' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#캐주얼 #유니크 #심플 #해당없음". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같아 {"#유니크" : "이 오브제는 해당 디자이너의 감성이 담겨 특이한 형태를 가지고 있기 때문"}. 이때 잘 어울린다고 생각하는 키워드를 최소로 선택하고 여러개 선택했다면 관련이 높다고 생각하는 순으로 작성해줘'}
                                          ],
                                'color' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#쨍한원색 #파스텔톤 #무채색". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같아 {"#쨍한원색" : "강렬한 색감의 외관을 가지고 있음"}'}
                                          ],
                                'lifestyle' : [
                                                {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON'},
                                                {'role': 'user', 'content': '제품의 특징으로 제안할 수 있는 태그는? "#집안 #야외". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#야외" : "여행갔을 때 필요한 물품이기 때문"}. 두 태그 중 더 가까운 것을 가능한 하나만 선택해주세요'}
                                              ],
                                'tendency' : [
                                                {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                                {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#실용성주의 #디자인중심". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#실용성중심" : "다양한 기능이 있어 기능 면에서 구매 욕구를 자극하는 제품이기 때문"}. 두가지 태그 중 잘 어울리는 것만 선택해서 어울리는 순서로 작성해줘'}
                                             ],
                                'taste' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#달콤 #상큼 #색다른 #달달하지않은 #해당없음". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#달달하지않은" : "티는 달달하지는 않지만 많은 사람들이 즐기는 간식이기 때문"}. 음식과 관련된 제품이라면 태그 중 잘 어울리는 순서로 작성해줘'}
                                          ],
                                'health' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#건강식 #영양제 #운동 #해당없음". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#건강식" : "도시락통은 식단 관리를 할 때 자주 쓰이기 때문"},{"#해당없음":"디저트는 건강관리에는 도움이 되는 음식은 아니기 때문"}. 태그 중에서 잘 어울리는 순서로 작성해줘'}
                                           ],
                                'makeup' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#스킨케어 #색조 #남성화장품 #해당없음". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#색조" : "해당 립스틱은 다양한 색상 옵션으로 색조 메이크업을 많이 하는 사람들이 사용하기 때문"}. 뷰티와 관련된 제품이라면 태그 중 잘 어울리는 순서로 작성해줘'}
                                           ],
                                'fragrance' : [
                                                {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                                {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#향기제품 #보습향기제품 #해당없음". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#보습향기제품" : "이 바디워시는 좋은 향과 더불어 보습에도 좋기 때문"}. 뷰티와 관련된 제품이라면 태그 중 잘 어울리는 태그를 선택하고 관련성이 높은 순서로 작성해줘'}
                                                
                                              ],
                                'hobby' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                            {'role': 'user', 'content': '제품과 잘 어울리는 태그는? "#요리 #여행 #컨텐츠감상 #기타". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#요리" : "주방용품은 요리가 취미인 사람들이 자주 활용하고 구매하기 때문"}. 태그를 가능한 하나 선택하고 여러개 선택했을 경우 그 중 잘 어울리는 순서로 작성해줘. 그리고 "#기타" 다른 태그가 어울리지 않을 경우 선택해줘.'},
                                          ],
                                'goal' : [
                                            {'role': 'system', 'content': 'You are a helpful assistant that summarizes the information in the detailed information of the product to output JSON.'},
                                            {'role': 'user', 'content': '제품을 선물하기 좋을 것 같은 대상은? "#생일 #기념일 #집들이". 반드시 {tag: reason} 형태로 나열해주세요. 답변 예시는 다음과 같습니다. {"#집들이" : "집들이에서 함께 먹는 용으로 선물하기 좋기 때문"}. 태그를 하나 이상 선택하고 잘 어울리는 상황을 순서대로 작성해주세요.'},
                                         ]
                             }

    def openai_img_prompt_maker(self, img_urls:list):
        content = [{'type': 'text', 'text': '제품의 상세 이미지야. 참고해서 제품에 대한 정보를 제공해줘'}]
        for img in img_urls:
            temp = {
                        'type': 'image_url',
                        'image_url': {'url': img},
                    }
            content.append(temp)
        
        return {'role' : 'user',
                'content': content}
    
    def get_info_from_details(self,  img_urls:list, max_tokens=3000, model = 'gpt-4o'):
        if 'gpt' in model or 'o1' in model:
            client = OpenAI(api_key=GPT_API_KEY)
            messages = self.openai_prompt['img2info']
            messages.append(self.openai_img_prompt_maker(img_urls))

            response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
            client.close()

            return response.choices[0].message.content
        
        elif 'gemini' in model:
            input_img_lst = []
            img_path_lst = []
            try:
                for i, img in enumerate(img_urls):
                    img_response = requests.get(img)
                    img_data = PIL.Image.open(BytesIO(img_response.content))
                    img_path = f'./details/img{i+1}.jpg'
                    if len(img_response.content) > 500 * 1024:
                        img_data = img_data.resize((img_data.width // 2, img_data.height // 2))
                        img_data.save(img_path, quality=85)
                        img_path_lst.append(img_path)
                    else:
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                            input_img_lst.append(Image(img_path))
                        img_path_lst.append(img_path)

                    generation_config = {
                                            'temperature': 1.2,
                                            'top_p': 0.95,
                                            'top_k': 64,
                                            'max_output_tokens': max_tokens,
                                            'response_mime_type': 'text/plain',
                                        }
                    genai.configure(api_key=GEMINI_API_KEY)
                    client = genai.GenerativeModel(model_name=model, 
                                                   generation_config=generation_config,
                                                   system_instruction = '당신은 선물을 고르는 고객을 대상으로 제품에 대한 정보를 제공하는 쇼핑 도우미 큐레이터입니다.')
                
                result = client.generate_content(input_img_lst + [self.genai_prompt['ver2']]).text

            finally:
                # 다운로드한 이미지 파일들을 삭제합니다.
                for img_path in img_path_lst:
                    # print(img_path)
                    if os.path.exists(img_path):
                        os.remove(img_path)

            return result
        
        return None
    
    def recommend_tagger(self, mode, info,model='gpt-4o', max_tokens=300,options=None):
        messages = self.openai_prompt[mode]
        messages.append([{'role':'user', 'content':info}])

        if options:
            messages.append([{'role': 'user', 'content':f'선택할 수 있는 옵션은 다음과 같아. {options}가 색상과 관련이 있다면 참고하도록 하세요'}])

        client = OpenAI(api_key=GPT_API_KEY)
        
        tag_result = client.chat.completions.create(model=model, messages=messages, response_format={"type": "json_object"},max_tokens=max_tokens).choices[0].message.content
        
        return tag_result


        




        
