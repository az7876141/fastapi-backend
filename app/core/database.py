import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 讀取 .env 中的連線字串
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 如果連線字串開頭是 postgresql://，將它修正為 postgresql+psycopg:// 以適配 psycopg 3
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+psycopg://", 1
  )
  
# 2. 建立 SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# 3. 建立 SessionLocal 類別，供 API 每次請求生產資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. ORM 模型繼承的基底類別
Base = declarative_base()


# 5. 提供給 API 端點使用的依賴注入（Depends）
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()