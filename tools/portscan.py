# -*- coding: utf-8 -*-
"""端口扫描"""
import socket, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

log = logging.getLogger('NetTools')

def port_scan(progress: Callable, host: str, ports: list,
              timeout: float = 0.8, max_workers: int = 20) -> list:
    """并行扫描端口，progress 预留未来进度推送"""
    if not host or not host.strip():
        return [{'port': p, 'open': False, 'service': '?', 'error': '主机为空'} for p in ports]

    def _scan_one(p: int):
        if not 1 <= p <= 65535:
            return {'port': p, 'open': False, 'service': '?', 'error': f'无效端口'}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(timeout)
            r = s.connect_ex((host, p))
            return {'port': p, 'open': r == 0, 'service': _port_service(p)}
        except Exception as e:
            log.debug(f'端口 {p} 扫描异常: {e}')
            return {'port': p, 'open': False, 'service': _port_service(p), 'error': str(e)}
        finally:
            try: s.close()
            except Exception: pass

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_scan_one, p): p for p in ports}
        for f in as_completed(futures):
            results.append(f.result())
    results.sort(key=lambda x: x['port'])
    return results

def _port_service(p: int) -> str:
    return {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
        80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB',
        993: 'IMAPS', 995: 'POP3S', 3306: 'MySQL', 3389: 'RDP',
        5432: 'PostgreSQL', 8080: 'HTTP-Alt', 6379: 'Redis', 27017: 'MongoDB',
        1433: 'MSSQL', 1521: 'Oracle', 8443: 'HTTPS-Alt', 9090: 'WebUI',
    }.get(p, 'Unknown')
