# 华东交通大学校园网自动连接程序 · Windows 使用教程

1. 将整个 ZIP 解压到固定目录，不要直接在压缩包内运行。
2. 双击 `configure.cmd`，填写学号和密码，将 `CAMPUS_ADAPTER` 改为 `ecjtu`。
3. 设置 `CAMPUS_ISP_SUFFIX`：移动 `@cmcc`、电信 `@telecom`、联通 `@unicom`。账号建议只填学号。
4. 保存配置，双击 `campus-auto-login.exe`。程序后台运行，不弹出窗口。
5. 双击 `install-startup.cmd`，下次登录 Windows 自动启动，无需管理员权限。

查看 `logs/campus.log`，出现 `INTERNET_OK` 表示已经联网。

取消自启动用 `remove-startup.cmd`；退出当前程序需在任务管理器结束 `campus-auto-login.exe`。不要反复双击启动。

修改配置后请重启程序。安装自启动后不要移动目录；需要移动时，先在旧目录取消自启动，再在新目录安装。

无法登录时，检查账号、密码及运营商后缀；若开启了代理软件的 TUN 模式，先关闭后重试。

## 免责声明

本程序为个人开发的非官方工具，与华东交通大学及各运营商无隶属或授权关系。仅用于本人有权使用的校园网账号登录，不提供绕过认证、缴费或网络访问限制的功能，请遵守学校及运营商的网络使用规定。

程序按现状提供，不保证在所有设备或校园网系统更新后持续可用。请妥善保管本机 `.env` 中的账号密码，反馈时不要上传密码或包含个人信息的日志。

## 联系方式

邮箱：[jk1ng@qq.com](mailto:jk1ng@qq.com)

项目：[ecjtu-auto-login](https://github.com/DUSK1NG/ecjtu-auto-login)
