# app.spec - ADICIONAR ESTAS LINHAS
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

BASE_DIR = os.getcwd()

# =============================
# COLETA TODAS AS DEPENDÊNCIAS
# =============================

# Coleta dados do undetected_chromedriver
uc_data = collect_data_files('undetected_chromedriver', include_py_files=False)
selenium_data = collect_data_files('selenium', include_py_files=False)

# Hidden imports críticos
hiddenimports = [
    'undetected_chromedriver._compat',
    'undetected_chromedriver.patcher',
    'undetected_chromedriver.options',
    'undetected_chromedriver.cdp',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'websocket._app',
    'websocket._core',
    'websocket._abnf',
    'packaging.version',
    'packaging.specifiers',
    'colorama',
    'colorama.ansi',
    'typing_extensions',
    'http.cookies',
    'http.cookiejar',
    'urllib3',
    'urllib3.contrib',
    'urllib3.contrib.pyopenssl',
    'charset_normalizer',
    'sqlite3',  # ADICIONADO
    'json',     # ADICIONADO
    'pathlib',  # ADICIONADO
    'datetime', # ADICIONADO
]

# Adiciona todos os submódulos
for pkg in ['selenium', 'undetected_chromedriver', 'PySide6', 'websocket', 'sqlite3']:
    hiddenimports.extend(collect_submodules(pkg))

# Dados do projeto
datas = [
    ("ui", "ui"),
    ("core", "core"),
    ("data", "data"),
    ("resources", "resources"),
    ("scheduled_tasks", "scheduled_tasks"),
]

# Adiciona dados coletados
datas += uc_data + selenium_data

# =============================
# ANÁLISE
# =============================
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
        "tkinter.test",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "test",
        "tests",
        "__pycache__",
    ],
    noarchive=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Study Practices",
    debug=False,  # Mude para False em produção
    bootloader_ignore_signals=False,
    strip=False,
    uac_admin=True,  # IMPORTANTE: Permite criar tarefas agendadas
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Mantenha True para ver logs
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join("resources", "Taty_s-English-Logo.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="dist/Study Practices"
)