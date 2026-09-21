@echo off
rem 손글씨 인식 앱 실행기
rem 파일 탐색기에서 이 파일을 더블클릭하면 앱이 실행됩니다.
rem pythonw.exe 로 띄우므로 검은 콘솔 창이 남지 않습니다.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" goto NOVENV
if not exist "mnist_cnn.pt" goto NOWEIGHT
start "" ".venv\Scripts\pythonw.exe" "app.py"
exit /b 0

:NOVENV
echo [오류] 가상환경 .venv 를 찾을 수 없습니다.
echo 터미널에서 아래 명령으로 먼저 환경을 만들어 주세요.
echo     python -m venv .venv
echo     .venv\Scripts\pip install -r requirements.txt
pause
exit /b 1

:NOWEIGHT
echo [오류] 학습된 가중치 mnist_cnn.pt 가 없습니다.
echo 터미널에서 아래 명령으로 먼저 학습해 주세요.
echo     .venv\Scripts\python train.py
pause
exit /b 1
