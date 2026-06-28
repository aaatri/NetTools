# -*- coding: utf-8 -*-
"""Ping 检测"""
import subprocess, sys, logging
from typing import Callable

_IS_WIN = sys.platform == 'win32'
_CF = subprocess.CREATE_NO_WINDOW if _IS_WIN else 0
log = logging.getLogger('NetTools')

def ping(progress: Callable, host: str, count: int = 4, timeout: int = 3) -> tuple:
    """Ping 检测，每完成一次即回调 progress"""
    if not host or not host.strip():
        results = [{'seq': 1, 'success': False, 'output': '主机为空'}]
        progress(results[0])
        return results, 0, 1

    results, successes = [], 0
    for i in range(count):
        try:
            param = '-n' if _IS_WIN else '-c'
            tmo = str(timeout * 1000)
            # Windows: -w 毫秒; Linux: -W 秒
            cmd = (['ping', param, '1', '-w', tmo, host] if _IS_WIN
                   else ['ping', param, '1', '-W', str(timeout), host])
            t = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout + 1, creationflags=_CF)
            ok = t.returncode == 0
            if ok: successes += 1
            entry = {'seq': i + 1, 'success': ok,
                     'output': t.stdout.strip() if ok else 'timeout'}
        except subprocess.TimeoutExpired:
            entry = {'seq': i + 1, 'success': False, 'output': 'timeout'}
        except Exception as e:
            log.error(f'Ping 异常: {e}')
            entry = {'seq': i + 1, 'success': False, 'output': f'error: {e}'}
        results.append(entry)
        progress(entry)
    return results, successes, count
