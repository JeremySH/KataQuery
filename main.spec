# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('katago-bin', 'katago-bin')],
    hiddenimports=['matplotlib.backends.backend_qtagg', 'pandas', 'GameSettingsDialog', "GameSettingsDialog_ui", "NeuralNetSettingsDialog_ui", "NeuralNetSettingsDialog"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["setuptools", "pip", "pyinstaller"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KataQuery',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
app = BUNDLE(
    coll,
    name='KataQuery.app',
    icon='resources/images/icon.ico',
    bundle_identifier=None,
)
