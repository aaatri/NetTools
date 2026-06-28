# -*- coding: utf-8 -*-
"""DNS 查询"""
import socket, logging
from typing import Callable

log = logging.getLogger('NetTools')

def dns_lookup(progress: Callable, domain: str, record_type: str = 'A') -> list:
    """DNS A 记录查询，progress 预留"""
    if not domain or not domain.strip():
        return [{'type': 'error', 'value': '域名为空'}]
    try:
        if record_type != 'A':
            return [{'type': 'unknown', 'value': f'{record_type} 查询暂不支持，目前仅支持 A 记录'}]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.close()
        r = socket.getaddrinfo(domain, None)
        ips = list(dict.fromkeys(a[4][0] for a in r))  # preserve order, dedupe
        return [{'type': 'A', 'value': ip} for ip in ips]
    except socket.gaierror as e:
        log.debug(f'DNS 解析失败: {domain} - {e}')
        return [{'type': 'error', 'value': f'无法解析域名: {e}'}]
    except Exception as e:
        log.error(f'DNS 查询异常: {e}')
        return [{'type': 'error', 'value': str(e)}]
