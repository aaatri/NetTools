import re
from typing import Any

TEMPLATES = {
    "vlan": {
        "name": "创建 VLAN",
        "description": "在交换机上创建 VLAN 并命名",
        "fields": [
            {"key": "vlan_id", "label": "VLAN ID", "type": "number", "default": 10},
            {"key": "vlan_name", "label": "VLAN 名称", "type": "text", "default": "VLAN10"},
        ],
        "generate": lambda f: _config_block(f"vlan {f['vlan_id']}", f"name {f['vlan_name']}"),
    },
    "vlan_interface": {
        "name": "VLAN 接口（SVI）",
        "description": "创建 VLAN 三层接口并配 IP",
        "fields": [
            {"key": "vlan_id", "label": "VLAN ID", "type": "number", "default": 10},
            {"key": "ip", "label": "IP 地址", "type": "text", "default": "192.168.10.1"},
            {"key": "mask", "label": "子网掩码", "type": "text", "default": "255.255.255.0"},
        ],
        "generate": lambda f: _config_block(
            f"interface vlan {f['vlan_id']}",
            f"ip address {f['ip']} {f['mask']}",
            "no shutdown",
        ),
    },
    "access_vlan": {
        "name": "Access 端口",
        "description": "将交换机端口设为 Access 并加入 VLAN",
        "fields": [
            {"key": "interface", "label": "接口名", "type": "text", "default": "FastEthernet0/1"},
            {"key": "vlan_id", "label": "VLAN ID", "type": "number", "default": 10},
        ],
        "generate": lambda f: _config_block(
            f"interface {f['interface']}",
            "switchport mode access",
            f"switchport access vlan {f['vlan_id']}",
        ),
    },
    "trunk": {
        "name": "Trunk 端口",
        "description": "将交换机端口设为 Trunk",
        "fields": [
            {"key": "interface", "label": "接口名", "type": "text", "default": "GigabitEthernet0/1"},
            {"key": "native_vlan", "label": "Native VLAN", "type": "number", "default": 1},
        ],
        "generate": lambda f: _config_block(
            f"interface {f['interface']}",
            "switchport mode trunk",
            f"switchport trunk native vlan {f['native_vlan']}",
        ),
    },
    "dhcp_pool": {
        "name": "DHCP 地址池",
        "description": "在路由器上配置 DHCP 池",
        "fields": [
            {"key": "pool_name", "label": "池名称", "type": "text", "default": "POOL1"},
            {"key": "network", "label": "网络号", "type": "text", "default": "192.168.10.0"},
            {"key": "mask", "label": "子网掩码", "type": "text", "default": "255.255.255.0"},
            {"key": "default_router", "label": "默认网关", "type": "text", "default": "192.168.10.1"},
            {"key": "dns", "label": "DNS 服务器", "type": "text", "default": "8.8.8.8"},
        ],
        "generate": lambda f: _config_block(
            f"ip dhcp pool {f['pool_name']}",
            f"network {f['network']} {f['mask']}",
            f"default-router {f['default_router']}",
            f"dns-server {f['dns']}",
        ),
    },
    "ospf": {
        "name": "OSPF",
        "description": "配置 OSPF 动态路由",
        "fields": [
            {"key": "process_id", "label": "进程 ID", "type": "number", "default": 1},
            {"key": "networks", "label": "网络 (逗号分隔)", "type": "text", "default": "192.168.1.0 0.0.0.255 area 0"},
            {"key": "router_id", "label": "Router ID", "type": "text", "default": ""},
        ],
        "generate": lambda f: _generate_ospf(f),
    },
    "static_route": {
        "name": "静态路由",
        "description": "配置静态路由",
        "fields": [
            {"key": "network", "label": "目标网络", "type": "text", "default": "0.0.0.0"},
            {"key": "mask", "label": "子网掩码", "type": "text", "default": "0.0.0.0"},
            {"key": "next_hop", "label": "下一跳", "type": "text", "default": "192.168.1.1"},
        ],
        "generate": lambda f: [f"ip route {f['network']} {f['mask']} {f['next_hop']}"],
    },
    "acl_standard": {
        "name": "标准 ACL",
        "description": "配置标准 ACL（编号）",
        "fields": [
            {"key": "number", "label": "ACL 编号", "type": "number", "default": 1},
            {"key": "action", "label": "动作", "type": "select", "options": ["permit", "deny"], "default": "deny"},
            {"key": "source", "label": "源网络", "type": "text", "default": "192.168.1.0"},
            {"key": "wildcard", "label": "通配符掩码", "type": "text", "default": "0.0.0.255"},
        ],
        "generate": lambda f: [f"access-list {f['number']} {f['action']} {f['source']} {f['wildcard']}"],
    },
    "acl_extended": {
        "name": "扩展 ACL",
        "description": "配置扩展 ACL",
        "fields": [
            {"key": "number", "label": "ACL 编号", "type": "number", "default": 100},
            {"key": "action", "label": "动作", "type": "select", "options": ["permit", "deny"], "default": "deny"},
            {"key": "protocol", "label": "协议", "type": "select", "options": ["ip", "tcp", "udp", "icmp"], "default": "tcp"},
            {"key": "src", "label": "源网络", "type": "text", "default": "192.168.1.0"},
            {"key": "src_wildcard", "label": "源通配符", "type": "text", "default": "0.0.0.255"},
            {"key": "dst", "label": "目标网络", "type": "text", "default": "any"},
            {"key": "dst_wildcard", "label": "目标通配符", "type": "text", "default": ""},
            {"key": "dst_port", "label": "目标端口", "type": "number", "default": 80, "required": False},
        ],
        "generate": lambda f: _generate_acl_ext(f),
    },
    "rip": {
        "name": "RIP",
        "description": "配置 RIP 动态路由",
        "fields": [
            {"key": "version", "label": "版本", "type": "select", "options": ["1", "2"], "default": "2"},
            {"key": "networks", "label": "直连网络 (逗号分隔)", "type": "text", "default": "192.168.1.0, 192.168.2.0"},
        ],
        "generate": lambda f: _generate_rip(f),
    },
    "eigrp": {
        "name": "EIGRP",
        "description": "配置 EIGRP 动态路由",
        "fields": [
            {"key": "as_number", "label": "AS 号", "type": "number", "default": 100},
            {"key": "networks", "label": "直连网络 (逗号分隔)", "type": "text", "default": "192.168.1.0, 192.168.2.0"},
        ],
        "generate": lambda f: _generate_eigrp(f),
    },
    "nat_static": {
        "name": "静态 NAT",
        "description": "配置静态 NAT 映射",
        "fields": [
            {"key": "inside_local", "label": "内部本地 IP", "type": "text", "default": "192.168.1.10"},
            {"key": "inside_global", "label": "内部全局 IP", "type": "text", "default": "200.100.50.10"},
        ],
        "generate": lambda f: [f"ip nat inside source static {f['inside_local']} {f['inside_global']}"],
    },
    "nat_pat": {
        "name": "PAT (NAT 过载)",
        "description": "配置 PAT（端口地址转换）",
        "fields": [
            {"key": "acl", "label": "ACL 编号", "type": "number", "default": 1},
            {"key": "inside_int", "label": "内部接口", "type": "text", "default": "GigabitEthernet0/0"},
            {"key": "outside_int", "label": "外部接口", "type": "text", "default": "GigabitEthernet0/1"},
            {"key": "pool_name", "label": "地址池名（留空用接口）", "type": "text", "default": ""},
            {"key": "pool_start", "label": "池起始（可选）", "type": "text", "default": ""},
            {"key": "pool_end", "label": "池结束（可选）", "type": "text", "default": ""},
        ],
        "generate": lambda f: _generate_pat(f),
    },
    "port_security": {
        "name": "端口安全",
        "description": "配置交换机端口安全",
        "fields": [
            {"key": "interface", "label": "接口", "type": "text", "default": "FastEthernet0/1"},
            {"key": "max_mac", "label": "最大 MAC 数", "type": "number", "default": 1},
            {"key": "violation", "label": "违规模式", "type": "select", "options": ["protect", "restrict", "shutdown"], "default": "shutdown"},
            {"key": "mac_address", "label": "MAC 地址（可选）", "type": "text", "default": "", "required": False},
        ],
        "generate": lambda f: _generate_port_sec(f),
    },
    "spanning_tree": {
        "name": "STP 生成树",
        "description": "配置生成树协议（BPDU Guard / Root Guard / PortFast）",
        "fields": [
            {"key": "interface", "label": "接口", "type": "text", "default": "GigabitEthernet0/1"},
            {"key": "features", "label": "功能", "type": "select", "options": ["portfast+bpduguard", "bpduguard", "rootguard", "portfast"], "default": "portfast+bpduguard"},
        ],
        "generate": lambda f: _generate_stp(f),
    },
    "inter_vlan_router": {
        "name": "单臂路由",
        "description": "在路由器子接口上配单臂路由（Router-on-a-Stick）",
        "fields": [
            {"key": "interface", "label": "物理接口", "type": "text", "default": "GigabitEthernet0/0"},
            {"key": "vlans", "label": "VLAN 配置 (格式: VID,IP,掩码; 多组用逗号)", "type": "text", "default": "10,192.168.10.1,255.255.255.0,20,192.168.20.1,255.255.255.0"},
        ],
        "generate": lambda f: _generate_inter_vlan(f),
    },
    "hsrp": {
        "name": "HSRP",
        "description": "配置 HSRP 热备份路由",
        "fields": [
            {"key": "interface", "label": "接口", "type": "text", "default": "GigabitEthernet0/0"},
            {"key": "group", "label": "组号", "type": "number", "default": 1},
            {"key": "virtual_ip", "label": "虚拟 IP", "type": "text", "default": "192.168.1.254"},
            {"key": "priority", "label": "优先级", "type": "number", "default": 100},
            {"key": "preempt", "label": "抢占", "type": "checkbox", "default": True},
        ],
        "generate": lambda f: _generate_hsrp(f),
    },
    "etherchannel": {
        "name": "EtherChannel",
        "description": "配置 EtherChannel（端口聚合）",
        "fields": [
            {"key": "channel_id", "label": "Channel 组号", "type": "number", "default": 1},
            {"key": "mode", "label": "模式", "type": "select", "options": ["active", "passive", "auto", "desirable", "on"], "default": "active"},
            {"key": "interfaces", "label": "成员接口 (逗号分隔)", "type": "text", "default": "FastEthernet0/1, FastEthernet0/2"},
            {"key": "trunk", "label": "设为 Trunk", "type": "checkbox", "default": True},
        ],
        "generate": lambda f: _generate_etherchannel(f),
    },
}


def _config_block(*lines):
    return [line for line in lines if line]


def _generate_ospf(f):
    cmds = [f"router ospf {f['process_id']}"]
    if f.get("router_id"):
        cmds.append(f"router-id {f['router_id']}")
    networks = [n.strip() for n in f.get("networks", "").split(",") if n.strip()]
    for net in networks:
        cmds.append(f"network {net}")
    return cmds


def _generate_rip(f):
    cmds = ["router rip"]
    if f["version"] == "2":
        cmds.append("version 2")
        cmds.append("no auto-summary")
    networks = [n.strip() for n in f.get("networks", "").split(",") if n.strip()]
    for net in networks:
        cmds.append(f"network {net}")
    return cmds


def _generate_eigrp(f):
    cmds = [f"router eigrp {f['as_number']}"]
    cmds.append("no auto-summary")
    networks = [n.strip() for n in f.get("networks", "").split(",") if n.strip()]
    for net in networks:
        cmds.append(f"network {net}")
    return cmds


def _generate_acl_ext(f):
    line = f"access-list {f['number']} {f['action']} {f['protocol']} {f['src']} {f['src_wildcard']} {f['dst']}"
    if f.get("dst_wildcard"):
        line += f" {f['dst_wildcard']}"
    if f.get("dst_port"):
        line += f" eq {f['dst_port']}"
    return [line]


def _generate_pat(f):
    cmds = []
    if f.get("pool_name") and f.get("pool_start") and f.get("pool_end"):
        cmds.append(f"ip nat pool {f['pool_name']} {f['pool_start']} {f['pool_end']} netmask 255.255.255.0")
        cmds.append(f"ip nat inside source list {f['acl']} pool {f['pool_name']} overload")
    else:
        cmds.append(f"ip nat inside source list {f['acl']} interface {f['outside_int']} overload")
    cmds.append(f"interface {f['inside_int']}")
    cmds.append("ip nat inside")
    cmds.append("exit")
    cmds.append(f"interface {f['outside_int']}")
    cmds.append("ip nat outside")
    return cmds


def _generate_port_sec(f):
    cmds = [
        f"interface {f['interface']}",
        "switchport port-security",
        f"switchport port-security maximum {f['max_mac']}",
        f"switchport port-security violation {f['violation']}",
    ]
    if f.get("mac_address"):
        cmds.append(f"switchport port-security mac-address {f['mac_address']}")
    return cmds


def _generate_stp(f):
    cmds = [f"interface {f['interface']}"]
    if "portfast" in f["features"]:
        cmds.append("spanning-tree portfast")
    if "bpduguard" in f["features"]:
        cmds.append("spanning-tree bpduguard enable")
    if "rootguard" in f["features"]:
        cmds.append("spanning-tree guard root")
    return cmds


def _generate_inter_vlan(f):
    parts = [p.strip() for p in f["vlans"].split(",")]
    cmds = []
    i = 0
    while i + 2 < len(parts):
        vlan_id = parts[i]
        ip = parts[i + 1]
        mask = parts[i + 2]
        sub_if = f"{f['interface']}.{vlan_id}"
        cmds.extend([
            f"interface {sub_if}",
            f"encapsulation dot1Q {vlan_id}",
            f"ip address {ip} {mask}",
            "no shutdown",
        ])
        i += 3
    return cmds


def _generate_hsrp(f):
    cmds = [
        f"interface {f['interface']}",
        f"standby {f['group']} ip {f['virtual_ip']}",
        f"standby {f['group']} priority {f['priority']}",
    ]
    if f.get("preempt"):
        cmds.append(f"standby {f['group']} preempt")
    return cmds


def _generate_etherchannel(f):
    intfs = [i.strip() for i in f.get("interfaces", "").split(",") if i.strip()]
    cmds = []
    for intf in intfs:
        cmds.extend([
            f"interface {intf}",
            f"channel-group {f['channel_id']} mode {f['mode']}",
        ])
    if f.get("trunk"):
        cmds.extend([
            f"interface port-channel {f['channel_id']}",
            "switchport mode trunk",
        ])
    return cmds


def get_template_list():
    return [
        {"key": k, "name": v["name"], "description": v["description"], "fields": v["fields"]}
        for k, v in TEMPLATES.items()
    ]


def generate_from_template(template_key: str, fields: dict) -> dict:
    tmpl = TEMPLATES.get(template_key)
    if not tmpl:
        return {"success": False, "error": f"Unknown template: {template_key}"}
    commands = tmpl["generate"](fields)
    return {"success": True, "template": template_key, "commands": commands}


RULE_PATTERNS = [
    (r"创建?VLAN\s*(\d+)\s*名称?\s*(\S+)", lambda m: {
        "template": "vlan",
        "fields": {"vlan_id": int(m.group(1)), "vlan_name": m.group(2)},
    }),
    (r"(?:vlan|VLAN)\s*(\d+)\s*接口?.*IP\s*([\d.]+)\s*掩码?\s*([\d.]+)", lambda m: {
        "template": "vlan_interface",
        "fields": {"vlan_id": int(m.group(1)), "ip": m.group(2), "mask": m.group(3)},
    }),
    (r"DHCP.*池\s*(\S+)\s*网络\s*([\d.]+)\s*掩码?\s*([\d.]+)", lambda m: {
        "template": "dhcp_pool",
        "fields": {"pool_name": m.group(1), "network": m.group(2), "mask": m.group(3)},
    }),
    (r"OSPF\s*(进程?ID)?\s*(\d+)", lambda m: {
        "template": "ospf",
        "fields": {"process_id": int(m.group(2)), "networks": ""},
    }),
    (r"静态路由\s*([\d.]+)\s*掩码?\s*([\d.]+)\s*(?:下一跳)?\s*([\d.]+)", lambda m: {
        "template": "static_route",
        "fields": {"network": m.group(1), "mask": m.group(2), "next_hop": m.group(3)},
    }),
    (r"(?:标准)?ACL\s*(\d+)\s*(允许|拒绝)\s*([\d.]+)", lambda m: {
        "template": "acl_standard",
        "fields": {
            "number": int(m.group(1)),
            "action": "permit" if m.group(2) == "允许" else "deny",
            "source": m.group(3),
        },
    }),
    (r"单臂路由\s*接口\s*(\S+)", lambda m: {
        "template": "inter_vlan_router",
        "fields": {"interface": m.group(1), "vlans": ""},
    }),
    (r"端口安全\s*接口\s*(\S+)", lambda m: {
        "template": "port_security",
        "fields": {"interface": m.group(1)},
    }),
    (r"Trunk\s*接口\s*(\S+)", lambda m: {
        "template": "trunk",
        "fields": {"interface": m.group(1)},
    }),
    (r"Access\s*接口\s*(\S+).*VLAN\s*(\d+)", lambda m: {
        "template": "access_vlan",
        "fields": {"interface": m.group(1), "vlan_id": int(m.group(2))},
    }),
]


def parse_natural_language(text: str) -> dict:
    for pattern, builder in RULE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return {"matched": True, **builder(m)}
    return {"matched": False, "error": "无法识别需求，请换一种描述方式或使用模板手动配置"}
