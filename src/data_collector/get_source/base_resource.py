import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(src_dir)

from secret import *

class ContentResource:
    def __init__(self):
        self.type = None
        self.content  = None # ??
        self.ytb_key = YOUTUBE_API_KEY
        self.product_keyword = ['product', 'gift', 'goods', 'catalog', 'promotion', 'item']
        self.brand_keyword = ['29cm', 'kko.to', 'musinsa', 'gift.kakao.com']
        # self.brand_keyword = ['29cm', 'oliveyoung', 'wconcept', 'kko.to', 'musinsa', 'gift.kakao.com', 'sivillage', 'smartstore', 'makers.kakao', 'kurly', 'nike', 'coupang']
    
    def get_resource_info(self, searchQ, maxCount, order='relevance'):
        raise NotImplementedError('...')
    
    def parse_resource_info(self):
        raise NotImplementedError('...')
    
    def get_product_url(self, video_info):
        raise NotImplementedError('...')