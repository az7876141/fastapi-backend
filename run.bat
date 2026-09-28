@echo off
REM 啟動虛擬環境並以 0.0.0.0 (代表所有本機 IP 皆可連入) 與 Port 7777 啟動服務
call .\venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 7777 --reload
pause