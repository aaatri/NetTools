# -*- mode: python ; coding: utf-8 -*-
# NetTools.spec - pywebview 版本

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect engineio async drivers (dynamically imported by engineio/socketio)
extra_hidden = collect_submodules('engineio.async_drivers')
extra_hidden += collect_submodules('simple_websocket')

# Force-include async_drivers and simple_websocket directories
import engineio
async_dir = os.path.join(os.path.dirname(engineio.__file__), 'async_drivers')
async_datas = []
for f in os.listdir(async_dir):
    fp = os.path.join(async_dir, f)
    if os.path.isfile(fp):
        async_datas.append((fp, 'engineio/async_drivers'))

import simple_websocket
sw_dir = os.path.dirname(simple_websocket.__file__)
sw_datas = []
for f in os.listdir(sw_dir):
    fp = os.path.join(sw_dir, f)
    if os.path.isfile(fp):
        sw_datas.append((fp, 'simple_websocket'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web'), ('icons', 'web/icons'), ('extension', '_internal/extension'), ('tools', 'tools'), ('ico.ico', '.'), ('main.png', '_internal')]
           + async_datas + sw_datas,
    hiddenimports=[
        'webview',
        'tools',
        'tools.subnet',
        'tools.bandwidth',
        'tools.portscan',
        'tools.ping',
        'tools.dns',
        'tools.traceroute',
        'tools.whois',
        'tools.query',
        'tools.hexconv',
        'tools.pt_bridge',

        'socketio',
        'aiohttp',
        'engineio',
        'simple_websocket',
    ] + extra_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NetTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NetTools',
)
