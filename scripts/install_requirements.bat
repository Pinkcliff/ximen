@echo off
chcp 65001 >nul
echo ========================================
echo 安装 Python S7 通信依赖库
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
echo 正在安装必要的库...
echo.

:: 安装核心库
echo [1/5] 安装 python-snap7 (S7 通信库)
pip install python-snap7
if errorlevel 1 echo 警告: python-snap7 安装可能失败

echo [2/5] 安装 pyyaml (配置文件支持)
pip install pyyaml
if errorlevel 1 echo 警告: pyyaml 安装可能失败

echo [3/5] 安装 loguru (日志库)
pip install loguru
if errorlevel 1 echo 警告: loguru 安装可能失败

:: 安装可选库
echo [4/5] 安装 numpy (数据处理，可选)
pip install numpy
if errorlevel 1 echo 警告: numpy 安装失败，仍可正常运行

echo [5/5] 安装 pandas (数据分析，可选)
pip install pandas
if errorlevel 1 echo 警告: pandas 安装失败，仍可正常运行

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用说明：
echo 1. 运行 quick_read_encoder.py 快速读取
echo 2. 运行 read_encoder_position.py 完整功能
echo 3. 编辑 encoder_config.yaml 配置参数
echo.
echo 重要提醒：
echo - 请确保 PLC 已启用 PUT/GET 通信
echo - 请根据实际情况修改 DB5 偏移地址
echo - 确认网络连接正常
echo.
pause