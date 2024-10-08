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
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)')

    def cookie_maker(self):
        rand_user_folder = random.randrange(1,100)
        userCookieDir = os.path.abspath('./cookies/{rand_user_folder}')
        if not os.path.exists(userCookieDir):
            print(userCookieDir, '폴더 생성...')
            os.mkdir(userCookieDir)
        self.options(f'--user-data-dir-{userCookieDir}')


    def fetch_content(self):
        import time
        driver = webdriver.Chrome(options=self.options)
        driver.get(self.url)
        time.sleep(10)
        content = driver.page_source
        return content
    
    def parse_content(self, page_source, response):
        raise NotImplementedError('no sub class')
    
    def run(self):
        self.cookie_maker()
        content = self.fetch_content()
        if content:
            page_source, response = content
            return self.parse_content(page_source, response)
        return None
