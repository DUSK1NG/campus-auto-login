# Windows 免安装版

1. 将整个 ZIP 解压到固定目录，不要直接在压缩包内运行。
2. 双击 `configure.cmd`，填写 `.env`，设置 `CAMPUS_ADAPTER=ecjtu`，填写账号和密码。
3. `CAMPUS_ISP_SUFFIX`：移动填 `@cmcc`，电信填 `@telecom`，联通填 `@unicom`。账号建议只填学号，不带运营商后缀。
4. 双击 `campus-auto-login.exe`，程序后台运行，无控制台窗口。查看 `logs/campus.log` 中的 `INTERNET_OK` 确认联网。
5. 双击 `install-startup.cmd` 安装当前用户自启动，下次登录 Windows 自动运行；无需管理员权限。这不是登录前运行的系统服务。

取消自启动：双击 `remove-startup.cmd`。它不会停止当前已经运行的程序；要停止程序，在任务管理器结束 `campus-auto-login.exe`。请勿反复双击启动，以免多份程序同时认证。

安装自启动后不要移动目录；需要移动时，先在旧目录取消自启动，再在新目录安装。此包不携带任何真实账号密码。

移动账号已有有线和 Wi-Fi 实测。电信和联通选项来自学校实际页面，字段组合测试已覆盖，但尚无对应账号的真实认证验证。多网卡和 TUN 会影响默认路由，排查时关闭 TUN 并只保留待验证的校园网连接。
