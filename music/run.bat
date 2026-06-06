@echo off
setlocal enabledelayedexpansion

set "PYTHON=C:/Users/Administrator/AppData/Local/Programs/Python/Python314/python.exe"
set "SCRIPT=%~dp0run-analysis.py"

if "%~1"=="" (
    echo 请将音频文件拖拽到此图标上，或在此窗口输入文件路径：
    set /p FILE="音频文件路径: "
    set "FILE=!FILE:"=!"
) else (
    set "FILE=%~1"
)

echo.
echo ============================================
echo   音乐分析 -- 正在处理...
echo ============================================
echo.

"%PYTHON%" "%SCRIPT%" "!FILE!"

if !ERRORLEVEL! neq 0 (
    echo.
    echo ============================================
    echo   分析失败！请检查上方错误信息。
    echo ============================================
)

echo.
pause
endlocal
