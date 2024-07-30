import sys
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import datetime 

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)
from src.secret import *

# DB 설정
connection_url = f"mysql+mysqldb://{USER_NAME}:{PASSWORD}@{HOST}:{PORT}/{TEST_DATABASE}"
engine = create_engine(connection_url)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# ORM 모델 정의 -> 형식 맞추기 미완
class Product(Base):
    __tablename__ = 'product'  # 이미 생성된 테이블 이름
    idx = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    brand_name = Column(String(255))
    brand_description = Column(String(255))
    original_price = Column(Integer)
    current_price = Column(Integer)
    discount_rate = Column(Integer)
    mall_name = Column(String(255))
    product_url = Column(String(255)) # TEXT와의 차이 알아보기
    thumbnail_url = Column(String(255))
    gender = Column(String(255))
    category_idx = Column(Integer)
    category_display_name = Column(String(255))
    deleted_at = Column(datetime.date) # None 값 할당 방법 알아보기

products = pd.read_csv("./productInfo/products_raw.csv")
for _, row in products.iterrows():
    product = Product(
        name=row['name'],
        brand_name=row['brand_name'],
        brand_description=row['brand_description'],
        original_price=row['original_price'],
        current_price=row['current_price'],
        discount_rate=row['discount_rate'],
        mall_name=row['mall_name'],
        product_url=row['product_url'],
        thumbnail_url=row['thumbnail_url'],
        gender=row['gender'],
        category_idx=row['category_idx'],
        category_display_name=row['category_display_name'],
        deleted_at=None
    )
    session.add(product)

session.commit()
session.close()

