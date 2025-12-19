import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

BASE_DIR = os.getcwd()

# --------------------------
# Módulos essenciais (incluindo http e urllib)
# --------------------------
hiddenimports = (
    collect_submodules("PySide6") +
    collect_submodules("selenium") +
    collect_submodules("undetected_chromedriver") +
    collect_submodules("http") +      # CRÍTICO para Selenium
    collect_submodules("urllib") +    # CRÍTICO para Selenium
    collect_submodules("email") +
    ["http.client", "http.server", "urllib.request", "urllib.parse"]
)

# --------------------------
# Dados do projeto
# --------------------------
datas = [
    ("ui", "ui"),
    ("core", "core"),
    ("data", "data"),
    ("resources", "resources"),
]

# --------------------------
# Analysis
# --------------------------
a = Analysis(
    ["app.py"],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Removi http, urllib e xml da lista de exclusão!
        "pytest",
        "unittest",
        "tkinter.test",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
    ],
    noarchive=False,
)

# --------------------------
# PYZ
# --------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --------------------------
# EXE (ONEDIR para reduzir tempo de inicialização)
# --------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],  # Vazio = modo ONEDIR (mais rápido)
    exclude_binaries=True,
    name="Study Practices",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join("resources", "Taty_s-English-Logo.ico"),
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
    name="Study Practices",
)