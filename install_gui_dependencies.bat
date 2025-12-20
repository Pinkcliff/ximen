@echo off
chcp 65001 >nul
echo ========================================
echo 安装 GUI 监控程序依赖库
echo ========================================
echo.

:: 检查 Python 版本
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11.13
    pause
    exit /b 1
)

echo.
echo 正在安装 GUI 监控程序所需依赖...
echo.

:: 安装核心依赖
echo [1/3] 安装 python-snap7 (S7 通信库)
pip install python-snap7
if errorlevel 1 echo 警告: python-snap7 安装可能失败

echo [2/3] 安装 PyQt6 (图形界面库)
pip install PyQt6
if errorlevel 1 echo 警告: PyQt6 安装可能失败

echo [3/3] 安装 pyqtgraph (绘图库)
pip install pyqtgraph
if errorlevel 1 echo 警告: pyqtgraph 安装可能失败

:: 安装可选依赖
echo.
echo 安装可选依赖...
echo [可选] 安装 numpy (数据处理)
pip install numpy
if errorlevel 1 echo 警告: numpy 安装失败，仍可正常运行

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用说明：
echo 1. 运行 encoder_monitor_gui.py 启动 GUI 监控程序
echo 2. 点击 "开始监控" 按钮开始实时监控
echo 3. 实时查看右缸编码器位置和变化曲线
echo.
echo 程序功能：
echo - 实时显示编码器位置 (LCD 数字显示)
echo - 位置变化实时曲线图
echo - 位置变化检测和提醒
echo - 统计信息 (最大值、最小值、平均值等)
echo - 运行时间统计
echo - 可调节读取频率
echo - 历史数据清除
echo - 详细日志记录
echo.
pause