import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
import jwt
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "wke-api"
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", 28800))

def create_access_token(member_id: int) -> str:
    """簽發本系統專屬的 JWT 通行證"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(member_id),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_member(
    token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    auth_header: Optional[str] = Header(None, alias="Authorization"),
) -> dict:
    """
    驗證使用者身份的 Dependency（兩階段防護：先驗 JWT 簽名，再查 DB）。
    未登入、過期或查無此人時直接丟出 401 Unauthorized。
    """
    token = None
    # 1. 優先從 HttpOnly Cookie 取出 Token；若無則從 Authorization: Bearer 讀取
    if token_cookie:
        token = token_cookie
    elif auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="尚未登入或認證憑證遺失",
        )

    # 2. 驗證 JWT 簽章、發行者與過期時間
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["sub", "exp", "iss"]},
        )
        member_id = int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效或已過期的認證憑證",
        )

    # 3. 驗簽通過後才連線資料庫確認帳號是否依然存在（防止帳號被停用/刪除後仍持舊 Token 存取）
    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, google_sub, email, name, picture, email_verified FROM public.member WHERE id = %s",
                    (member_id,),
                )
                member = cur.fetchone()
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="會員帳號不存在或已被移除",
                    )
                return member
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"資料庫連線或查詢錯誤: {str(e)}",
        )