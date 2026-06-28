# -*- coding: utf-8 -*-
"""路由追踪"""
import subprocess, sys, logging
from typing import Callable

_IS_WIN = sys.platform == 'win32'
_CF = subprocess.CREATE_NO_WINDOW if _IS_WIN else 0
log = logging.getLogger('NetTools')

_TRACERT_HEADER_KEYWORDS = {'tracert', 'trace', 'traceroute', 'over', 'maximum', 'hops', 'tracing', 'route', 'to'}

def traceroute(progress: Callable, host: str, max_hops: int = 30) -> list:
    """路由追踪，progress 预留"""
    if not host or not host.strip():
        return [{'raw': '目标主机为空'}]

    results = []
    try:
        cmd = (['tracert', '-d', '-h', str(max_hops), host] if _IS_WIN
               else ['traceroute', '-n', '-m', str(max_hops), host])
        t = subprocess.run(cmd, capture_output=True, text=True, timeout=80, creationflags=_CF)
        for line in t.stdout.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            # 过滤头部行
            if any(kw in lower for kw in _TRACERT_HEADER_KEYWORDS) and not any(
                c.isdigit() for c in stripped[:4] if c.strip()
            ):
                continue
            results.append({'raw': stripped})
        if not results:
            results.append({'raw': t.stdout.strip()[:300] if t.stdout else '无输出'})
    except subprocess.TimeoutExpired:
        results.append({'raw': '路由追踪超时 (80s)'})
    except Exception as e:
        log.error(f'路由追踪异常: {e}')
        results.append({'raw': f'错误: {e}'})
    return results
