@echo off
:: 启动网络监控脚本
powershell -Command "Start-Process python -ArgumentList '%~dp0network_monitor.py' -Verb RunAs"