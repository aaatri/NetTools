# -*- coding: utf-8 -*-
"""进制转换：输入任意进制数，同时显示 Bin / Oct / Dec / Hex"""
from typing import Callable

_BASES = {
    'bin': 2, '二': 2, '2': 2, '二进制': 2,
    'oct': 8, '八': 8, '8': 8, '八进制': 8,
    'dec': 10, '十': 10, '10': 10, '十进制': 10,
    'hex': 16, '十六': 16, '16': 16, '十六进制': 16,
}

def convert_all(progress: Callable, value: str, src_base: str) -> dict:
    """将 value 从 src_base 转为全部 4 种进制"""
    base = _BASES.get(src_base.lower())
    if base is None:
        return {'error': f'不支持的进制: {src_base}'}

    value = value.strip().lower()
    if not value:
        return {'error': '输入不能为空'}

    # 处理常见前缀
    original = value
    if base == 2 and value.startswith('0b'):
        value = value[2:]
    elif base == 16 and value.startswith('0x'):
        value = value[2:]
    elif base == 8 and value.startswith('0o'):
        value = value[2:]

    if not value:
        return {'error': '输入不能为空'}

    # 输入验证
    allowed = {
        2: set('01'),
        8: set('01234567'),
        10: set('0123456789'),
        16: set('0123456789abcdef'),
    }[base]
    for ch in value:
        if ch not in allowed:
            return {'error': f'输入"{original}"在{src_base}进制中包含无效字符 "{ch}"'}

    try:
        num = int(value, base)
    except ValueError as e:
        return {'error': f'转换失败: {e}'}

    return {
        'input': original,
        'src_base': base,
        'decimal': str(num),
        'bin': bin(num)[2:],
        'oct': oct(num)[2:],
        'dec': str(num),
        'hex': hex(num)[2:].upper(),
        'bin_zfill': _zfill_bin(num),
    }

def _zfill_bin(n: int) -> str:
    """二进制按 4 位分组补零"""
    if n == 0: return '0000'
    bits = bin(n)[2:]
    pad = (4 - len(bits) % 4) % 4
    padded = '0' * pad + bits
    return ' '.join(padded[i:i+4] for i in range(0, len(padded), 4))
