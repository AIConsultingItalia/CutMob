# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.png', '.'), ('app_icon.ico', '.')],
    hiddenimports=['pymysql', 'pyodbc', 'mysql.connector', 'pymssql'],
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
    name='CutMob',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app_icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CutMob',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='CutMob.app',
        icon='logo.icns',
        bundle_identifier='com.cutmob.app'
    )
