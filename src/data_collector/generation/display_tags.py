import os
import sys 
import requests
# from PIL import Image
import PIL.Image

from io import BytesIO

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..', '..')))
from secret import GPT_API_KEY, GEMINI_API_KEY

from openai import OpenAI, FineTune
import google.generativeai as genai

from IPython.display import Image
from IPython.core.display import HTML


class DisplayTagCreator:
    def __init__(self):
        self.openai_prompt = {
                                'ver-curation':[
                                                {"role": "system", "content": "You are a helpful marketer that curates the appeal of a product from a gift perspective and recommends keywords for the product."},
                                                {"role": "user", "content": "당신은 선물을 주는 사람에게 제품의 장점을 드러낼 수 있는 키워드를 제공하는 큐레이터입니다."},
                                                {"role": "user", "content": "제품의 리뷰를 참고해서 선물을 준비하는 사람에게 해당 제품을 선물하기에 적합한 대상, 상황을 제안하며, 제품의 장점을 설명해주세요"},
                                               ],
                                'ver-img2info':[
                                                {"role": "system", "content": "You are a helpful assistant that summarizes the information in the detailed images of the product."},
                                                {"role": "user", "content": "당신은 제품 상세 이미지를 보고 제품의 특징을 요약해주는 마케터입니다."},
                                                {"role": "user", "content": "제품에 대한 상세 이미지를 참고해서 해당 제품만의 특징 정보를 작성해주세요"},
                                               ]
                             }
        self.genai_prompt = {
                                'ver1': '''
                                            제공해주는 제품명, 제품 정보, 제품군 정보를 참고해서 해당 제품 만의 특징과 장점을 보여줄 수 있는 태그를 만들어주세요.
                                            답변은 다른 말 붙이지 말고 잘 어울리는 태그만 나열해줘. 태그는 선물을 고르는 사람에게 상황, 대상 등을 고려해 도움이 되는 태그로 구성해주세요.
                                            태그 예시는 다음과 같습니다. #집들이선물, #친구선물, #귀여운 #감성적인
                                            브랜드 명칭이나 제품군과 같은 제품 기본 정보는 태그에서 제외해주세요,
                                        ''',
                                'ver2': '''
                                            당신은 제품 상세 이미지를 보고 제품의 특징을 요약해주는 마케터입니다.
                                            제공해주는 제품의 상세 이미지를 참고해서 해당 제품만의 특징 정보를 추출해주세요.
                                        '''                                
                            }

    
    def openai_img_prompt_maker(self, img_urls:list):
        content = [{"type": "text", "text": "제품의 상세 이미지야. 참고해서 제품에 대한 정보를 제공해줘"}]
        for img in img_urls:
            temp = {
                        "type": "image_url",
                        "image_url": {"url": img},
                    }
            content.append(temp)
        
        return {'role' : 'user',
                'content': content}


    def get_info_from_details(self,  img_urls:list, max_tokens=3000, model = 'gpt-4o'):
        if 'gpt' in model or 'o1' in model:
            client = OpenAI(api_key=GPT_API_KEY)
            messages = self.openai_prompt['ver-img2info']
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
                        with open(img_path, "wb") as f:
                            f.write(img_response.content)
                            input_img_lst.append(Image(img_path))
                        img_path_lst.append(img_path)

                    generation_config = {
                                            "temperature": 1.2,
                                            "top_p": 0.95,
                                            "top_k": 64,
                                            "max_output_tokens": max_tokens,
                                            "response_mime_type": "text/plain",
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

      
    
    def product_curator(self, reviews:list, info:str, max_tokens=500):
        client = OpenAI(api_key=GPT_API_KEY)
        model = 'gpt-4o'
        messages = self.openai_prompt['ver-curation']
        if info:
            content = {"role": "user", "content": '\n'.join([info, ' '.join(reviews)])}
            messages.append(content)
        else:
            content = {"role": "user", "content": ' '.join(reviews)}
            messages.append(content)        
            
        response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)

        return response.choices[0].message.content
    
    
    def display_tag_maker(self, title:str, category_inmall:str, curation:str):
        model = 'gemini-1.5-flash' # 'gemini-1.5-pro'
        generation_config = {
                                "temperature": 1.2,
                                "top_p": 0.95,
                                "top_k": 64,
                                "max_output_tokens": 300,
                                "response_mime_type": "text/plain",
                            }
        genai.configure(api_key=GEMINI_API_KEY)
        client = genai.GenerativeModel(model_name=model, 
                                       generation_config=generation_config,
                                       system_instruction = '당신은 선물을 고르는 고객을 대상으로 제품에 대한 정보를 제공하는 쇼핑 도우미 큐레이터입니다.')
        
    
        try:
            response = client.generate_content([title+' : ' + category_inmall, curation, self.genai_prompt['ver1']])
        except: return None

        return response.text
    

    def run(self, img_urls:list, reviews:list, title:str, category_inmall:str,model='gpt-4o'):
        info = self.get_info_from_details(img_urls, max_tokens=1500,model=model)
        curation = self.product_curator(reviews, info, max_tokens=1500)
        tags = self.display_tag_maker(title, category_inmall, curation,)
        return tags

if __name__ == '__main__':
    title = '무아스 바람건조 온열 UV 무선 휴대용 칫솔 살균기 히팅건조'
    url = 'https://product.29cm.co.kr/catalog/2191811'
    detail_urls = ['https://mooas09.hgodo.com/mooas/portable-toothbrush_01.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_03.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_04.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_05.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_06.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_07.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_08.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_09.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_11.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_12.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_13.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_14.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_16.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_17.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_18.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_19.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_21.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_23.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_24.jpg', 'https://mooas09.hgodo.com/mooas/portable-toothbrush_25.jpg', 'https://mooas09.hgodo.com/common/mooas_warranty.jpg']
   
    reviews = ['커버를 열었다 닫으면 바로 불이 들어오면서 바람도 나오고 살균이 되나봐여~~저는 칫솔 꺼냈을 때는 작동 안하게 옆에 버튼 눌러줘요~노랑색이 넘 귀엽고 예뻐요~~약간 무게감이 있지만 사무실에 두고 쓰는거라 부담이 느껴질 정도는 아니고, 휴대용으로 갖고 다니기엔 좀 무겁다 느낄 수 있어요~작동할 때 소리도 크지 않아 좋습니다! ', '회사에서 휴대용으로 쓸려고 샀는데\n일단 기존에 있던 휴대용칫솔살균기는 건전지용으로\n매번 건전기 갈아줘야해서 불편하도 번거로웠는데\n이번에 산 제품을 충전식으로 너무 편하고 좋으며\n살균효과 바람건조 고온가열 등 장점들이 많아\n칫솔을 깨끗하게 사용할 수 있어서 좋아요 :)', '색깔 너무 귀엽고 작동 잘하구 다 조아요!!! 딱 하나 아쉬운건 이게 렌즈통 같은 오픈형식이라서 자석 붙여놓은 상태에서 여는 것이 살짝 불편합니다 전에 버튼 형식 썼는데 그게 더 편한거가타요 저는 항상 저렇게 붙이고 써왔어서 요렇게 쓰시는 분들은 참고..', '사무실에서 사용할 칫솔살균기가 필요했는데 마침 할인도 하고 사고싶었던 브랜드라 후딱 구매했습니다 :) 색도 넘 이쁘고 사이즈가 아주 딱이여서 사무실에서 사용하거나 휴대용으로도 넘 좋은것 같아서 강추입니다!!!!', '택배 받자마자 충전중입니다 :) 예전에 더 비싼 제품 사용했는데 금방 고장나더라구요 ...그래서 더 작지만 알차면서 가격이 착한 제품 찾다가 구매했어요 :)\n사무실에서 쓸 예정인데 만족스럽길!! 기대합니당ㅎㅎ', '약간 둥근듯한 모서리와 몸체가 귀여워용 ㅎㅎㅎ 칫솔살균기 중에 평이 젤 좋길래 샀는데 만족합니다. 건조될 때 소리가 조금 나긴하지만 빨리 건조되어 크게 신경쓰이진 않아요. 전체적으로 만족합니다!', '사무실 자리 벽에 붙여놓고 사용해요 양치\n후 먼지 걱정없이 뚜껑 안에 쏙 넣으면 되고 살균까지 해주니까 너무 좋아요 자석으로 부착돼서 떼고 붙일 수 있어서 편리하고 한번 충전하면 오래가서 더 좋아요 ㅎㅎ', '크기가 사진으로 봤던거랑 똑같아요. 바람으로 말려지는 소리?가 엄청 작아서 사무실에서 거의 들리지도 않고 칫솔에 먼지쌓일 걱정 안해도 돼서 넘 좋이요ㅎㅎ 자석도 있어서 거치해놓기도 너무 편해요', '작동시키면 소리가 거의 안나요. 조용해서 좋아요.\n자력도 세서 고정 잘 됩니다. \n근데 뚜껑 열 때 마다 실행되다 보니까 \n칫솔 넣어놨다가 다시 꺼낼 때 작동되는 것만 조심하면 될 것 같아요.', '커플템으로 맞췄습니다 두가지색상 모두 예뻐요!\n고민많이하다가 무아스로 골랐는데 후회안해요!!\n맨들맨들 무광이라 촉감도 좋고 소음도 다른소음에 묻혀서그런지 잘 안들려요', '왕타칫솔 쓰는데 큰칫솔도 다 들어가서 너무 좋아요!\n바람 건조 쎄지는 않는데 안나오는 것보다 낫고\n자석도 튼튼하고\n몇번 떨어트렷는데 고장도 안납니다.\n충전은 3주에 한번?', '적당한 사이즈에 칫솔도 안정되게 쏙 들어가서 만족스럽습다. 한번의 작동으로 칫솔이 다 마르지는 않아서 두세번 더 작동시켰어요. 한두시간 지나도 외부에 두는것처럼 바싹 마르지는 않는것 같아서 조금 염려되지만 오염된 환경에 노출시키지 않는다는 점을 위안삼아 잘 사용해보려고 합니다', '심플하고 소음도 없는 편이네요. 실제로 효과가 어느정도인지는 눈에 보이지않아 알 수는 없겠지만, 안 쓰는 것보다는 좋겠지 하는 마음으로 사용해봅니다ㅎㅎ', '건조 소리도 조용하고, 생각보다 무게감도 없어서 휴대하기 편합니다. 사용전 칫솔 물기 제거후 사용하라고 되어있어서 물기 닦고 사용했더니 뽀송합니다.', '사무실에서 너무 잘 쓰고있어요\n아무래도 좀 찝찝 했는데 살균도 되고 통풍도되고\n디자인도 너무 맘에 들어요!!!!\n동봉되서 온 자석도 잘 이용중입니다ㅎㅎ', '색도 예쁘고 좋아요 선물하기도 좋고 여행갈때 휴대용으로도 가볍고 좋을것 같아요 욕실 수납장 안에 자석으로 붙여서 쓰고 있는데 완전 만족입니다', '아직 충전 하느라 사용은 못했지만 \n디자인이 너무 깔끔하고 색도 좋네요\n바람 건조인 것도 좋아요\n무아스제품을 평소에 좋아해서 믿고 써보겠습니다\n', '원래 쓰던 칫솔살균기가 있었는데 따로 건조시키고 보관하다보니 아예 건조 기능 있는 제품으로 사자 싶어 이 제품으로 구매했습니다.\n사이즈가 손바닥 반 정도하니 작은 사이즈는 아니지만 어차피 사무실에 두고 쓸거라 괜찮았구요, 색상도 예뻐서 마음에 듭니다 :)', '생각했던 크기지만 칫솔을 넣으니 뭔가 거대한 느낌이에요 일단 조용한 편이라 마음에 들어요 건조나 살균이 잘 되는지는 써봐야 알 것 같아요', '사무실에서 사용하려고 샀습니다! 무슨 색으로 할지 고민하다가 노란색했는데 잘 선택한 거 같아요ㅎㅎ 색깔 너무 예쁘고 작동도 잘 됩니다']
    category_inmall = '가전>이미용가전>전동칫솔,칫솔살균기'
    detail_urls = ['https://img.29cm.co.kr/item/202405/11ef12bc5ab99d1fb9bba1ca3b3bbf7e.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e70dc0819b2a27f37b096cc88b0.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e70e1c51064a27f954ffc8102a7.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e70e7820716a27f05bf7a2f43f0.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e70f31bd888a27f339f9fe5aa0d.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e70f71a7de99714e3a9fc79d28a.png?width=1000', 'https://img.29cm.co.kr/item/202410/11ef87783c950947b8a23935c38423b8.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e7102ed87cd9714c1fd651f905b.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e710b66b7cea27f2d0cea4747ce.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e711556aa4f9714e143bf97f5a9.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e7133722f5197143393b078e0d8.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e71370fc803a23c4b0a0220d5c3.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e71dc0c9141a23c17bfafd37e73.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e71e63127caa27fb7670ad26fe8.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e71f8f27ced9714712e633cf9e3.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72107d8e9f9714e14294ce5b1e.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e721c509800a27f930897695411.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72200933b59714dd461e9235cc.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72252a117797141140a425e57a.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e722bfa7378a27feb1d8d8f5aa6.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e723709df41a23caf4099d94b3d.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e723a9ec5caa27fd915656693e8.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e726ed7270597147da519f648d9.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e7272a39857971467649e0e443e.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e7277536448a27f05b0b2cdb8f3.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e727ca05b999714c56e5c2e37d9.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72a5566a05a23caf3c417e6a20.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72a90baa4f97147b785005d377.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72c9b5c8fba23c079fdea0373a.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e72cec827cca27f63a85a77dfcf.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e73094f37e3a23cc1b90ab0a95e.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e7316b9aaa5a23c3553e876953f.png?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e732b826809a23cbd16ea2c54a1.jpg?width=1000', 'https://img.29cm.co.kr/item/202409/11ef7e735cc0c2a1a23c9fbf6f6dd898.png?width=1000', 'https://img.29cm.co.kr/item/202411/11ef9964857ce9c9b0a78b226ef4c33d.jpg?width=1000', 'https://img.29cm.co.kr/item/202411/11ef996488fe482bba5253be21363003.png?width=1000', 'https://img.29cm.co.kr/item/202411/11ef99648cd62b2fba529b26dd624e36.jpg?width=1000', 'https://img.29cm.co.kr/item/202411/11ef996490621111ba5205471ad9c92c.png?width=1000']
    detail_urls = ['https://img.29cm.co.kr/item/202311/11ee81b9c3625c1983bce79fef4c3d10.jpg', 'https://img.29cm.co.kr/next-product/2022/11/10/5ce0924033c74cfcbc2bbaeac0c3fe9a_20221110095713.jpg?width=1000', 'https://img.29cm.co.kr/next-product/2021/11/25/bd142c81482c4d83bb3d64f69c295e2d_20211125074948.jpg?width=1000', 'https://img.29cm.co.kr/next-product/2021/11/25/e0b4f342cc4c48d8a6a49b42a01f6f92_20211125075032.jpg?width=1000', 'https://img.29cm.co.kr/next-product/2021/11/25/a49abdeb3f4c478eb70784d73f9b3071_20211125075045.jpg?width=1000', 'https://img.29cm.co.kr/next-product/2021/11/25/a4c9975a90b242028274e517442e5504_20211125075054.jpg?width=1000', 'https://img.29cm.co.kr/item/202403/11eee2989aa428a89a76e518e2065c36.jpg?width=1000', 'https://img.29cm.co.kr/next-product/2023/05/19/bf310829c3a14a5b8c5f5ecca72ca99f_20230519142841.jpg?width=1000']


    tagger = DisplayTagCreator()
    result = tagger.get_info_from_details(detail_urls)
  

    print(result)
