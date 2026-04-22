# -*- coding: utf-8 -*-
# Ce fichier contient des fonctions supplémentaires pour l'analyse des particules
# Pour l'instant, il est vide mais prêt pour des extensions futures

def filter_particles_by_size(particles_data, min_size_mm=0.1, max_size_mm=100):
    """Filtre les particules par taille"""
    filtered = []
    for particle in particles_data:
        minor = particle.get('minor_axis_mm', 0)
        major = particle.get('major_axis_mm', 0)
        if min_size_mm <= minor <= max_size_mm and min_size_mm <= major <= max_size_mm:
            filtered.append(particle)
    return filtered

def calculate_aspect_ratios(particles_data):
    """Calcule les rapports d'aspect des particules"""
    aspect_ratios = []
    for particle in particles_data:
        minor = particle.get('minor_axis_mm', 0)
        major = particle.get('major_axis_mm', 0)
        if major > 0:
            aspect_ratio = minor / major
            aspect_ratios.append(aspect_ratio)
    return aspect_ratios