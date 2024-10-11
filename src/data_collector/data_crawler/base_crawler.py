from selenium import webdriver
import random
import os

class Crawler:
    def __init__(self, url):
        self.url = url
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless') # 창 띄우지 않기 옵션
        # self.options.add_argument('--no-sandbox') # 샌드박스 모드를 비활성화 -> 호환성 문제 해결 but 보안 기능 비활성화 
        # self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('window-size=1920x1080')
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

    def cookie_maker(self):
        rand_user_folder = random.randrange(1,100)
        userCookieDir = os.path.abspath(f'./cookies/{rand_user_folder}')
        print(userCookieDir)
        if not os.path.exists(userCookieDir):
            print(userCookieDir, '폴더 생성...')
            os.mkdir(userCookieDir)
        self.options.add_argument(f'--user-data-dir-{userCookieDir}')


    def fetch_content(self):
        import time
        driver = webdriver.Chrome(options=self.options)
        driver.get(self.url)
        time.sleep(10)
        content = dict()
        content['page_source']= driver.page_source
        return content
    
    def parse_content(self, content):
        raise NotImplementedError('해당 쇼핑몰에 대한 cralwer가 없습니다.')
    
    def run(self):
        self.cookie_maker()
        content = self.fetch_content()
        if content:
            return self.parse_content(content)
        return None

