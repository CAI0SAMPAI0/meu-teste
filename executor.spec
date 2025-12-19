import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

BASE_DIR = os.getcwd()

# --------------------------
# Módulos essenciais (incluindo http e urllib)
# --------------------------
hiddenimports = (
    collect_submodules("selenium") +
    collect_submodules("undetected_chromedriver") +
    collect_submodules("http") +      # CRÍTICO para Selenium
    collect_submodules("urllib") +    # CRÍTICO para Selenium
    collect_submodules("email") +
    ["http.client", "http.server", "urllib.request", "urllib.parse"]
)

# --------------------------
# Analysis
# --------------------------
a = Analysis(
    ["executor.py"],
    pathex=[BASE_DIR],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Removi http, urllib e xml da lista de exclusão!
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
    ],
    noarchive=False,  # Mudei para False (melhor compatibilidade)
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
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,  # Mudei para False (facilita debug)
)

# --------------------------
# COLLECT
# --------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        "vcruntime140.dll",
        "python312.dll",
    ],
    name="executor",
)