# -*- coding: utf-8 -*-
"""带宽换算"""
def bw_convert(value: float, frm: str, to: str) -> float:
    units = {'bps': 1, 'Kbps': 1e3, 'Mbps': 1e6, 'Gbps': 1e9, 'Tbps': 1e12}
    if frm not in units: raise ValueError(f'未知单位: {frm}')
    if to not in units: raise ValueError(f'未知单位: {to}')
    return value * units[frm] / units[to]
