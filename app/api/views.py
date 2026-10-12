from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/api", tags=["Database Views (W05)"])


# 1. Sidebar 子選單 API：完全吻合作業 /api/subclass/pcid/{id}
@router.get("/subclass/pcid/{id}")
def get_subclasses(id: int, db: Session = Depends(get_db)):
  query = text(
      "SELECT pcid, parent_name, cid, child_name FROM vd_subclass WHERE pcid ="
      " :pcid"
  )
  result = db.execute(query, {"pcid": id}).fetchall()
  return [dict(row._mapping) for row in result]


# 2. 點選鄉鎮市區 (cid)，取得景點列表
@router.get("/objectlist/{cid}")
def get_object_list(cid: int, db: Session = Depends(get_db)):
  query = text("SELECT * FROM vd_objectlist WHERE cid = :cid")
  result = db.execute(query, {"cid": cid}).fetchall()
  return [dict(row._mapping) for row in result]


# 3. 取得景點詳細資訊 (oid)
@router.get("/object/{oid}")
def get_object_detail(oid: int, db: Session = Depends(get_db)):
  query = text("SELECT * FROM vd_object WHERE oid = :oid")
  result = db.execute(query, {"oid": oid}).fetchone()
  if not result:
    raise HTTPException(status_code=404, detail=f"找不到 ID 為 {oid} 的景點")
  return dict(result._mapping)