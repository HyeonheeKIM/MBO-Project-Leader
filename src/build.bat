@echo off
chcp 65001 >nul
echo ============================================
echo   MBO Project Leader - EXE 빌드 스크립트
echo ============================================
echo.

:: Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

:: PyInstaller 설치 확인 및 설치
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [설치] PyInstaller를 설치합니다...
    pip install pyinstaller
    echo.
)

:: 빌드 디렉토리 정리
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [빌드] EXE 파일을 생성합니다...
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "MBO_Project_Leader" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    --add-data "app_history.md;." ^
    --hidden-import "tkinter" ^
    --hidden-import "sqlite3" ^
    Project_Leader.py

if errorlevel 1 (
    echo.
    echo [오류] 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   빌드 완료!
echo   실행 파일: dist\MBO_Project_Leader.exe
echo ============================================
echo.
echo 이 EXE 파일을 사용자에게 배포하세요.
echo DB 파일은 EXE와 같은 폴더에 자동 생성됩니다.
echo.
pause
