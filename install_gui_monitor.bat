@echo off
chcp 65001 >nul
echo ========================================
echo 点位表监控GUI依赖安装脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/3] 安装核心依赖...
pip install python-snap7 pyyaml pandas openpyxl
echo.

echo [3/3] 安装GUI依赖...
pip install PyQt6 loguru
echo.

echo ========================================
echo ✅ 所有依赖安装完成！
echo ========================================
echo.
echo 运行监控程序：
echo python point_table_monitor_gui.py
echo.
pause
