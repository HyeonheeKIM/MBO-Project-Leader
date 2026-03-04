@echo off
chcp 65001 >nul
echo ============================================
echo   MBO Project Leader - 배포 스크립트
echo ============================================
echo.

:: Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

:: Project_Leader.py에서 __version__ 읽기
for /f "tokens=2 delims='= " %%A in ('python -c "exec(open('Project_Leader.py','r',encoding='utf-8').read().split('import')[0]); print(__version__)"') do set "VERSION=%%~A"
if "%VERSION%"=="" (
    echo [오류] Project_Leader.py에서 버전을 읽을 수 없습니다.
    pause
    exit /b 1
)
echo [정보] 현재 버전: v%VERSION%
echo.

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

echo [빌드] EXE 파일을 생성합니다 (v%VERSION%)...
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

:: 버전이 포함된 파일명으로 복사
set "VERSIONED_NAME=MBO_Project_Leader_v%VERSION%.exe"
copy "dist\MBO_Project_Leader.exe" "dist\%VERSIONED_NAME%" >nul

echo.
echo ============================================
echo   배포 빌드 완료! (v%VERSION%)
echo ============================================
echo.
echo   dist\MBO_Project_Leader.exe
echo   dist\%VERSIONED_NAME%
echo.
echo GitHub Releases에 %VERSIONED_NAME% 파일을
echo 업로드하면 자동 업데이트가 동작합니다.
echo.
pause
