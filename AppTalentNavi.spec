# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\hajime.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\co-vibe.py', '.'), ('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\ollama_setup.py', '.'), ('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\data', 'data'), ('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\skills', 'skills'), ('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\templates', 'templates'), ('C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\.env.example', '.')],
    hiddenimports=['ollama_setup', 'html', 'html.parser', 'json', 're', 'uuid', 'argparse', 'subprocess', 'fnmatch', 'platform', 'shutil', 'tempfile', 'threading', 'unicodedata', 'urllib.request', 'urllib.error', 'urllib.parse', 'hashlib', 'traceback', 'base64', 'atexit', 'abc', 'datetime', 'collections', 'concurrent.futures', 'ssl', 'readline', 'ctypes', 'select', 'difflib', 'heapq', 'socket', 'ipaddress', 'locale', 'sqlite3', 'ast', 'shlex', 'zlib', 'webbrowser', 'random', 'itertools', 'pathlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AppTalentNavi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Users\\tsuba\\AppTalentHub\\02_product\\00_prototypes\\AppTalentNavi v2.0\\version_info.txt',
)
