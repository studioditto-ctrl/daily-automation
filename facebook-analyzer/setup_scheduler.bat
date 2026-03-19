@echo off
REM Facebook Analyzer - Windows 작업 스케줄러 등록 스크립트
REM 관리자 권한으로 실행해야 합니다.
REM 더블클릭 또는 관리자 cmd에서: setup_scheduler.bat

echo [Facebook Analyzer] Windows 작업 스케줄러 등록 중...

REM Python 경로 자동 감지
for /f "delims=" %%i in ('where python') do (
    set PYTHON_PATH=%%i
    goto :found
)
:found

echo Python 경로: %PYTHON_PATH%
echo 스크립트 경로: %~dp0main.py

REM 기존 작업 삭제 (있으면)
schtasks /delete /tn "FacebookAnalyzerDaily" /f >nul 2>&1

REM 새 작업 등록 (매일 오전 9시, 현재 사용자 계정으로 실행)
schtasks /create ^
  /tn "FacebookAnalyzerDaily" ^
  /tr "\"%PYTHON_PATH%\" \"%~dp0main.py\" --daily" ^
  /sc DAILY ^
  /st 09:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %errorlevel% == 0 (
    echo.
    echo [성공] 작업 스케줄러 등록 완료!
    echo        매일 오전 9시에 자동으로 --daily 가 실행됩니다.
    echo.
    echo 등록된 작업 확인:
    schtasks /query /tn "FacebookAnalyzerDaily" /fo LIST
) else (
    echo.
    echo [오류] 등록 실패. 관리자 권한으로 실행했는지 확인하세요.
)

pause
