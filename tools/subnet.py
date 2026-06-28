# -*- coding: utf-8 -*-
"""子网计算 & VLSM"""
import ipaddress, logging

log = logging.getLogger('NetTools')

class SubnetCalc:
    @staticmethod
    def cidr_to_mask(prefix: int) -> str:
        if not 0 <= prefix <= 32:
            raise ValueError(f'前缀必须在 0-32 之间，收到 {prefix}')
        mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
        return '.'.join(str((mask_int >> (8 * (3 - i))) & 0xFF) for i in range(4))

    @staticmethod
    def mask_to_cidr(mask: str) -> int:
        try: return sum(bin(int(x)).count('1') for x in mask.split('.'))
        except Exception: return 0

    @staticmethod
    def calc(network: str, prefix: int):
        try:
            n = ipaddress.IPv4Network(f'{network}/{prefix}', strict=False)
            total_ips = 1 << (32 - prefix)
            usable = total_ips - 2
            first_ip = str(n.network_address + 1) if usable > 0 else 'N/A'
            last_ip = str(n.broadcast_address - 1) if usable > 0 else 'N/A'
            wildcard = '.'.join(str(255 - int(x)) for x in SubnetCalc.cidr_to_mask(prefix).split('.'))
            bin_mask = '.'.join(f'{int(x):08b}' for x in str(n.netmask).split('.'))
            fo = int(str(n.network_address).split('.')[0])
            nc = 'A' if fo < 128 else 'B' if fo < 192 else 'C' if fo < 224 else 'D' if fo < 240 else 'E'
            return {
                'network': str(n.network_address), 'mask': str(n.netmask),
                'wildcard': wildcard, 'prefix': prefix,
                'broadcast': str(n.broadcast_address) if prefix < 31 else 'N/A',
                'total': total_ips, 'usable': max(0, usable),
                'first': first_ip, 'last': last_ip,
                'binary_mask': bin_mask, 'class': nc,
                'is_private': n.is_private, 'is_loopback': n.is_loopback,
            }
        except Exception as e: return {'error': str(e)}

    @staticmethod
    def vlsm(network: str, prefix: int, hosts: list):
        try:
            hosts = [h for h in hosts if h > 0]
            if not hosts: return [{'error': '所有主机数必须大于 0'}]
            base = ipaddress.IPv4Network(f'{network}/{prefix}', strict=False)
            results = []
            sorted_hosts = sorted(enumerate(hosts), key=lambda x: x[1], reverse=True)
            current_int = int(base.network_address)
            end_int = int(base.broadcast_address)
            for idx, h in sorted_hosts:
                need_bits = max(1, (h + 2).bit_length())
                sub_prefix = 32 - need_bits
                if sub_prefix < prefix: sub_prefix = prefix
                host_bits = 32 - sub_prefix
                mask = (0xFFFFFFFF << host_bits) & 0xFFFFFFFF
                aligned = current_int & mask
                if aligned < current_int: aligned += (1 << host_bits)
                if aligned > end_int:
                    results.append({'index': idx, 'hosts': h, 'subnet': '无可用空间', 'error': True})
                    continue
                sub_size = 1 << host_bits
                usable = sub_size - 2
                results.append({
                    'index': idx, 'hosts': h,
                    'subnet': str(ipaddress.IPv4Address(aligned)),
                    'mask': str(ipaddress.IPv4Network(f'{ipaddress.IPv4Address(aligned)}/{sub_prefix}', strict=True).netmask),
                    'prefix': sub_prefix, 'usable': max(0, usable),
                    'first': str(ipaddress.IPv4Address(aligned + 1)) if usable > 0 else 'N/A',
                    'last': str(ipaddress.IPv4Address(aligned + sub_size - 2)) if usable > 0 else 'N/A',
                    'broadcast': str(ipaddress.IPv4Address(aligned + sub_size - 1)) if sub_prefix < 31 else 'N/A',
                })
                current_int = aligned + sub_size
            results.sort(key=lambda x: x['index'])
            return results
        except Exception as e: return [{'error': str(e)}]

    @staticmethod
    def supernet(subnets: list):
        try:
            nets = [ipaddress.IPv4Network(s, strict=False) for s in subnets]
            return [str(s) for s in ipaddress.collapse_addresses(nets)]
        except Exception as e: return [str(e)]
