# Windows 校园网自动认证框架

已实现网络检测、华东交通大学 Adapter、认证状态机、退避重试、凭据配置和轮转日志。**默认只检测网络；在 .env 设置 CAMPUS_ADAPTER=ecjtu 才启用认证。** 2026-09-12 已完成真实有线认证验证，用户随后确认有线及 Wi-Fi 手动运行均成功。其他学校及运营商仍需单独适配验证。

## 运行

需要 Python 3.11+。在 PowerShell 中执行：

```powershell
git clone https://github.com/DUSK1NG/campus-auto-login.git
cd campus-auto-login
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe -m src.main --once --check-only
.\.venv\Scripts\python.exe -m src.main
```

如果已经有 `.env`，不要再次复制覆盖。填写 `CAMPUS_USERNAME`、`CAMPUS_PASSWORD`，特殊字符用 dotenv 支持的引号包围。环境变量优先于 `.env`。配置在启动时读取，修改后重启。凭据不进入源码或命令行，`.env` 是本地明文文件，仅放在自己的用户目录中。

华东交通大学中国移动账号配置如下（请在本机填写实际值，不要发送密码）：

```dotenv
CAMPUS_ADAPTER=ecjtu
CAMPUS_ISP_SUFFIX=@cmcc
CAMPUS_USERNAME=
CAMPUS_PASSWORD=
CHECK_INTERVAL=30
```

账号可不带 `@cmcc`，程序自动补齐；已带同一后缀不会重复添加。配置完成后用 `python -m src.main --once` 执行一次检测及必要认证，确认后再持续运行。`--check-only` 无论 .env 如何配置都不会认证。

`--once` 只执行一次检测周期；退出码 0 表示周期完成，不代表 Internet 可用，具体状态看日志。持续运行时 Ctrl+C 退出。日志位置为项目 `logs/campus.log`，每个文件约 1 MB，保留 3 个备份。业务层不记录响应正文、请求 URL 或异常原文；日志过滤器另对原始及 URL 编码凭据脱敏。

## 模块

| 文件 | 职责 |
|---|---|
| `src/network.py` | Windows 活动接口和多 HTTP 探针检测 |
| `src/portal.py` | Adapter 抽象接口及禁止认证的默认实现 |
| `src/ecjtu.py` | 学校环境核对、POST 表单、可信响应跳转识别 |
| `src/controller.py` | 状态转换、认证后验证、重试计时 |
| `src/config.py` | 固定应用目录的 .env 配置 |
| `src/logger.py` | 轮转日志及脱敏 |
| `src/main.py`、`run.py` | 命令行和打包入口 |

网络状态包括 `NO_NETWORK`、`LAN_ONLY`、`PORTAL_REQUIRED`、`INTERNET_OK`。状态机另有 `AUTHENTICATING`、`AUTH_SUCCESS`、`AUTH_FAILED`。保留 `LAN_ONLY`，避免把局域网故障误判为需要登录。

每轮先检查 Internet；成功立即跳过认证。无活动接口时等待连接。有局域网但无 Internet 时，只有 `adapter.matches()` 明确确认学校环境后才可登录。未知重定向只是疑似 Portal，不能作为凭据提交地址。学校接口返回已知格式的 302 时只记录“结果待验证”，Internet 复查通过后才进入 `AUTH_SUCCESS` 和 `INTERNET_OK`。

认证失败后最早在 5、10、30、60 秒重试，后续封顶 60 秒；等待期间仍可检测网络。恢复 Internet 后重置失败次数。错误密码也执行退避，请及时修正配置，避免持续失败。缺少凭据不会发认证请求。默认检测间隔 30 秒，可用 `CHECK_INTERVAL` 设置为 5–3600 秒。

## 检测边界

不使用 ping。Windows 通过 `GetAdaptersAddresses` 检测活动非回环接口及地址；API 不可用时降级为本机地址检查。虚拟网卡也可能算活动接口，因此 `NO_NETWORK` 是本地证据判断，无法证明所有物理网络状况。

HTTP 探针严格比对预期正文或 204，禁止跟随重定向；任一有效 Internet 探针优先于之前的疑似 Portal 结果。探针失败可能来自 DNS、代理、出口策略或服务故障，不能据此断定一定需要认证。探针禁用环境代理，HTTPS 保持证书验证；只允许代理上网的环境可能显示 `LAN_ONLY`。

探针使用专用 `ProbeSession`，禁止 requests 为重定向预先读取正文。注入真实会话时必须使用 `ProbeSession`（可挂载自定义 Adapter）；普通 `requests.Session` 会被拒绝。测试也支持注入 Mock 会话。

连接和读取超时各为 2.5 秒，响应体最多读取 4097 字节，并在读取过程中检查 6 秒预算。**requests 的超时不是严格的总时限**：系统 DNS、连接多个 IP、响应头慢速传输等可能超过预算。当前以串行有界响应读取降低一般网络故障的等待，不承诺操作系统级硬截止时间。

## 学校协议和待验证项

已知请求是固定地址 `http://172.16.2.100:801/eportal/` 的表单 POST。程序独立构造抓包中的查询和表单字段，不导入浏览器 Cookie、旧会话或抓包 IP。该已知接口使用 HTTP，表单凭据会在校园网络中明文传输；目前没有证据支持另一个 HTTPS 端点。程序不会关闭 TLS 验证。

优先接受学校主机的 `/a70.htm` 重定向、匹配的 `wlanacname` 和有效 IP，并核对 Portal IP 与本机到认证服务器的路由源地址。外网探针没有给出 Portal URL 或返回 MSN 地址时，直接只读请求用户指定的 `http://172.16.2.100/a70.htm`，动态构造当前 IP、AC 名称等参数；不会访问 MSN 或依赖学校根目录。只有标题、同源脚本和已知登录模板标记同时匹配时才允许认证。页面含动态内容，不使用整页哈希作为认证条件。注销页、未知页面或不可用时不认证。读取页面期间及提交凭据前均复核 IP。HTTP 页面标识只是环境核对，无法提供 TLS 服务器身份保证。

已提供的 `/2.htm` 跳转及 `RetCode=512` 没有确切业务语义，程序不将它硬编码为成功或密码错误。仅对可信跳转触发 Internet 复查；验证失败按退避重试并给出可能原因。错误码精细分类、其他运营商、不同登录入口或 NAT/VPN 环境仍需真实信息（TODO）。若失败，不要连续手动运行，先检查日志和配置。

## 扩展其他学校 Adapter

1. 根据真实抓包确认登录端点、字段、token/challenge、Cookie、成功/失败语义及必要预请求。
2. 在 `portal.py` 或独立学校模块实现 `PortalAdapter`，在 `main.py` 替换 `UnconfiguredPortalAdapter`。
3. `matches()` 验证明确的学校标识和配置端点；不要对探针提供的任意 URL 提交凭据。
4. `authenticate()` 返回 `AuthResult`；错误密码返回 `INVALID_CREDENTIALS`，服务不可用返回 `SERVER_UNAVAILABLE`。所有请求设超时、关闭自动重定向、验证 HTTPS 证书、不输出敏感负载。
5. 新增抓包响应对应的 mock 测试，再用本人授权账号验证真实环境。

本阶段不猜测认证接口，不实现验证码绕过、密码爆破、扫描或访问控制绕过。

## 测试

若已进入 AUTHENTICATING 但始终无法联网，查看 `AUTH_DIAG response` 的 HTTP、RetCode、ACLogOut。程序只记录这些数字码及 ErrorMsg 是否存在，不输出完整跳转、会话或错误正文。未知返回码不自动解释成密码错误。

排查无法重连时，查看 `logs/campus.log` 中的 `PROBE_DIAG` 和 `PORTAL_DIAG`。后者会区分入口超时、入口连接失败、注销页、页面结构不匹配和 IP 不一致；不会输出响应正文或凭据。断网状态运行一次并复制输出后，可以手动恢复联网再发送日志。

```powershell
cd 'C:\Users\Q1573\Documents\Codex\2026-09-11\python-windows-1-2-wi-fi-2\outputs\campus-auto-login'
.\.venv\Scripts\python.exe -m pytest -q
```

单元测试使用 mock，不要求校园网、不读取真实账号、不发送真实认证请求。覆盖正常联网、无网络、Portal 重定向、认证成功、密码错误、超时、服务不可用、认证过程中断网和退避。

## Windows 后台自启动

尚未创建系统任务。学校 Adapter 验证后，可在 Windows“任务计划程序”创建当前用户任务：

- 触发器：当前用户登录时（开机登录后自动运行）。
- 程序：项目绝对路径下 `.venv\Scripts\pythonw.exe`。
- 参数：双引号包围的 `run.py` 绝对路径。
- 起始于：项目绝对目录。
- 多实例策略：不启动新实例；取消“运行超过指定时间就停止”。
- 不要求管理员权限；通过“结束”该任务停止后台程序，删除任务取消自启动。

配置文件和日志由程序按项目位置定位，不受任务工作目录影响。请勿同时手动启动另一实例；本阶段没有跨进程单实例锁。若需要未登录桌面就运行，需单独配置“启动时”触发器及合适的运行账号，验证该账号的网络与文件访问权限；本阶段未设置或验证此模式。

## 后续打包单独 exe

预留 `run.py` 和 frozen 应用目录解析。后续可在单独构建环境安装 PyInstaller 后使用：

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --name campus-auto-login run.py
```

这是后续构建示例，本阶段未打包验证。将 `.env` 放在 exe 同目录，日志写入该目录的 `logs/`，目录需可写。不要把 `.env` 打进 exe，也不要在受保护的 Program Files 目录直接运行此布局。

## 下一步收集信息

浏览器 F12 → Network → Preserve log，正常登录一次，找到真正提交账号认证的请求。提供：

- Request URL（保留字段名，脱敏查询参数中的账号、IP/MAC、token）。
- HTTP Method、Content-Type、必要 Headers（Origin、Referer 等）。
- Query Parameters、Form Data 或 JSON Request Body 的字段结构。
- HTTP 状态码和成功 Response；已有的失败响应也可提供，不要专门反复输入错误密码。
- 认证前是否先请求 challenge/token、依赖 Cookie、跳转、选择运营商或账号后缀；如有，提供相关请求顺序。
- 或提供脱敏后的 Copy as cURL。

把账号、密码、Cookie、Authorization、token、session 等值替换为 `<REDACTED>`。保留字段名、编码形式和响应结构，不提供真实密码；真实凭据只保留在本机 `.env`。
# 2026-09-12 现场验证补充

通过单独绑定校园有线网卡的诊断请求，实测认证前为 `portal_required`，提交一次认证后为 `internet_ok`，学校 `/errcode` 返回 `no errcode`。这次验证未改系统路由，没有借用 WLAN 的联网结果。

已修正两个识别问题：支持学校实际返回的 `a79.htm` 入口；同源认证结果跳转不再限定为 `2.htm`，收到响应后交由 Internet 探针验证，仍不跟随结果跳转，也不直接视为登录成功。外部主机、异常端口及带用户信息的跳转仍拒绝。

回归测试 106 项通过。用户随后手动运行最新版，确认有线及 Wi-Fi 均能成功登录。多网卡同时连接时，常规程序检查的是默认路由联网状态；TUN 接管路由可能影响校园门户访问。
