"""
Runtime hook PyInstaller — Cellpose & Torch
Ce fichier est exécuté AVANT tout import de l'application.
Il configure les chemins nécessaires pour que Cellpose trouve ses modèles
dans le bundle PyInstaller et que Torch charge ses DLLs correctement.
"""
import os
import sys


def _get_bundle_dir():
    """Retourne le répertoire de base du bundle PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


bundle_dir = _get_bundle_dir()

# --- 1. Chemins des modèles Cellpose ---
# Les modèles sont bundlés dans : _MEIPASS/.cellpose/models/
cellpose_models_dir = os.path.join(bundle_dir, '.cellpose', 'models')
if os.path.isdir(cellpose_models_dir):
    os.environ['CELLPOSE_LOCAL_MODELS_PATH'] = cellpose_models_dir
    print(f"[HOOK] CELLPOSE_LOCAL_MODELS_PATH => {cellpose_models_dir}")
else:
    # Fallback : utiliser le répertoire home de l'utilisateur
    home_models = os.path.join(os.path.expanduser('~'), '.cellpose', 'models')
    os.environ['CELLPOSE_LOCAL_MODELS_PATH'] = home_models
    print(f"[HOOK] CELLPOSE_LOCAL_MODELS_PATH (fallback) => {home_models}")

# --- 2. DLLs Torch CUDA ---
# Ajouter les chemins des DLLs Torch pour éviter WinError 1114
torch_lib_paths = [
    os.path.join(bundle_dir, 'torch', 'lib'),
    os.path.join(bundle_dir, 'torch', 'bin'),
]
for torch_path in torch_lib_paths:
    if os.path.isdir(torch_path):
        print(f"[HOOK] Ajout DLL path: {torch_path}")
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(torch_path)
            except Exception as e:
                print(f"[HOOK] Warning add_dll_directory: {e}")
        # Ajouter aussi au PATH pour compatibilité
        os.environ['PATH'] = torch_path + os.pathsep + os.environ.get('PATH', '')

# --- 3. Variables d'environnement Torch ---
# Forcer Torch à utiliser les DLLs bundlées
if 'TORCH_HOME' not in os.environ:
    torch_home = os.path.join(bundle_dir, 'torch_home')
    os.environ['TORCH_HOME'] = torch_home

print(f"[HOOK] Bundle dir: {bundle_dir}")
print(f"[HOOK] Runtime hook Cellpose chargé avec succès")
