@echo off
cd /d %~dp0
python -m pip install -r requirements.txt
echo.
echo Cai dat xong. Vi du chay: python nhan_dang.py --camera 0
pause
