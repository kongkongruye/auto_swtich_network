# 网络自动切换工具

这是一个用于自动监控和切换网络连接的工具，特别适用于以下场景：
- 同时拥有有线网卡(连接VPN/OpenClash)和无线网卡
- 当VPN连接不稳定时，需要自动切换到无线网络
- 当VPN连接恢复时，自动切换回VPN路由

## 功能特点

- 自动监控VPN连接状态
- 在VPN不稳定时自动切换到备用网络
- 在VPN恢复时自动切换回VPN路由
- 支持开机自启动
- 详细的日志记录
- 状态变化通知

## 系统要求

- Windows 10/11
- Python 3.6+
- 管理员权限（修改网络设置需要）

## 安装方法

### 自动安装

1. 右键点击`install.bat`，选择"以管理员身份运行"
2. 按照屏幕提示完成安装
3. 安装程序会自动设置开机自启动

### 手动安装

1. 确保已安装Python 3.6+
2. 将`network_monitor.py`复制到您选择的目录
3. 修改`start_network_monitor.bat`中的路径指向您的Python脚本
4. 将`start_network_monitor.bat`复制到启动文件夹：
   `C:\Users\[用户名]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
5. 安装win10toast库（可选，用于通知）：`pip install win10toast`

## 配置说明

您可以编辑`network_monitor.py`文件来修改以下配置：

```python
# 配置参数
VPN_INTERFACE = "以太网"  # 有线网卡名称
WIRELESS_INTERFACE = "WLAN"  # 无线网卡名称
TEST_SITES = ["www.google.com", "www.github.com"]  # 测试站点
CHECK_INTERVAL = 30  # 检查间隔(秒)
```

- `VPN_INTERFACE`: 您的有线网卡名称
- `WIRELESS_INTERFACE`: 您的无线网卡名称
- `TEST_SITES`: 用于测试连接的网站列表
- `CHECK_INTERVAL`: 检查网络状态的时间间隔（秒）

## 使用方法

安装完成后，工具会在每次系统启动时自动运行。您也可以：

1. 手动运行`start_network_monitor.bat`来启动监控
2. 查看`%USERPROFILE%\network_monitor.log`文件了解工具的工作状态

## 故障排除

如果遇到问题：

1. 确保以管理员身份运行脚本
2. 检查网卡名称是否正确
3. 查看日志文件了解详细错误信息
4. 尝试手动启用/禁用网络接口测试

## 许可证

MIT License
