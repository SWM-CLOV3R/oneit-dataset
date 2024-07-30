import sys
import os
import pandas as pd
from sqlalchemy import create_engine

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(src_dir)

from secret import *

connection_message = f"mysql+mysqldb://{USER_NAME}:{PASSWORD}@{HOST}:{PORT}/{TEST_DATABASE}"
engine = create_engine(connection_message)

try:
    connection = engine.connect()
    print("Connected to AWS RDS MySQL database successfully!")
    connection.close()
except Exception as e:
    print(f"Error: {e}")
