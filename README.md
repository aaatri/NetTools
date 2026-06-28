<div align="center">

# NetTools v1.7

<img src="main.png" width="256" alt="NetTools">

基于 **pywebview** 的跨平台网络工具桌面应用，集成 Cisco Packet Tracer 远程控制与 AI 配置生成。

</div>

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com)
[![PyWebView](https://img.shields.io/badge/pywebview-6.x-orange.svg)](https://github.com/r0x0r/pywebview)
[![PT](https://img.shields.io/badge/Cisco-Packet%20Tracer%208.x-red.svg)](https://www.netacad.com/courses/packet-tracer)

---

## ✨ 功能特性

### 🛠️ 网络工具箱

| 工具 | 说明 |
|------|------|
| **子网计算** | IPv4 子网掩码、广播地址、可用 IP 范围快速计算 |
| **VLSM 划分** | 可变长子网掩码自动划分，按主机数需求智能分配 |
| **快速查询** | IP/域名一键解析，显示地址类型与反向 DNS |
| **带宽换算** | bps / Kbps / Mbps / Gbps / Tbps 任意互转 |
| **端口扫描** | TCP 端口开放状态检测，自动识别常见服务 |
| **IP 归属** | 查询 IP 地理位置、运营商信息 |
| **Ping 检测** | ICMP 连通性测试，支持自定义发包次数 |
| **DNS 查询** | 域名 A 记录解析 |
| **路由追踪** | TraceRoute 路径追踪，可调最大跳数 |
| **进制转换** | 二 / 八 / 十 / 十六进制相互转换 |

### 🤖 Cisco Packet Tracer 集成

- 📡 **实时拓扑查看** — 读取 PT 网络拓扑，展示设备列表与链路连接
- 🧠 **AI 自动配置** — 通过 OpenAI 兼容 API，根据拓扑结构和需求自动生成完整 IOS 配置
- 💬 **自然语言 → IOS** — 用中文或英文描述需求，AI 直接生成对应的 Cisco IOS 命令
- 📋 **配置模板生成** — 内置 VLAN / OSPF / EIGRP / NAT / ACL 等模板，快速填充生成命令
- 🖥️ **设备管理** — 添加/删除设备、添加链路、查看设备详细信息
- 🔗 **远程控制** — 通过 PT 扩展插件（Socket.IO 桥接）与 Packet Tracer 实时通信

---

## 📁 项目结构

```
NetToolsV2/
├── main.py                  # 程序入口，pywebview 窗口 + JS API
├── main.png                 # 应用图标（侧边栏 & 关于页面）
├── ico.ico                  # 窗口标题栏图标（exe 嵌入）
├── NetTools.spec            # PyInstaller 构建配置
├── config.json              # AI API 配置（自动生成）
├── README.md
│
├── web/                     # 前端文件
│   ├── index.html           # 12 个工具页面
│   ├── style.css            # 浅色主题，自适应样式
│   └── app.js               # 前端交互逻辑 (~31KB)
│
├── tools/                   # Python 后端模块
│   ├── __init__.py
│   ├── subnet.py            # 子网计算 & VLSM
│   ├── bandwidth.py         # 带宽换算
│   ├── portscan.py          # 端口扫描
│   ├── ping.py              # ICMP Ping
│   ├── dns.py               # DNS 查询
│   ├── traceroute.py        # 路由追踪
│   ├── whois.py             # IP 归属
│   ├── query.py             # IP/域名快速查询
│   ├── hexconv.py           # 进制转换
│   ├── pt_bridge.py         # PT 桥接服务器 (aiohttp + Socket.IO)
│   └── pt_tools.py          # IOS 配置模板引擎
│
├── extension/               # Cisco Packet Tracer 插件
│   ├── source/              # JS 源码
│   │   ├── main.js          # 菜单注册
│   │   ├── window.js        # Webview 窗口管理
│   │   ├── devices.js       # 设备类型映射
│   │   ├── modules.js       # 模块类型映射
│   │   ├── links.js         # 线缆类型映射
│   │   ├── runcode.js       # PT 脚本执行器
│   │   ├── userfunctions.js # 60+ PT 操作函数
│   │   └── interface/       # 桥接状态 Web 界面
│   │       ├── index.html
│   │       ├── interface.js
│   │       └── socket.io.min.js
│   └── cisco-pt-mcp.pts     # 编译后的 PT 插件 (~50KB)
│
├── icons/                   # 16 个 SVG 导航图标
└── dist/                    # 编译输出
    └── NetTools/
        ├── NetTools.exe     # 可执行文件 (~10.6MB)
        └── _internal/       # Python 运行时与依赖
```

---

## 🖥️ 环境要求

| 组件 | 版本/说明 |
|------|-----------|
| **Python** | 3.12+ |
| **操作系统** | Windows 10/11（Linux/macOS 可用，但 PT 集成仅限 Windows） |
| **Cisco Packet Tracer** | 8.x（仅 PT 相关功能需要） |
| **Python 依赖** | 见下方安装 |

---

## 📦 安装与运行

### 1. 安装 Python 依赖

```bash
pip install pywebview pydantic pillow aiohttp socketio-engineio simple-websocket
```

### 2. 开发模式运行

```bash
python main.py
```

### 3. 编译为可执行文件

```bash
pip install pyinstaller
pyinstaller --clean NetTools.spec
```

编译产物位于 `dist\NetTools\NetTools.exe`。

---

### 🔌 Cisco Packet Tracer 集成（可选）

<details>
<summary>点击展开详细步骤</summary>

1. 打开 Packet Tracer → **Extensions** → **Manage Extensions**
2. 点击 **Import**，选择 `extension/cisco-pt-mcp.pts`
3. 菜单栏出现 **Extensions** → **Packet Tracer MCP**，点击启动桥接
4. 在 NetTools 中进入 **思科 MCP** 页面，点击 **刷新拓扑** 即可连接

</details>

---

### 🤖 AI 配置功能设置

<details>
<summary>点击展开配置说明</summary>

1. 在 NetTools 中进入 **思科 MCP** 页面
2. 点击 **AI 自动配置** 区域的 **⚙ 设置** 按钮
3. 填入：
   - **API Endpoint** — 如 `https://api.openai.com/v1`
   - **API Key** — 你的 API 密钥
   - **模型** — 如 `gpt-4o`、`deepseek-chat` 等
4. 点击保存，配置将写入 `config.json`

</details>

---

## 🐞 调试

在窗口中按 **F12** 或 **Ctrl+Shift+I** 即可打开 DevTools 控制台。

---

## 🙏 参考项目

### NetToolsV2（当前版本）

| 项目 | 用途 |
|------|------|
| [pywebview](https://github.com/r0x0r/pywebview) | 桌面 GUI 框架（Python + WebView2） |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | Python 打包为独立 exe |
| [aiohttp](https://github.com/aio-libs/aiohttp) | 异步 HTTP 服务器（PT 桥接） |
| [python-socketio](https://github.com/miguelgrinberg/python-socketio) | Socket.IO 服务端（PT 通信） |
| [simple-websocket](https://github.com/miguelgrinberg/simple-websocket) | WebSocket 底层实现 |
| [python-engineio](https://github.com/miguelgrinberg/python-engineio) | Engine.IO 传输层 |
| [Cisco Packet Tracer](https://www.netacad.com/courses/packet-tracer) | 网络模拟器（PT 扩展插件目标平台） |
| [OpenAI API](https://platform.openai.com/docs/api-reference) | AI 配置生成接口（兼容格式） |
| [Material Icons](https://fonts.google.com/icons) | SVG 导航图标参考 |

### NetTools（旧版 PyQt6 + pywebview）

| 项目 | 用途 |
|------|------|
| [pywebview](https://github.com/r0x0r/pywebview) | 桌面 GUI 框架 |
| [PyQt6](https://pypi.org/project/PyQt6/) | Qt GUI 框架（backup 版本 & Worker/QThread） |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | Python 打包为独立 exe |
| [ipinfo.io](https://ipinfo.io) | IP 归属地查询 API |
| [UPX](https://upx.github.io/) | 可执行文件压缩（可选） |
| ping / tracert | 系统命令（ICMP / 路由追踪） |

### CiscoTools（MCP 服务器，上游 fork）

| 项目 | 用途 |
|------|------|
| [cisco-pt-mcp](https://github.com/muhammadbalawal/cisco-pt-mcp) | 上游项目（本 fork 基于 v0.1.6） |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Model Context Protocol 服务端框架 |
| [python-socketio](https://github.com/miguelgrinberg/python-socketio) | PT 桥接实时通信 |
| [aiohttp](https://github.com/aio-libs/aiohttp) | HTTP + WebSocket 服务器 |
| [PyQt6](https://pypi.org/project/PyQt6/) | 独立 GUI 工具（work/gui/） |
| [Cisco Packet Tracer](https://www.netacad.com/courses/packet-tracer) | 目标网络模拟器 |
| [Socket.IO JS](https://socket.io/) | PT 插件侧 WebSocket 客户端 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | 打包 exe |
| [pyautogui](https://github.com/asweigart/pyautogui) | PT 插件自动构建脚本 |
| [pytest](https://github.com/pytest-dev/pytest) | 测试框架 |
| [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | 异步测试支持 |
| [OpenCode API](https://opencode.ai) | AI 模型接口 |
| Codex / Claude Desktop / Cursor / Backboard | 目标 MCP 客户端 |

---

## 🧰 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12 + pywebview 6.x |
| **前端** | HTML5 + CSS3 + JavaScript（原生，无框架） |
| **PT 桥接** | aiohttp + Socket.IO + WebSocket |
| **AI 接口** | OpenAI 兼容 API |
| **打包** | PyInstaller 6.x |
| **窗口** | Windows Edge Chromium（WebView2） |

---

## 📄 许可证

本项目采用 **MIT License** 开源许可。

---

> 🚀 **NetTools v1.7** — 让网络工程师的工具箱更智能、更高效！
