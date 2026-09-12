# Windows 使用教程

1. 将整个 ZIP 解压到固定目录，不要直接在压缩包内运行。
2. 双击 `configure.cmd`，填写学号和密码，将 `CAMPUS_ADAPTER` 改为 `ecjtu`。
3. 设置 `CAMPUS_ISP_SUFFIX`：移动 `@cmcc`、电信 `@telecom`、联通 `@unicom`。账号建议只填学号。
4. 保存配置，双击 `campus-auto-login.exe`。程序后台运行，不弹出窗口。
5. 双击 `install-startup.cmd`，下次登录 Windows 自动启动，无需管理员权限。

查看 `logs/campus.log`，出现 `INTERNET_OK` 表示已经联网。

取消自启动用 `remove-startup.cmd`；退出当前程序需在任务管理器结束 `campus-auto-login.exe`。不要反复双击启动。

修改配置后请重启程序。安装自启动后不要移动目录；需要移动时，先在旧目录取消自启动，再在新目录安装。

无法登录时，检查账号、密码及运营商后缀；若开启了代理软件的 TUN 模式，先关闭后重试。
