# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH).parent

a = Analysis(
    [str(project_root / "packaging" / "run_coinductor.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "coinductor" / "qml"), "coinductor/qml"),
        (str(project_root / "coinductor" / "assets" / "guides"), "coinductor/assets/guides"),
        (str(project_root / "coinductor" / "coinductor.ico"), "coinductor"),
        (str(project_root / "config.example.toml"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Coinductor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(project_root / "coinductor" / "coinductor.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Coinductor",
)
