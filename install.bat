@echo off
rem 关闭命令回显

echo ===================================================
echo        网络自动切换工具安装程序
echo ===================================================
echo.

rem 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 需要管理员权限来安装此工具。
    echo 请右键点击此脚本，选择"以管理员身份运行"。
    pause
    exit /b 1
)

rem 设置变量
set SCRIPT_DIR=%~dp0
set INSTALL_DIR=%USERPROFILE%\NetworkMonitor
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set PYTHON_SCRIPT=network_monitor.py
set STARTUP_SCRIPT=start_network_monitor.bat

echo 正在检查Python安装...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python未安装！请先安装Python 3.6或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载Python。
    pause
    exit /b 1
)

rem 检查Python版本
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
echo 检测到Python版本: %PYTHON_VERSION%

rem 创建安装目录
echo 正在创建安装目录...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

rem 复制文件
echo 正在复制文件...
copy "%SCRIPT_DIR%%PYTHON_SCRIPT%" "%INSTALL_DIR%\%PYTHON_SCRIPT%" >nul
if %errorlevel% neq 0 (
    echo 复制Python脚本失败！
    pause
    exit /b 1
)

rem 创建启动脚本
echo 正在创建启动脚本...
echo @echo off > "%INSTALL_DIR%\%STARTUP_SCRIPT%"
echo rem 网络自动切换工具启动脚本 >> "%INSTALL_DIR%\%STARTUP_SCRIPT%"
echo powershell -Command "Start-Process python -ArgumentList '%INSTALL_DIR%\%PYTHON_SCRIPT%' -Verb RunAs" >> "%INSTALL_DIR%\%STARTUP_SCRIPT%"

rem 复制启动脚本到启动文件夹
echo 正在设置开机自启动...
copy "%INSTALL_DIR%\%STARTUP_SCRIPT%" "%STARTUP_DIR%\%STARTUP_SCRIPT%" >nul
if %errorlevel% neq 0 (
    echo 设置开机自启动失败！
    pause
    exit /b 1
)

rem 安装必要的Python库
echo 正在安装必要的Python库...
python -m pip install win10toast >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: win10toast库安装失败，通知功能可能受限。
) else (
    echo win10toast库安装成功。
)

echo.
echo ===================================================
echo 安装完成！
echo.
echo 网络监控工具已安装到: %INSTALL_DIR%
echo 并已设置为开机自动启动。
echo.
echo 您可以通过以下方式立即启动网络监控:
echo 1. 重启计算机
echo 2. 手动运行: %INSTALL_DIR%\%STARTUP_SCRIPT%
echo ===================================================
echo.

rem 询问是否立即启动
set /p START_NOW="是否立即启动网络监控? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo 正在启动网络监控...
    start "" "%INSTALL_DIR%\%STARTUP_SCRIPT%"
)

echo.
echo 感谢您使用网络自动切换工具！
pause
