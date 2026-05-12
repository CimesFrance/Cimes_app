""" 
Ce fichier contient les fonctions de correction DNA
"""
import numpy as np

def dna_correct(cumul_actuel, tamis_exp, scale=0.823, offset=8.5):
    """ 
    Correction DNA de la courbe granulométrique avec transformation linéaire.
    """
    # pylint: disable=too-many-locals, too-many-branches
    if len(cumul_actuel) == 0 or len(tamis_exp) == 0:
        return cumul_actuel
    try:
        # Convertir en numpy arrays si nécessaire
        cumulative_classes = np.array(cumul_actuel)
        tamis_exp = np.array(tamis_exp)
        # Appliquer la transformation aux tailles de tamis
        tamis_temp = tamis_exp * scale + offset
        a_list = []
        b_list = []
        # Calculer les coefficients a et b pour chaque segment
        for i in range(tamis_exp.shape[0]-1):
            denominator = tamis_temp[i+1] - tamis_temp[i]
            if denominator == 0:
                a = 0
            else:
                a = (cumulative_classes[i+1] - cumulative_classes[i]) / denominator
            b = cumulative_classes[i] - a * tamis_temp[i]
            a_list.append(a)
            b_list.append(b)
        cumulative_corrige = []
        # Appliquer la correction pour chaque tamis expérimental
        for i, elt_exp in enumerate(tamis_exp):
            if tamis_temp[0] <= elt_exp <= tamis_temp[-1]:
                j = 1
                while elt_exp > tamis_temp[j]:
                    j += 1
                cumulative_corrige.append(a_list[j-1] * elt_exp + b_list[j-1])
            else:
                if elt_exp > tamis_temp[tamis_temp.shape[0]-1]:
                    cumulative_corrige.append(a_list[-1] * elt_exp + b_list[-1])
                elif elt_exp < tamis_temp[0]:
                    cumulative_corrige.append(a_list[0] * elt_exp + b_list[0])
        # Post-traitement pour restreindre les valeurs entre 0 et 100
        cumulative_corrige = np.array(cumulative_corrige)
        cumulative_corrige = np.clip(cumulative_corrige, 0, 100)
        for i, val in enumerate(cumulative_corrige):
            if 0 <= val < cumulative_classes[0]:
                cumulative_corrige[i] = cumulative_classes[0]
            if cumulative_classes[-1] < val < 100:
                cumulative_corrige[i] = cumulative_classes[-1]
        return cumulative_corrige.tolist()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'application de la correction DNA : {e}") from e
