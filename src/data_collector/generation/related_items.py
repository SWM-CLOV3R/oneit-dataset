from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from secret import GPT_API_KEY
import numpy as np

class MeasureSimilarity:
    def __init__(self):
        self.client = OpenAI(api_key=GPT_API_KEY)

def get_embedding(self, text, model="text-embedding-3-large"):
   text = text.replace("\n", " ")
   return self.client.embeddings.create(input = [text], model=model).data[0].embedding

def get_similar_items(self, total_item_lst, product_url, product_tags):
    tot_score = dict()

    product_embedding = get_embedding(product_tags)

    for i in range(len(total_item_lst)):
        compared_url, compared_tags = total_item_lst[i][0], total_item_lst[i][1]
        if compared_url == product_url: continue

        compared_embedding = get_embedding(compared_tags)

        score = cosine_similarity(np.array(product_embedding).reshape(1, -1),np.array(compared_embedding).reshape(1, -1))
        tot_score[compared_url] = score[0][0]
    
    sorted_dict = dict(sorted(tot_score.items(), key=lambda item: item[1], reverse=True)[:10])
    sorted_dict = {key: value for key, value in sorted_dict.items() if value >= 0.6}
    return sorted_dict
