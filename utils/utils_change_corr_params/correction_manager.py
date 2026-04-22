import numpy as np
from scipy.interpolate import interp1d


def inv_correct(tamis_act,scale_act,offset_act):
    """Retorune l'axe des x de la courbe originale selon les paramètres de correction actuels"""
    return list((np.array(tamis_act)-offset_act) / scale_act)

def correct(tamis_act,scale_nv,offset_nv):
    """Retorune l'axe des x de la courbe originale modifiée selon les nouveaux paramètres de correction"""
    return list(np.array(tamis_act)*scale_nv+offset_nv)

def calc_erreur(tamis_corrigee,cumulatif_corrigee,tamis_pratique,cumulatif_pratique):
        Xfine = np.linspace(min(tamis_pratique), max(tamis_pratique), 300)
        exp_interp = interp1d(tamis_pratique, cumulatif_pratique, kind='linear')
        y_exp_interp = exp_interp(Xfine)
        # Interpolation cumulatif_actuel
        corr_interp = interp1d(tamis_corrigee, cumulatif_corrigee, kind='linear',fill_value="extrapolate")
        y_corr_interp = corr_interp(Xfine)
        # interpolation des valeurs corrigées
        # erreur 2D
        dx = Xfine - Xfine   # Xfine vs Xfine → pas d’écart sur X
        dy = y_corr_interp - y_exp_interp
        return round(np.sum(dy**2) / 300,3)

def erreur_minim(params_correct,tamis_originale,cumulatif_originale,tamis_pratique,cumulatif_pratique):
    scale , offset = params_correct
    tamis_corr = tamis_originale * scale + offset
    Xfine = np.linspace(min(tamis_pratique), max(tamis_pratique), 300)
    corr_interp = interp1d(tamis_corr, cumulatif_originale,kind='linear',fill_value="extrapolate")
    cumul_corr_interp = corr_interp(Xfine)
    prat_interp = interp1d(tamis_pratique, cumulatif_pratique,kind='linear')
    cumul_prat_interp = prat_interp(Xfine)
    dy = cumul_corr_interp - cumul_prat_interp
    return np.sum(dy**2)