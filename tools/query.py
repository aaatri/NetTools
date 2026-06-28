# -*- coding: utf-8 -*-
"""快速查询 (IP/域名)"""
import ipaddress, socket, logging
from typing import Callable

log = logging.getLogger('NetTools')

def quick_query(progress: Callable, ip_or_domain: str) -> dict:
    """快速 IP/域名 解析，progress 预留"""
    if not ip_or_domain or not ip_or_domain.strip():
        return {'type': 'unknown', 'value': '', 'error': '输入为空'}

    try:
        ip = ipaddress.ip_address(ip_or_domain)
        return {'type': 'ip', 'value': str(ip), 'version': ip.version}
    except ValueError:
        pass

    try:
        r = socket.getaddrinfo(ip_or_domain, None)
        ips = list(dict.fromkeys(a[4][0] for a in r))
        return {'type': 'domain', 'value': ip_or_domain, 'ips': ips}
    except socket.gaierror as e:
        return {'type': 'unknown', 'value': ip_or_domain, 'error': f'域名解析失败: {e}'}
    except Exception as e:
        log.error(f'快速查询异常: {e}')
        return {'type': 'unknown', 'value': ip_or_domain, 'error': str(e)}
