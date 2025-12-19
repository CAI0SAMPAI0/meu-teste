import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

BASE_DIR = os.getcwd()

# --------------------------
# Forçar inclusão dos módulos essenciais
# --------------------------
hiddenimports = (
    collect_submodules("PySide6") +
    collect_submodules("selenium") +
    collect_submodules("undetected_chromedriver") +
    ["email"] 
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
        "pytest",
        "unittest",
        "http",
        "xml",
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
# EXE
# --------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="WhatsAuto",
    debug=False,
    strip=False,
    upx=True,
    console=False,  # sem console
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
