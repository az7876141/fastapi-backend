import os
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
import psycopg
from psycopg.rows import dict_row

from app.core.security import create_access_token, get_current_member

router = APIRouter(prefix="/api/auth", tags=["認證管理 (Authentication)"])

# 讀取 OAuth 與轉址環境變數
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "true").lower() == "true"
AUTH_SUCCESS_REDIRECT_URL = os.getenv("AUTH_SUCCESS_REDIRECT_URL", "/")
DATABASE_URL = os.getenv("DATABASE_URL")

# 初始化 Authlib OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/google/login")
async def google_login(request: Request):
    """步驟 1：建立 state 暗號，轉址導向 Google 登入授權頁面"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth 未正確設定",
        )
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def google_callback(request: Request):
    """
    步驟 2：Google 授權完成回呼
    - 比對 session cookie 的 state 防偽暗號
    - 交換 Token 並解析 OIDC 使用者資訊 (sub, email, profile)
    - 在 PostgreSQL 執行 Upsert (第一次 INSERT，後續 UPDATE)
    - 簽發本系統 JWT 並設定至 HttpOnly Cookie
    - 轉址回前端首頁
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"授權失敗: {str(e)}")

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無法取得 Google 使用者資訊")

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    if not google_sub or not email or not email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無效或未驗證的 Google 帳號")

    # 寫入或更新資料庫 member 表（Upsert）
    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.member (google_sub, email, name, picture, email_verified, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (google_sub) DO UPDATE SET
                        email = EXCLUDED.email,
                        name = EXCLUDED.name,
                        picture = EXCLUDED.picture,
                        email_verified = EXCLUDED.email_verified,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id;
                    """,
                    (google_sub, email, name, picture, email_verified),
                )
                member = cur.fetchone()
                member_id = member["id"]
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"資料庫寫入失敗: {str(e)}")

    # 簽發本系統 JWT
    app_jwt = create_access_token(member_id=member_id)

    # 303 Redirect 回前端首頁，並設定安全 HttpOnly Cookie
    response = RedirectResponse(url=AUTH_SUCCESS_REDIRECT_URL, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=app_jwt,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        max_age=int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", 28800)),
    )
    return response

@router.get("/me")
def read_current_member(member: dict = Depends(get_current_member)):
    """提供前端查詢當前登入者資訊（未登入會自動回傳 401）"""
    return {
        "id": member["id"],
        "name": member["name"],
        "email": member["email"],
        "picture": member["picture"],
    }

@router.post("/logout")
def logout(response: Response):
    """安全登出：清除 access_token Cookie"""
    response.delete_cookie(
        key="access_token",
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
    )
    return {"status": "success", "message": "已安全登出"}