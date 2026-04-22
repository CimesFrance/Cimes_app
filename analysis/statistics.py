# -*- coding: utf-8 -*-
import numpy as np

def calculer_statistiques_granulometriques(particles_data, minor_axes_mm, major_axes_mm=None):
    """
    Calcule les statistiques principales de la granulométrie.
    """
    if not particles_data or len(minor_axes_mm) == 0:
        return None
    
    stats = {}
    
    # Convertir en array numpy
    minor_sizes_mm = np.array(minor_axes_mm)
    
    # Statistiques de base pour l'axe mineur
    stats['n_particules'] = len(minor_sizes_mm)
    stats['min_mm_minor'] = float(np.min(minor_sizes_mm))
    stats['max_mm_minor'] = float(np.max(minor_sizes_mm))
    stats['moyenne_mm_minor'] = float(np.mean(minor_sizes_mm))
    
    # Statistiques pour l'axe majeur
    if major_axes_mm and len(major_axes_mm) > 0:
        # Si major_axes_mm est fourni en paramètre
        major_sizes_mm = np.array(major_axes_mm)
        stats['min_mm_major'] = float(np.min(major_sizes_mm))
        stats['max_mm_major'] = float(np.max(major_sizes_mm))
        stats['moyenne_mm_major'] = float(np.mean(major_sizes_mm))
    else:
        # Sinon, extraire des particles_data
        major_axes = []
        for particle in particles_data:
            if 'major_axis_mm' in particle:
                major_axes.append(particle['major_axis_mm'])
        
        if major_axes:
            major_sizes_mm = np.array(major_axes)
            stats['min_mm_major'] = float(np.min(major_sizes_mm))
            stats['max_mm_major'] = float(np.max(major_sizes_mm))
            stats['moyenne_mm_major'] = float(np.mean(major_sizes_mm))
        else:
            stats['min_mm_major'] = 0
            stats['max_mm_major'] = 0
            stats['moyenne_mm_major'] = 0
    
    # Percentiles pour l'axe mineur (D10, D25, D50, D75, D90)
    percentiles = [10, 25, 50, 75, 90]
    for p in percentiles:
        stats[f'D{p}_mm'] = float(np.percentile(minor_sizes_mm, p))
    
    return stats

def generer_rapport_statistique(stats):
    """Génère un rapport textuel des statistiques"""
    if not stats:
        return "Aucune statistique disponible."
    
    rapport = []
    rapport.append("📊 RAPPORT GRANULOMÉTRIQUE")
    rapport.append("=" * 40)
    rapport.append(f"Nombre de particules : {stats['n_particules']}")
    rapport.append("")
    rapport.append("📏 STATISTIQUES DE TAILLE (mm)")
    rapport.append("-" * 30)
    rapport.append(f"Min (Axe mineur) : {stats['min_mm_minor']:.2f} mm")
    rapport.append(f"Max (Axe mineur) : {stats['max_mm_minor']:.2f} mm")
    rapport.append(f"Moyenne (Axe mineur) : {stats['moyenne_mm_minor']:.2f} mm")
    rapport.append(f"Min (Axe majeur) : {stats['min_mm_major']:.2f} mm")
    rapport.append(f"Max (Axe majeur) : {stats['max_mm_major']:.2f} mm")
    rapport.append(f"Moyenne (Axe majeur) : {stats['moyenne_mm_major']:.2f} mm")
    rapport.append("")
    rapport.append("📈 PERCENTILES (mm)")
    rapport.append("-" * 30)
    rapport.append(f"D10 : {stats['D10_mm']:.2f} mm (10% plus fins)")
    rapport.append(f"D25 : {stats['D25_mm']:.2f} mm (25% plus fins)")
    rapport.append(f"D50 : {stats['D50_mm']:.2f} mm (Taille médiane)")
    rapport.append(f"D75 : {stats['D75_mm']:.2f} mm (75% plus fins)")
    rapport.append(f"D90 : {stats['D90_mm']:.2f} mm (90% plus fins)")
    
    return "\n".join(rapport)

def get_color_for_value(value, thresholds):
    """
    Retourne une couleur en fonction de la valeur et des seuils
    thresholds = [(max_value, color), ...]
    """
    for max_val, color in thresholds:
        if value <= max_val:
            return color
    return "#ef4444"  # Par défaut rouge si hors limites