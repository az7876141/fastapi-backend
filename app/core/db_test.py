import os
from dotenv import load_dotenv
import psycopg

# 讀取 .env 檔案裡面的 DATABASE_URL
load_dotenv()

def test_connection():
    try:
        conn = psycopg.connect(os.getenv("DATABASE_URL"))
        print("連線成功:", conn.info.dbname)
        conn.close()
    except Exception as e:
        print("連線失敗，錯誤原因:", e)

if __name__ == "__main__":
    test_connection()