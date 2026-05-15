# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
import os

# ============================================================
# Modèles Cellpose — à bundler directement dans l'exécutable
# ============================================================
cellpose_models_src = os.path.join(
    os.path.expanduser('~'), '.cellpose', 'models'
)

# Vérification des fichiers de modèle présents
cellpose_model_files = []
if os.path.isdir(cellpose_models_src):
    for fname in os.listdir(cellpose_models_src):
        fpath = os.path.join(cellpose_models_src, fname)
        if os.path.isfile(fpath):
            cellpose_model_files.append((fpath, '.cellpose/models'))
    print(f"[SPEC] Modèles Cellpose trouvés : {[f[0] for f in cellpose_model_files]}")
else:
    print(f"[SPEC] ATTENTION : Dossier de modèles Cellpose non trouvé : {cellpose_models_src}")

# ============================================================
# Données de l'application
# ============================================================
datas = [
    ('assets', 'assets'),
    ('modules', 'modules'),
    ('mesure', 'mesure'),
    ('mesure_config.json', '.'),
]

# Ajouter les modèles Cellpose (CRITIQUE pour la segmentation)
datas += cellpose_model_files

# Cellpose needs its data and metadata
datas += collect_data_files('cellpose')
datas += copy_metadata('cellpose')

# Torch data and metadata
datas += collect_data_files('torch')
datas += copy_metadata('torch')

# Skimage and others
datas += collect_data_files('skimage')
datas += copy_metadata('numpy')
datas += copy_metadata('openpyxl')
datas += copy_metadata('pandas')
datas += collect_data_files('openpyxl')


# ============================================================
# Hidden imports
# ============================================================
hiddenimports = collect_submodules('cellpose')
hiddenimports += collect_submodules('torch')
hiddenimports += [
    'numpy', 'cv2', 'PIL', 'pandas', 'scipy', 'skimage',
    'skimage.measure', 'skimage.morphology', 'skimage.filters',
    'reportlab', 'numba', 'llvmlite',
    'torch', 'torch.nn', 'torch.nn.functional',
    'torchvision', 'fastremap', 'ncolor',
    'cellpose.models', 'cellpose.core', 'cellpose.utils',
    'cellpose.dynamics', 'cellpose.transforms', 'cellpose.io',
    'cellpose.resnet_torch', 'cellpose.denoise',
    'cellpose.neurips_loss_2022', 'cellpose.transforms',
]
hiddenimports += collect_submodules('openpyxl')
hiddenimports += ['et_xmlfile']




block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_cellpose.py'],  # <- CRITIQUE : hook pour Cellpose
    excludes=['tensorboard', 'tensorflow', 'notebook', 'ipython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================
# OneDir config
# ============================================================
exe_dir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CimesApp_Dir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX désactivé pour éviter corruption DLLs Torch
    console=False,  # Console désactivée pour la version finale
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\logo.png'],
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
# OneFile config
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
    upx=False,  # UPX désactivé pour éviter corruption DLLs Torch
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Console désactivée pour la version finale
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\logo.png'],
)
