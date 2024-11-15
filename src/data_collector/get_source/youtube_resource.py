import sys
import os
from time import gmtime, strftime, sleep

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir)))
from base_resource import ContentResource

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from preprocess import extract_urls, check_url, get_final_url


class YoutubeResource(ContentResource):
    def get_resource_info(self, searchQ, maxCount, order='relevance'):
        youtube = build('youtube', 'v3', developerKey=self.ytb_key)
        
        # 검색 키워드로 search한 결과 최신순으로 받아오기
        search_response = youtube.search().list(
            order = order,
            part = 'snippet',
            type='video',
            q = searchQ,
            maxResults = maxCount,
        ).execute()

        video_lst_dict = dict()
        for i in range(0, len(search_response['items'])):
            video_id = (search_response['items'][i]['id']['videoId'])
            video_info = youtube.videos().list(
                part='snippet, statistics, topicDetails, contentDetails, player',
                id=video_id,
            ).execute()

            videoViewcount = video_info['items'][0]['statistics'].get('viewCount')
            if order == 'relevance':
                if order == 'relevance':
                    if int(videoViewcount) < 10000 or videoViewcount is None: continue
                    
            is_live = video_info['items'][0]['snippet'].get('liveBroadcastContent')
            if is_live != 'none': continue

            video_type = video_info['items'][0]['contentDetails'].get('duration')
            if len(video_type) == 5: continue

            video_description = video_info['items'][0]['snippet'].get('description')
            if video_description == '' or video_description == 'none': continue
            
            video_lst_dict[video_id] = video_info

        return video_lst_dict
    
    def parse_resource_info(self, video_info):
        video_id = video_info['items'][0]['id']
        published_at = video_info['items'][0]['snippet'].get('publishedAt') # 나중엔 ~~일 이전의 데이터는 제거
        video_title = video_info['items'][0]['snippet'].get('title')
        video_description = video_info['items'][0]['snippet'].get('description') # None? 처리
        channel_title = video_info['items'][0]['snippet'].get('channelTitle') 
        video_tags =  video_info['items'][0]['snippet'].get('tags') # None? 처리
        video_viewcount = video_info['items'][0]['statistics'].get('viewCount') if video_info['items'][0]['statistics'].get('viewCount') else '0'

        if video_tags=='none' : video_tags = []

        return dict(
                    video_id=video_id,
                    published_at=published_at,
                    video_title=video_title,
                    video_description=video_description,
                    channel_title=channel_title,
                    video_tags=video_tags,
                    video_viewcount=video_viewcount
                )
    
    def get_product_url(self, parsed_vinfo_dict):
        result = []
        video_id =  parsed_vinfo_dict['video_id']
        video_description = parsed_vinfo_dict['video_description']

        urls = extract_urls(video_description)
        for url in urls:            
            # 유효하지 않은 url 확인                
            if not check_url(url): continue

            # short url인 경우를 대비하여 최종 url 받아오기
            url = get_final_url(url)
            cut_idx = url.find('?')
            if cut_idx != -1:
                url = url[:cut_idx]

            if any(word in url for word in self.product_keyword): result.append(url)
            elif any(word in url for word in self.brand_keyword): result.append(url)
        
        return result
    

