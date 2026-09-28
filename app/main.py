import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, APIRouter
from fastapi.staticfiles import StaticFiles
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html

# 1. 讀取 .env 設定檔與資料庫連線字串
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(
    title="My Backend API & Web App",
    docs_url=None,                # 使用下方自訂的相對路徑 Swagger UI
    openapi_url="/api/openapi.json"  # 讓 API 規格文件也移到 /api 底下
)
api_router = APIRouter(prefix="/api")
# 取得專案根目錄下的 webui 資料夾絕對路徑
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "webui"


# 掛載靜態資源與首頁
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/version")
def get_version():
    return {"version": "0.1.0"}


@app.get("/api/docs", include_in_schema=False)
def swagger_ui():
    # 使用相對路徑，部署在 /s學號/api/docs 時仍能找到 OpenAPI 規格
    return get_swagger_ui_html(
        openapi_url="openapi.json",
        title=app.title + " - Swagger UI",
    )





app.include_router(api_router)