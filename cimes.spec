# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# cimes.spec — Build PyInstaller (OneDir + OneFile)
# Généré automatiquement — ne packager que les bibliothèques nécessaires
# ============================================================
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
import os

# ============================================================
# Modèles Cellpose — bundler dans l'exécutable si présents
# ============================================================
cellpose_models_src = os.path.join(os.path.expanduser('~'), '.cellpose', 'models')
cellpose_model_files = []
if os.path.isdir(cellpose_models_src):
    for fname in os.listdir(cellpose_models_src):
        fpath = os.path.join(cellpose_models_src, fname)
        if os.path.isfile(fpath):
            cellpose_model_files.append((fpath, '.cellpose/models'))
    print(f"[SPEC] Modèles Cellpose trouvés : {len(cellpose_model_files)}")
else:
    print(f"[SPEC] ATTENTION : Dossier de modèles Cellpose non trouvé : {cellpose_models_src}")

# ============================================================
# Données de l'application (assets, modules, mesure, config)
# ============================================================
datas = [
    ('assets', 'assets'),
    ('modules', 'modules'),
    ('mesure', 'mesure'),
    ('mesure_config.json', '.'),
]

# Modèles Cellpose
datas += cellpose_model_files

# Données Cellpose (fichiers internes du package)
datas += collect_data_files('cellpose')
datas += copy_metadata('cellpose')

# Torch (DLLs et fichiers de données nécessaires)
datas += collect_data_files('torch')
datas += copy_metadata('torch')

# Scikit-image (haarcascades, etc.)
datas += collect_data_files('skimage')

# Métadonnées pip nécessaires au runtime
datas += copy_metadata('numpy')
datas += copy_metadata('openpyxl')
datas += copy_metadata('pandas')
datas += copy_metadata('reportlab')
datas += copy_metadata('Pillow')
datas += copy_metadata('scipy')
datas += copy_metadata('scikit-image')
datas += copy_metadata('opencv-python')

# Données openpyxl (templates XML)
datas += collect_data_files('openpyxl')

# Données matplotlib (backends, polices)
datas += collect_data_files('matplotlib')
datas += copy_metadata('matplotlib')

# ============================================================
# Hidden imports — UNIQUEMENT ce qui est réellement utilisé
# ============================================================
hiddenimports = []

# --- Cellpose & Torch (discovery automatique) ---
hiddenimports += collect_submodules('cellpose')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchvision')

# --- NumPy / SciPy / Scikit-image ---
hiddenimports += [
    'numpy',
    'numpy.core._multiarray_umath',
    'numpy.core._ufunc_config',
    'scipy',
    'scipy.special._ufuncs',
    'scipy.spatial',
    'scipy.ndimage',
    'scipy.interpolate',
    'scipy.interpolate.interpolate',
    'scipy.optimize',
    'scipy._lib.array_api_compat.numpy',
    # unittest est requis en interne par scipy — NE PAS EXCLURE
    'unittest',
    'unittest.mock',
    'skimage',
    'skimage.measure',
    'skimage.morphology',
    'skimage.filters',
    'skimage.segmentation',
    'skimage.color',
    'skimage.io',
]

# --- OpenCV ---
hiddenimports += ['cv2']

# --- PIL / Pillow ---
hiddenimports += [
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
]

# --- Matplotlib ---
hiddenimports += [
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
]

# --- Pandas ---
hiddenimports += ['pandas', 'pandas.io.formats.excel']

# --- ReportLab ---
hiddenimports += [
    'reportlab',
    'reportlab.lib.pagesizes',
    'reportlab.lib.colors',
    'reportlab.lib.styles',
    'reportlab.platypus',
    'reportlab.platypus.doctemplate',
    'reportlab.platypus.paragraph',
    'reportlab.platypus.tables',
    'reportlab.lib.units',
]

# --- openpyxl ---
hiddenimports += collect_submodules('openpyxl')
hiddenimports += ['et_xmlfile']

# --- Numba / llvmlite (utilisés par Cellpose) ---
hiddenimports += ['numba', 'llvmlite', 'llvmlite.binding']

# --- fastremap (utilisé par Cellpose) ---
hiddenimports += ['fastremap']

# --- email (utilisé par email_sender.py) ---
hiddenimports += [
    'smtplib',
    'email',
    'email.message',
    'email.mime',
    'email.mime.multipart',
    'email.mime.text',
    'email.mime.base',
    'email.encoders',
]

# --- tkinter ---
hiddenimports += ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox']

# --- Stdlib couramment manqués par PyInstaller ---
hiddenimports += [
    'json',
    'zipfile',
    'shutil',
    'pathlib',
    'logging',
    'threading',
    'subprocess',
    'traceback',
    'warnings',
]

# ============================================================
# Exclusions explicites (bibliothèques NON utilisées)
# ============================================================
excludes = [
    # Deep learning frameworks non utilisés
    'tensorflow',
    'tensorboard',
    'tensorflow_core',
    'keras',
    'jax',
    'flax',
    # Notebooks / IPython
    'notebook',
    'ipython',
    'ipykernel',
    'ipywidgets',
    'jupyter',
    'jupyter_client',
    'jupyter_core',
    'nbformat',
    'nbconvert',
    'nbclassic',
    # Tests
    'pytest',
    # Outils de dev
    'pylint',
    'black',
    'mypy',
    'setuptools',
    'pip',
    'wheel',
    # Web / serveur
    'django',
    'flask',
    'fastapi',
    'aiohttp',
    'tornado',
    'requests',
    'urllib3',
    # Qt (on utilise tkinter)
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',
    # Base de données
    'sqlite3',
    'sqlalchemy',
    'psycopg2',
    'pymysql',
    # Autres inutiles
    'docutils',
    'sphinx',
    'cryptography',
    'paramiko',
    'boto3',
    'botocore',
    'google',
    'grpc',
    'protobuf',
    'xml.etree.ElementTree',  # garder que si vraiment pas utilisé
    'multiprocessing.popen_spawn_win32',
    'distutils',
    'pkg_resources._vendor',
]

# ============================================================
# Configuration PyInstaller
# ============================================================
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_cellpose.py'],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================
# OneDir — dossier avec un EXE + toutes les DLLs séparées
# Avantage : démarrage rapide, facile à déboguer
# ============================================================
exe_dir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CimesApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX désactivé — évite la corruption des DLLs Torch
    console=False,      # Pas de console (mode GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\logo.png',
)

coll = COLLECT(
    exe_dir,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CimesApp_Dir',
)

# ============================================================
# OneFile — exécutable unique auto-extractible
# Avantage : distribution simple (un seul fichier)
# ============================================================
exe_file = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CimesApp_File',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX désactivé — évite la corruption des DLLs Torch
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # Pas de console (mode GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\logo.png',
)
