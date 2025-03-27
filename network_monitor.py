#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网络自动切换监控脚本
用于在有线网卡(Killer E2600)和无线网卡之间自动切换
当有线网卡连接不稳定时，自动切换到无线网卡
"""

import os
import time
import socket
import subprocess
import logging
import datetime
import sys
from pathlib import Path
import ctypes

# 配置参数
VPN_INTERFACE = "以太网"  # 有线网卡名称 (Killer E2600)
WIRELESS_INTERFACE = "WLAN"  # 无线网卡名称
TEST_SITES = ["www.google.com", "www.github.com"]  # 测试站点
CHECK_INTERVAL = 30  # 检查间隔(秒)
LOG_FILE = os.path.join(os.path.expanduser("~"), "network_monitor.log")  # 日志文件路径

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 如果没有管理员权限，尝试重新以管理员权限启动
if not is_admin():
    logger = logging.getLogger("NetworkMonitor")
    logger.warning("脚本需要管理员权限才能修改网络设置。尝试以管理员身份重新启动...")
    try:
        import ctypes, sys
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    except Exception as e:
        logger.error(f"无法以管理员身份重新启动: {e}")
        logger.error("请右键点击脚本，选择'以管理员身份运行'")
        input("按Enter键退出...")
        sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="gbk"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("NetworkMonitor")

def show_notification(title, message):
    """显示Windows通知"""
    try:
        # 首先尝试使用简单的MessageBox
        try:
            cmd = f'powershell -command "& {{[System.Reflection.Assembly]::LoadWithPartialName(\'System.Windows.Forms\'); [System.Windows.Forms.MessageBox]::Show(\'{message}\', \'{title}\', \'OK\', \'Information\');}}"'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"已显示通知: {title} - {message}")
            return
        except Exception as e:
            logger.warning(f"无法使用MessageBox显示通知: {e}")
        
        # 如果MessageBox失败，尝试使用win10toast
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
            return
        except ImportError:
            logger.warning("未安装win10toast库，无法显示toast通知")
        
        # 如果以上都失败，尝试使用msvcp140_notify
        try:
            cmd = f'msg * "{title}: {message}"'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"已使用msg命令显示通知")
        except Exception as e:
            logger.warning(f"无法使用msg命令显示通知: {e}")
            
    except Exception as e:
        logger.error(f"显示通知时出错: {e}")
        # 通知失败不影响主要功能，继续执行

def get_interface_index(interface_name):
    """获取网络接口的索引号"""
    try:
        # 使用netsh命令获取接口信息
        cmd = f'netsh interface ipv4 show interfaces'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
        
        if result.returncode != 0:
            logger.error(f"获取接口信息失败: {result.stderr}")
            return None
            
        # 解析输出找到接口索引
        for line in result.stdout.splitlines():
            if interface_name in line:
                # 接口索引通常是第一列
                parts = line.split()
                if len(parts) > 0 and parts[0].isdigit():
                    return int(parts[0])
        
        # 如果找不到精确匹配，尝试部分匹配
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) > 1:  # 确保有足够的部分
                # 检查接口名称是否是部分匹配
                interface_desc = " ".join(parts[1:])  # 接口描述通常从第二列开始
                if interface_name.lower() in interface_desc.lower():
                    if parts[0].isdigit():
                        logger.info(f"找到接口部分匹配: '{interface_desc}' 索引为 {parts[0]}")
                        return int(parts[0])
        
        logger.error(f"找不到接口 '{interface_name}' 的索引")
        return None
    except Exception as e:
        logger.error(f"获取接口索引时出错: {e}")
        return None

def set_interface_metric(interface_name, metric):
    """设置网络接口的跃点数(metric)"""
    try:
        # 首先尝试使用接口名称
        cmd = f'netsh interface ipv4 set interface "{interface_name}" metric={metric}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
        
        if result.returncode != 0:
            # 如果失败，尝试使用接口索引
            index = get_interface_index(interface_name)
            if index is not None:
                cmd = f'netsh interface ipv4 set interface interface={index} metric={metric}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
                
                if result.returncode != 0:
                    logger.error(f"设置接口索引 {index} 的metric值失败: {result.stderr}")
                    return False
                    
                logger.info(f"成功设置接口索引 {index} 的metric值为 {metric}")
                return True
            else:
                logger.error(f"设置接口 '{interface_name}' 的metric值失败，且无法获取接口索引")
                return False
            
        logger.info(f"成功设置接口 '{interface_name}' 的metric值为 {metric}")
        return True
    except Exception as e:
        logger.error(f"设置接口metric值时出错: {e}")
        return False

def ensure_interface_enabled(interface_name):
    """确保网络接口已启用"""
    try:
        # 检查接口状态
        cmd = f'netsh interface show interface name="{interface_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
        
        # 如果按名称查询失败，尝试获取所有接口并进行部分匹配
        if result.returncode != 0:
            logger.warning(f"按名称检查接口 '{interface_name}' 状态失败，尝试部分匹配")
            cmd = f'netsh interface show interface'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
            
            if result.returncode != 0:
                logger.error(f"获取接口列表失败: {result.stderr}")
                return False
                
            # 在所有接口中查找部分匹配
            interface_found = False
            interface_enabled = False
            for line in result.stdout.splitlines():
                if interface_name.lower() in line.lower():
                    interface_found = True
                    if "已启用" in line or "Enabled" in line:
                        logger.info(f"接口 '{interface_name}' 已启用")
                        interface_enabled = True
                    else:
                        # 尝试启用接口
                        index = get_interface_index(interface_name)
                        if index is not None:
                            logger.info(f"正在启用接口索引 {index}")
                            enable_cmd = f'netsh interface set interface interface={index} admin=enabled'
                            enable_result = subprocess.run(enable_cmd, shell=True, capture_output=True, text=True, encoding="gbk")
                            
                            if enable_result.returncode != 0:
                                logger.error(f"启用接口索引 {index} 失败: {enable_result.stderr}")
                                return False
                                
                            # 等待接口启动
                            time.sleep(5)
                            logger.info(f"已成功启用接口索引 {index}")
                            interface_enabled = True
            
            return interface_enabled if interface_found else False
            
        # 检查是否已禁用
        if "已禁用" in result.stdout or "Disabled" in result.stdout:
            logger.info(f"正在启用接口 '{interface_name}'")
            # 尝试使用接口名称启用
            enable_cmd = f'netsh interface set interface "{interface_name}" admin=enabled'
            enable_result = subprocess.run(enable_cmd, shell=True, capture_output=True, text=True, encoding="gbk")
            
            if enable_result.returncode != 0:
                # 如果失败，尝试使用接口索引
                index = get_interface_index(interface_name)
                if index is not None:
                    logger.info(f"正在使用索引 {index} 启用接口")
                    enable_cmd = f'netsh interface set interface interface={index} admin=enabled'
                    enable_result = subprocess.run(enable_cmd, shell=True, capture_output=True, text=True, encoding="gbk")
                    
                    if enable_result.returncode != 0:
                        logger.error(f"启用接口索引 {index} 失败: {enable_result.stderr}")
                        return False
                else:
                    logger.error(f"启用接口 '{interface_name}' 失败，且无法获取接口索引")
                    return False
                
            # 等待接口启动
            time.sleep(5)
            logger.info(f"已成功启用接口 '{interface_name}'")
        
        return "已启用" in result.stdout or "Enabled" in result.stdout
    except Exception as e:
        logger.error(f"确保接口启用时出错: {e}")
        return False

def test_connection(interface_name, test_site):
    """测试通过指定接口连接到测试站点"""
    try:
        # 获取接口IP地址
        cmd = f'netsh interface ipv4 show addresses "{interface_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk")
        
        if result.returncode != 0:
            logger.error(f"获取接口 '{interface_name}' 的IP地址失败: {result.stderr}")
            return False
            
        # 从输出中提取IP地址
        ip_address = None
        for line in result.stdout.splitlines():
            if "IP 地址" in line or "IP Address" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    ip_address = parts[1].strip()
                    break
        
        if not ip_address:
            logger.error(f"无法获取接口 '{interface_name}' 的IP地址")
            return False
            
        # 使用特定接口的IP地址进行ping测试
        ping_cmd = f'ping -n 1 -w 3000 -S {ip_address} {test_site}'
        ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True, encoding="gbk")
        
        # 检查ping是否成功
        success = "TTL=" in ping_result.stdout
        if success:
            logger.info(f"通过接口 '{interface_name}' 成功连接到 {test_site}")
        else:
            logger.info(f"通过接口 '{interface_name}' 无法连接到 {test_site}")
        
        return success
    except Exception as e:
        logger.error(f"测试连接时出错: {e}")
        return False

def test_multiple_sites(interface_name):
    """测试通过指定接口连接到多个测试站点"""
    for site in TEST_SITES:
        if test_connection(interface_name, site):
            return True
    return False

def main():
    """主函数"""
    logger.info("网络监控脚本已启动")
    logger.info(f"监控VPN接口: {VPN_INTERFACE} (Killer E2600)")
    logger.info(f"备用无线接口: {WIRELESS_INTERFACE}")
    logger.info(f"测试站点: {', '.join(TEST_SITES)}")
    
    # 检查接口是否存在
    vpn_index = get_interface_index(VPN_INTERFACE)
    wireless_index = get_interface_index(WIRELESS_INTERFACE)
    
    if vpn_index is None:
        logger.error(f"错误: VPN接口 '{VPN_INTERFACE}' 不存在，脚本将退出")
        input("按Enter键退出...")
        return
    
    if wireless_index is None:
        logger.error(f"错误: 无线接口 '{WIRELESS_INTERFACE}' 不存在，脚本将退出")
        input("按Enter键退出...")
        return
    
    logger.info(f"找到VPN接口索引: {vpn_index}")
    logger.info(f"找到无线接口索引: {wireless_index}")
    
    # 记录当前状态
    using_vpn = True  # 默认使用VPN
    
    try:
        while True:
            # 确保有线接口启用
            vpn_enabled = ensure_interface_enabled(VPN_INTERFACE)
            wireless_enabled = ensure_interface_enabled(WIRELESS_INTERFACE)
            
            # 测试VPN连接
            vpn_working = False
            if vpn_enabled:
                vpn_working = test_multiple_sites(VPN_INTERFACE)
            
            # 根据测试结果调整网络优先级
            if vpn_working:
                # VPN正常，确保VPN路由优先级高
                if not using_vpn:
                    set_interface_metric(VPN_INTERFACE, 1)
                    set_interface_metric(WIRELESS_INTERFACE, 10)
                    logger.info("VPN连接恢复正常，切换回VPN路由")
                    show_notification("网络切换", "VPN连接恢复正常，已切换回VPN路由")
                    using_vpn = True
                else:
                    logger.info("VPN连接正常，继续使用VPN路由")
            else:
                # VPN异常，切换到无线网络
                if using_vpn:
                    set_interface_metric(WIRELESS_INTERFACE, 1)
                    set_interface_metric(VPN_INTERFACE, 100)
                    logger.info("VPN连接异常，切换到无线网络")
                    show_notification("网络切换", "VPN连接异常，已切换到无线网络")
                    using_vpn = False
                else:
                    logger.info("VPN连接仍然异常，继续使用无线网络")
            
            # 等待下一次检查
            logger.info(f"等待 {CHECK_INTERVAL} 秒后进行下一次检查...")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("用户中断，脚本退出")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        show_notification("网络监控错误", f"脚本遇到错误: {e}")

if __name__ == "__main__":
    main()
