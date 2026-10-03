from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteResponse

# 建立專屬於筆記的路由器，統一加上前綴 /api/notes
router = APIRouter(prefix="/api/notes", tags=["筆記管理 (Notes CRUD)"])

# 1. 取得所有筆記清單 (Read All)
@router.get("", response_model=List[NoteResponse])
def get_all_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return notes

# 2. 依 ID 取得單筆筆記 (Read One)
@router.get("/{note_id}", response_model=NoteResponse)
def get_note_by_id(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {note_id} 的筆記")
    return note

# 3. 新增一筆筆記 (Create)
@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note_in: NoteCreate, db: Session = Depends(get_db)):
    # 建立 ORM 模型實體
    new_note = Note(title=note_in.title, content=note_in.content)
    db.add(new_note)
    db.commit()      # 寫入資料庫
    db.refresh(new_note)  # 重新整理以取得資料庫自動產生的 id 與 created_at
    return new_note

# 4. 修改筆記 (Update)
@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_in: NoteCreate, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {note_id} 的筆記")
    
    note.title = note_in.title
    note.content = note_in.content
    db.commit()
    db.refresh(note)
    return note

# 5. 刪除筆記 (Delete)
@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {note_id} 的筆記")
    
    db.delete(note)
    db.commit()
    return {"status": "success", "message": f"ID 為 {note_id} 的筆記已成功刪除"}