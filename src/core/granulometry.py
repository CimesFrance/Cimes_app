# -*- coding: utf-8 -*-
import numpy as np
from src.core.dna_correction import dna_correct

def calculate_granulometric_curve_with_dna(particles_data, L_min_axis, scale, offset, scale_mm_per_pixel=1.0):
    """
    Calcule la courbe granulométrique avec correction DNA.
    
    Returns:
        tamis_exp: tailles des tamis
        cumulative_raw: pourcentages cumulés bruts
        cumulative_corrected: pourcentages cumulés corrigés
        L_min_axis_mm: axes mineurs en mm
    """
    if not particles_data or not L_min_axis:
        return [], [], [], []

    try:
        # Convertir L_min_axis de pixels en mm
        L_min_axis_mm = np.array(L_min_axis) * scale_mm_per_pixel
        
        # Tailles de tamis
        tamis_exp = np.array([4, 22.4, 25, 31.5, 40, 50, 63, 80])
        classes = np.zeros(len(tamis_exp))

        for i, t in enumerate(tamis_exp):
            classes[i] = np.sum(L_min_axis_mm <= t)

        # Conversion en % cumulatif
        if len(L_min_axis_mm) > 0:
            cumulative_raw = classes * 100 / len(L_min_axis_mm)
            cumulative_raw[-1] = 100
        else:
            cumulative_raw = np.zeros(len(tamis_exp))
        
        # Appliquer la correction DNA
        cumulative_corrected = dna_correct(cumulative_raw, tamis_exp, scale, offset)
        
        print(f"[OK] Courbe granulométrique avec correction DNA calculée")
        return tamis_exp.tolist(), cumulative_raw.tolist(), cumulative_corrected, L_min_axis_mm.tolist()

    except Exception as e:
        print(f"[ERREUR calcul granulométrie avec DNA] {e}")
        return [], [], [], []