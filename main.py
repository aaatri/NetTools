# -*- coding: utf-8 -*-
"""
NetTools - 主程序入口
使用 pywebview 创建原生窗口，内部加载 HTML 前端
Python 后端通过 js_api 暴露给前端调用
"""
import sys
import os
import json
import urllib.request
import urllib.error
import webview

# 添加当前目录到路径
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# 导入工具模块
from tools.subnet import SubnetCalc
from tools.bandwidth import bw_convert
from tools.portscan import port_scan
from tools.ping import ping
from tools.dns import dns_lookup
from tools.traceroute import traceroute
from tools.whois import whois_ip
from tools.query import quick_query
from tools.hexconv import convert_all
from tools.pt_bridge import get_network, configure_ios, add_device, add_link, remove_device, get_device_info, configure_pc_ip, add_module, set_power, rename_device, move_device, get_status, wait_pt, is_pt_connected, call_pt, send_ios_commands, get_running_config
from tools.pt_tools import generate_from_template, get_template_list
CONFIG_FILE = os.path.join(base_path, "config.json")
import base64


class Api:
    """暴露给前端的 Python API"""

    # ── 子网计算 ──
    def subnet_calc(self, network: str, prefix: int) -> dict:
        return SubnetCalc.calc(network, prefix)

    # ── VLSM ──
    def vlsm(self, network: str, prefix: int, hosts: list) -> list:
        return SubnetCalc.vlsm(network, prefix, hosts)

    # ── 带宽换算 ──
    def bw_convert(self, value: float, frm: str, to: str) -> float:
        return bw_convert(value, frm, to)

    # ── 端口扫描 ──
    def port_scan(self, host: str, ports: list) -> list:
        return port_scan(lambda x: None, host, ports)

    # ── Ping ──
    def ping(self, host: str, count: int) -> dict:
        results, successes, total = ping(lambda x: None, host, count)
        return {
            'results': results,
            'successes': successes,
            'total': total,
            'loss_rate': round((total - successes) / total * 100, 1) if total else 0
        }

    # ── DNS 查询 ──
    def dns_lookup(self, domain: str) -> list:
        return dns_lookup(lambda x: None, domain)

    # ── 路由追踪 ──
    def traceroute(self, host: str) -> list:
        return traceroute(lambda x: None, host)

    # ── IP 归属 ──
    def whois_ip(self, ip: str) -> str:
        return whois_ip(lambda x: None, ip)

    # ── 快速查询 ──
    def quick_query(self, target: str) -> dict:
        return quick_query(lambda x: None, target)

    # ── 进制转换 ─
    def hex_convert(self, value: str, src_base: str) -> dict:
        return convert_all(lambda x: None, value, src_base)

    # ── 思科 MCP ──
    def pt_wait(self, timeout: int = 30) -> dict:
        try:
            wait_pt(timeout)
            return {"success": True}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_status(self) -> dict:
        return get_status()

    def pt_connected(self) -> dict:
        return {"connected": is_pt_connected()}

    def pt_get_network(self) -> dict:
        try:
            result = get_network()
            # PT may return array-like objects instead of real arrays
            if isinstance(result, dict):
                for key in ('devices', 'connections'):
                    val = result.get(key)
                    if val is not None and not isinstance(val, list):
                        if isinstance(val, dict):
                            arr = []
                            for k, v in val.items():
                                if isinstance(k, str) and k.isdigit():
                                    arr.append(v)
                            result[key] = arr
                        elif hasattr(val, '__iter__'):
                            result[key] = list(val)
                        else:
                            result[key] = []
                # Ensure each device has interfaces as array
                for d in result.get('devices', []):
                    if isinstance(d, dict):
                        ifaces = d.get('interfaces')
                        if ifaces is not None and not isinstance(ifaces, list):
                            if isinstance(ifaces, dict):
                                arr = []
                                for k, v in ifaces.items():
                                    if isinstance(k, str) and k.isdigit():
                                        arr.append(v)
                                d['interfaces'] = arr
                            elif hasattr(ifaces, '__iter__'):
                                d['interfaces'] = list(ifaces)
                            else:
                                d['interfaces'] = []
            return result
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_configure_ios(self, device_name: str, commands: str) -> dict:
        try:
            return send_ios_commands(device_name, commands)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_add_device(self, name: str, model: str, x: float, y: float) -> dict:
        try:
            return add_device(name, model, x, y)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_add_link(self, d1: str, i1: str, d2: str, i2: str, link_type: str = "auto") -> dict:
        try:
            return add_link(d1, i1, d2, i2, link_type)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_remove_device(self, names: list) -> dict:
        try:
            return remove_device(names)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_get_device_info(self, name: str) -> dict:
        try:
            return get_device_info(name)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_configure_pc(self, name: str, dhcp: bool = False, ip: str = "", mask: str = "", gateway: str = "", dns: str = "") -> dict:
        try:
            return configure_pc_ip(name, dhcp, ip, mask, gateway, dns)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_add_module(self, name: str, slot: int, model: str) -> dict:
        try:
            return add_module(name, slot, model)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_set_power(self, name: str, on: bool) -> dict:
        try:
            return set_power(name, on)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_rename_device(self, name: str, new_name: str) -> dict:
        try:
            return rename_device(name, new_name)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_get_app_icon(self) -> str:
        try:
            for p in [os.path.join(base_path, "main.png"), os.path.join(base_path, "_internal", "main.png")]:
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        return "data:image/png;base64," + base64.b64encode(f.read()).decode()
            return ""
        except:
            return ""

    def pt_get_templates(self) -> list:
        return get_template_list()

    def pt_generate_config(self, template_key: str, fields: dict) -> dict:
        return generate_from_template(template_key, fields)

    def pt_parse_nl(self, text: str) -> dict:
        try:
            import json, urllib.request, urllib.error
            cfg = self.pt_ai_load_config()
            if not cfg.get("endpoint") or not cfg.get("key"):
                return {"matched": False, "error": "请先在设置中配置 API 端点和密钥"}
            model = cfg.get("model", "gpt-4o")
            api_key = cfg["key"]
            endpoint = cfg["endpoint"].rstrip("/")

            prompt = f"""你是网络工程师。请将以下自然语言需求转换为 Cisco IOS 命令。

需求：{text}

注意：这是 Cisco Packet Tracer 模拟器，不是其他品牌设备。
只使用 Cisco IOS 标准命令（switchport mode trunk 等）。

请严格按照以下 JSON 格式返回（不要有其他文字）：
{{"commands": ["命令1", "命令2", ...]}}

只返回纯 IOS 命令，不要解释。"""

            body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }).encode("utf-8")
            req = urllib.request.Request(f"{endpoint}/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            reply = result["choices"][0]["message"]["content"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1]
                reply = reply.rsplit("```", 1)[0]
            parsed = json.loads(reply.strip())
            return {"matched": True, "commands": parsed.get("commands", [])}
        except json.JSONDecodeError:
            return {"matched": False, "error": "AI 返回格式错误"}
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode()
            except:
                detail = str(e)
            return {"matched": False, "error": f"API 请求失败 ({e.code}): {detail[:200]}"}
        except Exception as e:
            return {"matched": False, "error": str(e)}

    def pt_send_pdu(self, source: str, dest: str) -> dict:
        try:
            return call_pt("sendPdu", sourceDevice=source, destinationDevice=dest)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_step_simulation(self, direction: str = "forward", steps: int = 5) -> dict:
        try:
            return call_pt("stepSimulation", direction=direction, steps=steps)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_get_pdu_results(self, types: list = None) -> dict:
        try:
            if types is None: types = ["ICMP"]
            return call_pt("getPduResults", types=types)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_test_ping(self, source: str, dest: str) -> dict:
        """完整 ping 测试：发 PDU → 步进 → 检查结果 → 重置"""
        try:
            pdu = call_pt("sendPdu", sourceDevice=source, destinationDevice=dest)
            if not isinstance(pdu, dict) or not pdu.get('success'):
                return {"success": False, "error": "发送 PDU 失败", "detail": pdu}
            # 多步进几次确保 PDU 跨多跳传输完成
            step = call_pt("stepSimulation", direction="forward", steps=30)
            results = call_pt("getPduResults", types=["ICMP"])
            call_pt("stepSimulation", direction="reset", steps=0)
            frames = []
            if isinstance(results, dict):
                r = results.get('result') or {}
                if isinstance(r, dict):
                    frames = r.get('frames') or []
            # 只要有 accepted 的 ICMP 帧就认为通
            accepted = False
            status = "unknown"
            for f in frames:
                if isinstance(f, dict) and f.get('status') == 'accepted':
                    accepted = True
                    status = 'accepted'
                    break
            return {"success": True, "accepted": accepted, "status": status, "frame_count": len(frames)}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    def pt_call_tool(self, tool_name: str, args: dict) -> dict:
        try:
            return call_pt(tool_name, **args)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    # ── AI 大模型配置 ──
    def _ai_config_path(self):
        return os.path.join(base_path, 'config.json')

    def ai_get_config(self) -> dict:
        path = self._ai_config_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def ai_save_config(self, cfg: dict) -> bool:
        path = self._ai_config_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True

    def ai_push_config(self, device: str, lines: list, is_pc: bool) -> dict:
        """推送单台设备的配置并返回结果"""
        try:
            cmd_str = '\n'.join(lines)
            if is_pc:
                ip = mask = gateway = dns = ''
                for ln in lines:
                    parts = ln.strip().split()
                    if not parts: continue
                    if parts[0] == 'ip' and len(parts) >= 3:
                        ip, mask = parts[1], parts[2]
                        for i, p in enumerate(parts):
                            if p == 'gateway' and i+1 < len(parts): gateway = parts[i+1]
                            if p == 'dns' and i+1 < len(parts): dns = parts[i+1]
                    if parts[0] == 'dns' and len(parts) >= 2:
                        dns = parts[1]
                    if parts[0] == 'gateway' and len(parts) >= 2:
                        gateway = parts[1]
                if ip and mask:
                    r = configure_pc_ip(device, False, ip, mask, gateway, dns)
                else:
                    r = configure_pc_ip(device, True, '', '', gateway, dns)
                # 重试一次如果失败（PT 端口可能尚未就绪）
                if isinstance(r, dict) and r.get('success') is False and 'functional' in (r.get('message') or r.get('error') or ''):
                    import time; time.sleep(0.5)
                    if ip and mask:
                        r = configure_pc_ip(device, False, ip, mask, gateway, dns)
                    else:
                        r = configure_pc_ip(device, True, '', '', gateway, dns)
            else:
                r = send_ios_commands(device, cmd_str)
            if isinstance(r, dict):
                return {"success": r.get('success') is not False, "message": r.get('message') or r.get('error',''), "commands": cmd_str}
            return {"success": False, "message": str(r), "commands": cmd_str}
        except Exception as e:
            return {"success": False, "message": str(e), "commands": cmd_str}

    def pt_ai_load_config(self) -> dict:
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"endpoint": "", "key": "", "model": "gpt-4o"}
        except:
            return {"endpoint": "", "key": "", "model": "gpt-4o"}

    def pt_ai_save_config(self, data: dict) -> dict:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pt_ai_generate_config(self, requirement: str) -> dict:
        import traceback, json
        try:
            cfg = self.pt_ai_load_config()
            if not cfg.get("endpoint") or not cfg.get("key"):
                return {"error": "请先在设置中配置 API 端点和密钥"}
            model = cfg.get("model", "gpt-4o")
            endpoint = cfg["endpoint"].rstrip("/")
            api_key = cfg["key"]

            net = get_network()
            if not net.get("devices"):
                return {"error": "无法读取拓扑"}

            devices = []
            for d in _to_list(net.get("devices", [])):
                if isinstance(d, dict):
                    devices.append({
                        "name": d.get("name", ""),
                        "model": d.get("model", ""),
                        "interfaces": d.get("interfaces", []),
                    })
            connections = []
            for c in _to_list(net.get("connections", [])):
                if isinstance(c, dict):
                    connections.append({
                        "from": c.get("from", ""),
                        "fromInterface": c.get("fromInterface", ""),
                        "to": c.get("to", ""),
                        "toInterface": c.get("toInterface", ""),
                    })

            prompt = f"""你是网络工程师。根据以下 Cisco Packet Tracer 模拟器拓扑，为每个设备生成完整的 Cisco IOS 配置。

设备列表：
{json.dumps(devices, indent=2, ensure_ascii=False)}

连接信息：
{json.dumps(connections, indent=2, ensure_ascii=False)}

用户需求：{requirement}

注意：这是 Cisco Packet Tracer 模拟器，不是其他品牌设备。
所有配置必须使用标准 Cisco IOS 命令（switchport mode trunk 等）。

请严格按照以下 JSON 格式返回（不要有其他文字）：
{{
  "configs": [
    {{"device": "设备名", "lines": ["命令1", "命令2", ...], "is_pc": false}},
    {{"device": "PC名", "lines": ["ip 192.168.1.2 255.255.255.0 gateway 192.168.1.1"], "is_pc": true}}
  ]
}}

要求：
- 路由器：配置 hostname、接口 IP、no shutdown、路由（静态/OSPF）
- PC：格式为 ip {{ip}} {{mask}} gateway {{gateway}}
- 交换机：配置 hostname、VLAN、switchport mode trunk / switchport trunk allowed vlan、接口 no shutdown
- 保证所有网段路由可达"""

            url = f"{endpoint}/chat/completions"
            body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            reply = result["choices"][0]["message"]["content"]
            reply = reply.strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1]
                reply = reply.rsplit("```", 1)[0]
            parsed = json.loads(reply.strip())

            configs = parsed.get("configs", [])
            config_text = "\n\n".join(
                [f"=== {c['device']} ===\n" + "\n".join(c["lines"]) for c in configs]
            )
            return {"configs": configs, "configText": config_text, "errors": [], "warnings": []}

        except json.JSONDecodeError:
            return {"error": "AI 返回格式错误，请检查模型是否支持 JSON 输出"}
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode()
            except:
                detail = str(e)
            return {"error": f"API 请求失败 ({e.code}): {detail[:200]}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}\n{traceback.format_exc()[:300]}"}


def _to_list(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [v for k, v in obj.items() if isinstance(k, str) and k.isdigit()]
    return []


def main():
    api = Api()

    # 获取 HTML 文件路径
    if getattr(sys, 'frozen', False):
        # PyInstaller: web/ 在 _internal/web/ 下
        html_path = os.path.join(os.path.dirname(sys.executable), '_internal', 'web', 'index.html')
    else:
        html_path = os.path.join(base_path, 'web', 'index.html')

    if not os.path.exists(html_path):
        print(f'ERROR: HTML file not found: {html_path}')
        input('Press Enter to exit...')
        sys.exit(1)

    # 创建窗口
    window = webview.create_window(
        'NetTools v1.7',
        html_path,
        js_api=api,
        width=1200,
        height=750,
        min_size=(900, 600),
        resizable=True,
        text_select=True
    )

    # 启动应用（Windows 默认用 edgechromium 避免 lost sys.stdin）
    webview.start(debug=False, gui='edgechromium')


if __name__ == '__main__':
    main()
