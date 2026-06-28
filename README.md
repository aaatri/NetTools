# NetTools v1.7 — 网络工具箱

基于 pywebview 的跨平台网络工具桌面应用，集成 Cisco Packet Tracer 远程控制与 AI 配置生成。

## 功能特性

### 网络工具
- **子网计算** — IPv4 子网掩码、广播地址、可用 IP 范围计算
- **VLSM 划分** — 可变长子网掩码自动划分，按主机数需求分配
- **快速查询** — IP/域名一键解析，显示地址类型与 Reverse DNS
- **带宽换算** — bps / Kbps / Mbps / Gbps / Tbps 互相转换
- **端口扫描** — TCP 端口开放状态检测，识别常见服务
- **IP 归属** — 查询 IP 地理位置、运营商信息
- **Ping 检测** — ICMP 连通性测试，自定义次数
- **DNS 查询** — 域名 A 记录解析
- **路由追踪** — TraceRoute 路径追踪，自定义最大跳数
- **进制转换** — 二 / 八 / 十 / 十六进制互转

### Cisco Packet Tracer 集成
- **实时拓扑查看** — 读取 PT 网络拓扑，显示设备列表与连接
- **AI 自动配置** — 通过 OpenAI 兼容 API，根据拓扑结构和需求自动生成完整 IOS 配置
- **自然语言 → IOS** — 用自然语言描述需求，AI 直接生成对应的 Cisco IOS 命令
- **配置模板生成** — 内置 VLAN / OSPF / EIGRP / NAT / ACL 等模板，快速填充生成命令
- **设备管理** — 添加/删除设备、添加链路、查看设备信息
- **远程控制** — 通过 PT 扩展插件（Socket.IO 桥接）与 Packet Tracer 通信

## 项目结构

```
NetToolsV2/
├── main.py                  # 程序入口，pywebview 窗口 + JS API
├── NetTools.spec            # PyInstaller 构建配置
├── config.json              # AI API 配置（自动生成）
├── README.md
│
├── web/                     # 前端文件
│   ├── index.html           # HTML 页面结构（12 个工具页面）
│   ├── style.css            # 样式表（浅色主题，自适应）
│   └── app.js               # 前端交互逻辑（~31KB）
│
├── tools/                   # Python 后端模块
│   ├── __init__.py          # 模块导出
│   ├── subnet.py            # 子网计算 & VLSM 划分
│   ├── bandwidth.py         # 带宽单位换算
│   ├── portscan.py          # TCP 端口扫描
│   ├── ping.py              # ICMP Ping
│   ├── dns.py               # DNS A 记录查询
│   ├── traceroute.py        # 路由追踪
│   ├── whois.py             # IP 归属查询
│   ├── query.py             # IP/域名快速查询
│   ├── hexconv.py           # 进制转换
│   ├── pt_bridge.py         # PT 桥接服务器（aiohttp + Socket.IO）
│   └── pt_tools.py          # IOS 配置模板引擎
│
├── extension/               # Cisco Packet Tracer 插件
│   ├── source/              # JS 源码
│   │   ├── main.js          # 菜单注册入口
│   │   ├── window.js        # Webview 窗口管理
│   │   ├── devices.js       # 设备类型映射表
│   │   ├── modules.js       # 模块类型映射表
│   │   ├── links.js         # 线缆类型映射表
│   │   ├── runcode.js       # PT 脚本执行器
│   │   ├── userfunctions.js # 60+ 个 PT 操作函数
│   │   └── interface/       # 桥接状态 Web 界面
│   │       ├── index.html
│   │       ├── interface.js
│   │       └── socket.io.min.js
│   └── cisco-pt-mcp.pts     # 编译后的 PT 插件（~50KB）
│
├── icons/                   # 16 个 SVG 导航图标
└── dist/                    # 编译输出
    └── NetTools/
        ├── NetTools.exe     # 可执行文件（~10.6MB）
        └── _internal/       # Python 运行时与依赖
```

## 环境要求

- **Python**: 3.12+
- **操作系统**: Windows 10/11（Linux/macOS 可用，但 PT 集成仅限 Windows）
- **Cisco Packet Tracer**: 8.x（仅 PT 相关功能需要）
- **依赖**: 见下方安装

## 安装与运行

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

编译产物在 `dist\NetTools\NetTools.exe`。

### 4. Cisco Packet Tracer 集成（可选）

1. 打开 Packet Tracer → **Extensions** → **Manage Extensions**
2. 点击 **Import**，选择 `extension/cisco-pt-mcp.pts`
3. 菜单栏出现 **Extensions** → **Packet Tracer MCP**，点击启动桥接
4. NetTools 中进入 **思科 MCP** 页面，点击 **刷新拓扑** 即可连接

### AI 配置功能配置

1. 在 NetTools 中进入 **思科 MCP** 页面
2. 点击 **AI 自动配置** 区域的 **⚙ 设置** 按钮
3. 填入：
   - **API Endpoint** — 如 `https://api.openai.com/v1`
   - **API Key** — 你的 API 密钥
   - **模型** — 如 `gpt-4o`、`deepseek-chat` 等
4. 点击保存，配置将写入 `config.json`

## 调试

在窗口中按 **F12** 或 **Ctrl+Shift+I** 打开 DevTools 控制台。

## 参考项目

| 项目 | 用途 |
|------|------|
| [pywebview](https://github.com/r0x0r/pywebview) | 桌面 GUI 框架，Python + WebView2 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | Python 打包为独立 exe |
| [aiohttp](https://github.com/aio-libs/aiohttp) | 异步 HTTP 服务器（PT 桥接） |
| [python-socketio](https://github.com/miguelgrinberg/python-socketio) | Socket.IO 服务端（PT 通信） |
| [simple-websocket](https://github.com/miguelgrinberg/simple-websocket) | WebSocket 底层实现 |
| [python-engineio](https://github.com/miguelgrinberg/python-engineio) | Engine.IO 传输层 |
| [Cisco Packet Tracer](https://www.netacad.com/courses/packet-tracer) | 网络模拟器，PT 扩展插件目标平台 |
| [OpenAI API](https://platform.openai.com/docs/api-reference) | AI 配置生成接口（兼容格式） |
| [Material Icons](https://fonts.google.com/icons) | SVG 导航图标参考 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + pywebview 6.x |
| 前端 | HTML5 + CSS3 + JavaScript（原生，无框架） |
| PT 桥接 | aiohttp + Socket.IO + WebSocket |
| AI 接口 | OpenAI 兼容 API |
| 打包 | PyInstaller 6.x |
| 窗口 | Windows Edge Chromium（WebView2） |

## 许可证

MIT License
