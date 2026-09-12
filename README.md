# 华东交通大学校园网自动登录

连接校园网后自动登录，支持移动、电信、联通，可设置开机后后台运行。

## 下载

在 [下载页面](https://github.com/DUSK1NG/campus-auto-login/releases/latest) 选择 `campus-auto-login-windows.zip`。

将整个压缩包解压到固定目录，无需安装 Python。

## 配置账号

双击 `configure.cmd`，在打开的配置文件中填写：

```dotenv
CAMPUS_ADAPTER=ecjtu
CAMPUS_USERNAME=你的学号
CAMPUS_PASSWORD=你的密码
CAMPUS_ISP_SUFFIX=@cmcc
CHECK_INTERVAL=30
```

按自己的运营商修改后缀：

| 运营商 | CAMPUS_ISP_SUFFIX |
|---|---|
| 中国移动 | `@cmcc` |
| 中国电信 | `@telecom` |
| 中国联通 | `@unicom` |

账号建议只填学号，不带运营商后缀。保存并关闭配置文件。已有 `.env` 不会被配置入口覆盖。

## 启动程序

双击 `campus-auto-login.exe`，程序会在后台运行，不弹出窗口。

连接校园有线网或 Wi-Fi 后，程序会检查联网状态，需要时自动登录。查看 `logs/campus.log`，出现 `INTERNET_OK` 表示已经联网。

请勿重复启动。修改配置后，在任务管理器结束 `campus-auto-login.exe`，再重新打开。

## 设置开机自启动

双击 `install-startup.cmd`。安装成功后，下次登录 Windows 会自动运行，无需管理员权限。

安装后请保留程序目录。需要移动目录时，先取消自启动，移动后再重新安装。

## 取消自启动或退出

- 取消自启动：双击 `remove-startup.cmd`。
- 退出当前程序：在任务管理器结束 `campus-auto-login.exe`。

取消自启动不会结束当前已经运行的程序。

## 无法登录时

确认账号、密码及运营商后缀填写正确，且 `CAMPUS_ADAPTER=ecjtu`。如果开启了代理软件的 TUN 模式，先关闭后重试。

## 从源码运行

已下载 Windows 版的用户无需执行本节。源码运行需要 Python 3.11 或更高版本。

```powershell
git clone https://github.com/DUSK1NG/campus-auto-login.git
cd campus-auto-login
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe -m src.main
```

按上面的账号配置说明填写 `.env`，运行后按 `Ctrl+C` 退出。
