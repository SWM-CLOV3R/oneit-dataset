import pandas as pd
from time import gmtime, strftime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from crawling_func.env import YOUTUBE_API

from crawling_func.preprocess import extract_urls, check_url, get_final_url

# 영상에서 정보 뽑아오는 함수
# 스크립트 정보 제외
def get_video(searchQ, maxCount, order="relevance"):
    youtube = build("youtube", "v3", developerKey = YOUTUBE_API)

    # 검색 키워드로 search한 결과 최신순으로 받아오기
    search_response = youtube.search().list(
        order = order,
        part = "snippet",
        type="video",
        q = searchQ,
        maxResults = maxCount,
    ).execute()

    # videoId 리스트 따로 빼서 video 정보를 가져와 보자
    video_ids = []
    for i in range(0, len(search_response["items"])):
        video_ids.append((search_response["items"][i]["id"]["videoId"])) #videoId의 리스트를 만들어 둔다 (videoId로 조회할 수 있게)

    #추출할 정보의 list들과 그 모든 정보를 key-value로 저장할 딕셔너리 변수를 하나 생성한다.
    videoId = []
    pubDates= []
    videoTitle = []
    videoDescription = []
    channelTitle = []
    videoTags = []
    videoLive = []
    videoType = []
    videoViewcount = []
    data_dicts = { }


    for i in range(0, len(search_response["items"])):
        video_info = youtube.videos().list(
            part="snippet, statistics, topicDetails, contentDetails, player",
            id=video_ids[i],
        ).execute()

        temp_videoId = video_info["items"][0]["id"]
        temp_pubDates = video_info["items"][0]["snippet"].get("publishedAt") # 나중엔 ~~일 이전의 데이터는 제거
        temp_videoTitle = video_info["items"][0]["snippet"].get("title")
        temp_videoDescription = video_info["items"][0]["snippet"].get("description") # None? 처리
        if temp_videoDescription == "" or temp_videoDescription == "none" or temp_videoDescription is None: continue
        temp_channelTitle = video_info["items"][0]["snippet"].get("channelTitle") 
        temp_videoTags =  video_info["items"][0]["snippet"].get("tags") # None? 처리
        if temp_videoTags is None or temp_videoTags=="none" : temp_videoTags = []
        temp_videoLive = video_info["items"][0]["snippet"].get("liveBroadcastContent") #"none" 이 아니라면 제외하기
        if temp_videoLive != "none": continue
        temp_videoType = video_info["items"][0]["contentDetails"].get("duration")
        if len(temp_videoType) == 5: continue
        temp_videoViewcount = video_info["items"][0]["statistics"].get("viewCount")
        if temp_videoViewcount is None:
            temp_videoViewcount = "0"

        videoId.append(temp_videoId)
        pubDates.append(temp_pubDates)
        videoTitle.append(temp_videoTitle)
        videoDescription.append(temp_videoDescription)
        channelTitle.append(temp_channelTitle)
        videoTags.append(temp_videoTags)
        videoType.append(temp_videoType)
        videoViewcount.append(temp_videoViewcount)
        
    data_dicts["id"] = videoId
    data_dicts["date"] = pubDates
    data_dicts["title"] = videoTitle
    data_dicts["description"] = videoDescription
    data_dicts["channel"] = channelTitle
    data_dicts["tags"] = videoTags
    data_dicts["type"] = videoType
    data_dicts["view"] = videoViewcount 
    
    return data_dicts

def get_video_by_keys(search_key_lst, maxCount, order="relevance"):
    video_dataset = pd.DataFrame(columns=["searchQ", "id", "date", "title", "description", "channel", "tags", "type", "view"])

    for key in search_key_lst:
        data = get_video(key, maxCount, order)
        df = pd.DataFrame.from_dict(data=data)
        df["searchQ"] = [key] * len(df)
        df = df[["searchQ", "id", "date", "title", "description", "channel", "tags", "type", "view"]]
        video_dataset = pd.concat([video_dataset, df],axis=0)

    video_dataset.reset_index(inplace=True, drop=True)
    video_dataset.drop_duplicates(subset="id", keep="first",inplace=True)
    video_dataset.reset_index(inplace=True,drop=True)
    
    path = "./YoutubeData/youtube_video_" + strftime("%Y-%m-%d_%H:%M", gmtime()) + ".csv"
    video_dataset.to_csv(path)

    print(path, f"\n총 {len(video_dataset)}개의 영상이 수집되었습니다.")
    return video_dataset

def get_product_urls(video_dataset):
    product_url = []
    video_id = []
    product_key = ["product", "gift", "goods", "catalog", "promotion", "item"]
    brand_key = ["29cm", "oliveyoung", "wconcept", "kko.to", "musinsa", "gift.kakao.com", "sivillage", "smartstore", "makers.kakao", "kurly", "nike", "coupang"]

    for i in range(len(video_dataset)):
        content_info = video_dataset.loc[i]
        product_info = content_info["description"]

        urls = extract_urls(product_info)
        for url in urls:            
            # 유효하지 않은 url 확인
            cut_idx = url.find('?')
            if cut_idx != -1:
                url = url[:cut_idx]
            if not check_url(url): continue
            # short url인 경우를 대비하여 최종 url 받아오기
            url = get_final_url(url)
            # 제품에 대한 단어가 있는 경우
            if any(word in url for word in product_key): 
                product_url.append(url)
                video_id.append(video_dataset["id"][i])
            # 브랜드에 대한 단어가 있는 경우
            elif any(word in url for word in brand_key): 
                product_url.append(url)
                video_id.append(video_dataset["id"][i])

    productDF = pd.DataFrame([video_id, product_url]).T
    productDF.columns =["videoID", "productURL"]
    
    path = "./YoutubeData/product_url_"+ strftime("%Y-%m-%d_%H:%M", gmtime()) + ".csv"
    productDF.to_csv(path)

    print(path, f"\n총 {len(productDF)}개의 제품 URL이 수집되었습니다.")