"""
Ce fichier contient les fonctions de calcul de la granulométrie
sous forme de courbes cumulées.
"""

import numpy as np
from src.core.dna_correction import dna_correct


def calculate_granulometric_curve_with_dna(
    particles_data, l_min_axis, scale, offset, scale_mm_per_pixel=1.0
):
    """
    Calcule la courbe granulométrique avec correction DNA.

    Returns:
        tamis_exp: tailles des tamis
        cumulative_raw: pourcentages cumulés bruts
        cumulative_corrected: pourcentages cumulés corrigés
        l_min_axis_mm: axes mineurs en mm
    """
    if not particles_data or not l_min_axis:
        return [], [], [], []
    try:
        # Convertir l_min_axis de pixels en mm
        l_min_axis_mm = np.array(l_min_axis) * scale_mm_per_pixel
        # Tailles des tamis expérimentaux
        tamis_exp = np.array([4, 22.4, 25, 31.5, 40, 50, 63, 80])
        # Compter le nombre de particules par tamis
        classes = np.zeros(len(tamis_exp))
        for i, t in enumerate(tamis_exp):
            classes[i] = np.sum(l_min_axis_mm <= t)
        # Conversion en % cumulatif
        if len(l_min_axis_mm) > 0:
            cumulative_raw = classes * 100 / len(l_min_axis_mm)
            cumulative_raw[-1] = 100
        else:
            cumulative_raw = np.zeros(len(tamis_exp))
        # Appliquer la correction DNA
        cumulative_corrected = dna_correct(cumulative_raw, tamis_exp, scale, offset)
        print("[OK] Courbe granulométrique avec correction DNA calculée")
        return (
            tamis_exp.tolist(),
            cumulative_raw.tolist(),
            cumulative_corrected,
            l_min_axis_mm.tolist(),
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors du calcul de la granulométrie : {e}") from e
