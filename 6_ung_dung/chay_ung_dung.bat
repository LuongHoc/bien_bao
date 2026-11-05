@echo off
chcp 65001 >nul
cd /d %~dp0
python -c "import flask, onnxruntime, cv2" 2>nul || python -m pip install -r requirements.txt
python app.py
pause
