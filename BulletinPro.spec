# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BulletinPro
Build: pyinstaller BulletinPro.spec
"""

import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collecter tous les modules
flet_datas, flet_binaries, flet_hiddenimports = collect_all('flet')
flet_core_datas, flet_core_binaries, flet_core_hiddenimports = collect_all('flet_core')
flet_runtime_datas, flet_runtime_binaries, flet_runtime_hiddenimports = collect_all('flet_runtime')
weasyprint_datas, weasyprint_binaries, weasyprint_hiddenimports = collect_all('weasyprint')
cairocffi_datas, cairocffi_binaries, cairocffi_hiddenimports = collect_all('cairocffi')

# Combiner toutes les données
all_datas = (
    flet_datas + 
    flet_core_datas + 
    flet_runtime_datas + 
    weasyprint_datas + 
    cairocffi_datas
)

all_binaries = (
    flet_binaries + 
    flet_core_binaries + 
    flet_runtime_binaries + 
    weasyprint_binaries + 
    cairocffi_binaries
)

# Ajouter config.py
all_datas += [('config.py', '.')]

# Hidden imports
hiddenimports = (
    flet_hiddenimports +
    flet_core_hiddenimports +
    flet_runtime_hiddenimports +
    [
        'flet.fastapi',
        'sqlite3',
        'weasyprint',
        'jinja2',
        'supabase',
        'dotenv',
        'cairocffi',
        'PIL',
        'PIL.Image',
    ]
)

a = Analysis(
    ['Page2.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BulletinPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
