import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 引入 W04 的 SQLAlchemy 資料庫連線核心與筆記路由模組
from app.api import notes
from app.core.database import Base, engine

# 1. 讀取 .env 設定檔與資料庫連線字串
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. 自動在 PostgreSQL 建立 notes 資料表（若已存在會自動略過）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="My Backend API & Web App",
    docs_url=None,  # 停用預設的 /docs，改用下方自訂的相對路徑 Swagger UI
    openapi_url="/api/openapi.json",  # 讓 API 規格文件統一在 /api 底下
)

api_router = APIRouter(prefix="/api")

# 取得專案根目錄下的 webui 資料夾絕對路徑
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "webui"

# 掛載靜態資源與首頁
if PUBLIC_DIR.exists():
  app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


@app.get("/")
async def serve_index():
  return FileResponse(PUBLIC_DIR / "index.html")


# --- 基礎健康檢查與版本端點 ---
@app.get("/api/health")
def health_check():
  return {"status": "ok"}


@app.get("/api/version")
def get_version():
  return {"version": "0.1.0"}


# --- 自訂 Swagger UI（支援反向代理相對路徑） ---
@app.get("/api/docs", include_in_schema=False)
def swagger_ui():
  # 使用相對路徑，部署在 /s學號/api/docs 時仍能正確抓到 openapi.json
  return get_swagger_ui_html(
      openapi_url="openapi.json",
      title=app.title + " - Swagger UI",
  )


# --- 掛載路由 ---
# 1. 掛載剛才寫好的 W04 筆記 CRUD 路由 (/api/notes)
app.include_router(notes.router)

# 2. 掛載一般 API 路由
app.include_router(api_router)