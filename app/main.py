import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel

# 1. 讀取 .env 設定檔與資料庫連線字串
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="My Backend API")


# --- 你原本寫好的商品模型與 API ---
class Item(BaseModel):
  name: str
  price: float


@app.get("/health")
def health_check():
  return {"status": "ok"}


@app.get("/version")
def get_version():
  return {"version": "0.1.0"}


@app.post("/items")
def create_item(item: Item):
  return item


# --- 本週新增：查詢筆記端點 ---
@app.get("/notes/{note_id}")
def get_note(note_id: int):
  try:
    # 建立 PostgreSQL 連線，dict_row 能直接將資料庫欄位轉成 JSON 格式回傳
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
      with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, content, created_at FROM notes WHERE id = %s",
            (note_id,),
        )
        note = cur.fetchone()

        # 若查無此 ID，回傳 404
        if not note:
          raise HTTPException(
              status_code=404, detail=f"找不到 ID 為 {note_id} 的筆記"
          )

        return {"status": "success", "data": note}

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"資料庫查詢錯誤: {str(e)}")