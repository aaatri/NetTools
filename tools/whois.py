# -*- coding: utf-8 -*-
"""IP 归属查询"""
import json, urllib.request, logging
from typing import Callable

log = logging.getLogger('NetTools')

def whois_ip(progress: Callable, ip: str) -> str:
    if not ip or not ip.strip():
        return json.dumps({"error": "IP 地址为空"})
    try:
        url = f'https://ipinfo.io/{ip}/json'
        req = urllib.request.Request(url, headers={'User-Agent': 'NetTools/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        log.error(f'whois_ip 异常: {e}')
        return json.dumps({"error": str(e)})
