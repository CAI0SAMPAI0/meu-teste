# executor.spec
import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

BASE_DIR = os.getcwd()

# --------------------------
# Forçar inclusão dos módulos essenciais
# --------------------------
hiddenimports = (
    collect_submodules("selenium") +
    collect_submodules("undetected_chromedriver") +
    ["email"]  # necessário para evitar ModuleNotFoundError
)

# --------------------------
# Analysis
# --------------------------
a = Analysis(
    ["executor.py"],
    pathex=[BASE_DIR],
    binaries=[],
    datas=[],  # executor não precisa de pastas extras
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PySide6",
        "PyQt5",
        "PyQt6",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "unittest",
        "http",
        "xml",
    ],
    noarchive=True,  # crítico para Selenium
)

# --------------------------
# PYZ
# --------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --------------------------
# EXE
# --------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="executor",
    debug=False,
    strip=True,
    upx=True,
    console=False,  # executor silencioso
    disable_windowed_traceback=True,
)

# --------------------------
# COLLECT
# --------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[
        "vcruntime140.dll",
        "python312.dll",
    ],
    name="executor",
)
