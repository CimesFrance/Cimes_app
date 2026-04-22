# -*- coding: utf-8 -*-
import cv2
import numpy as np
import traceback
from cellpose import utils

# Vérifier disponibilité de skimage
try:
    from skimage.measure import label, regionprops
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

# Vérifier disponibilité de Cellpose
try:
    from cellpose import models
    CELLPOSE_AVAILABLE = True
except ImportError:
    CELLPOSE_AVAILABLE = False

from core.calibration import undistort_img, homo_and_pixel_conversion

def mask_overlay(img, masks, colors=None):
    """Overlay masks on image (set image to grayscale).

    Args:
        img (int or float, 2D or 3D array): Image of size [Ly x Lx (x nchan)].
        masks (int, 2D array): Masks where 0=NO masks; 1,2,...=mask labels.
        colors (int, 2D array, optional): Size [nmasks x 3], each entry is a color in 0-255 range.

    Returns:
        RGB (uint8, 3D array): Array of masks overlaid on grayscale image.
    """
    if colors is not None:
        if colors.max() > 1:
            colors = np.float32(colors)
            colors /= 255
        colors = utils.rgb_to_hsv(colors)
    if img.ndim > 2:
        img = img.astype(np.float32).mean(axis=-1)
    else:
        img = img.astype(np.float32)

    HSV = np.zeros((img.shape[0], img.shape[1], 3), np.float32)
    HSV[:, :, 2] = np.clip((img / 255. if img.max() > 1 else img) * 1.5, 0, 1)
    hues = np.linspace(0, 1, masks.max() + 1)[np.random.permutation(masks.max())]
    for n in range(int(masks.max())):
        ipix = (masks == n + 1).nonzero()
        if colors is None:
            HSV[ipix[0], ipix[1], 0] = hues[n]
        else:
            HSV[ipix[0], ipix[1], 0] = colors[n, 0]
        HSV[ipix[0], ipix[1], 1] = 1.0
    RGB = (utils.hsv_to_rgb(HSV) * 255).astype(np.uint8)
    return RGB

def segment_and_analyze(image, scale_mm_per_pixel=0.1, min_area_px=10, min_axis_px=1.0,
                       use_undistortion=False, mtx=None, dist=None,
                       use_homography=False, homo_matrix=None):
    print("\n=== DÉBUT SEGMENTATION ===")

    if image is None:
        print("[ERREUR] Image None")
        return None, None, [], None, [], []

    if len(image.shape) != 3 or image.shape[2] != 3:
        print("[ERREUR] Image invalide")
        return None, None, [], None, [], []

    if not CELLPOSE_AVAILABLE:
        print("[ERREUR] Cellpose non installé")
        return None, None, [], None, [], []

    try:
        # Appliquer les corrections si demandées
        processed_image = image.copy()
        
        if use_undistortion and mtx is not None and dist is not None:
            processed_image = undistort_img(dist, mtx, processed_image)
        
        if use_homography and homo_matrix is not None:
            processed_image = homo_and_pixel_conversion(processed_image, homo_matrix)
        
        # Suite du traitement
        rgb_img = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
        print("[OK] Image convertie en RGB")

        print("Chargement modèle Cellpose GPU…")
        model = models.CellposeModel(gpu=True)
        print("[OK] Modèle chargé")

        # Appel Cellpose avec paramètres ajustés
        masks, flows, styles = model.eval(
            rgb_img,
            diameter=80,
            channels=[0, 0],
            flow_threshold=0.4,
            cellprob_threshold=0.0
        )
        print("[OK] Segmentation faite")

        unique_masks = np.unique(masks)
        num_particles = len(unique_masks) - 1
        print(f"[OK] Particules détectées par Cellpose : {num_particles}")

        overlay = rgb_img.copy()

        if num_particles > 0:
            for mask_id in unique_masks[1:]:
                mask = masks == mask_id
                color = np.random.randint(0, 255, 3)
                overlay[mask] = color
        overlay_bgr = cv2.cvtColor(mask_overlay(rgb_img,masks), cv2.COLOR_RGB2BGR)
        # overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)

        # Analyse SKIMAGE avec filtrage
        particles_data = []
        L_min_axis = []
        L_max_axis = []

        if SKIMAGE_AVAILABLE and num_particles > 0:
            try:
                label_img = label(masks)
                regions = regionprops(label_img)
                
                print(f"[INFO] Régions détectées par skimage : {len(regions)}")

                for props in regions:
                    minor = props.axis_minor_length
                    major = props.axis_major_length
                    
                    # FILTRER les particules trop petites ou invalides
                    if minor < min_axis_px or major < min_axis_px or props.area < min_area_px:
                        continue
                    
                    # Stocker en pixels
                    L_min_axis.append(minor)
                    L_max_axis.append(major)
                    
                    # Convertir en mm
                    minor_mm = minor * scale_mm_per_pixel
                    major_mm = major * scale_mm_per_pixel

                    particles_data.append({
                        "area": props.area,
                        "minor_axis_px": minor,
                        "major_axis_px": major,
                        "minor_axis_mm": minor_mm,
                        "major_axis_mm": major_mm,
                        "centroid": props.centroid,
                        "orientation": props.orientation,
                        "perimeter": props.perimeter
                    })

                print(f"[OK] Particules valides après filtrage : {len(particles_data)}")
                if L_min_axis:
                    print(f"[OK] Axe mineur min/max : {np.min(L_min_axis):.1f}/{np.max(L_min_axis):.1f} px")
                    print(f"[OK] Axe majeur min/max : {np.min(L_max_axis):.1f}/{np.max(L_max_axis):.1f} px")
                else:
                    print("[ATTENTION] Aucune particule valide après filtrage")

            except Exception as e:
                print(f"[ERREUR analyse skimage] {e}")

        print("=== FIN SEGMENTATION ===")
        return masks, overlay_bgr, particles_data, flows, L_min_axis, L_max_axis

    except Exception as e:
        print(f"[ERREUR CRITIQUE] {e}")
        traceback.print_exc()
        return None, None, [], None, [], []

def create_ellipse_visualization(rgb_img, masks, scale_mm_per_pixel=0.1):
    """Crée une visualisation avec les ellipses des particules"""
    if not SKIMAGE_AVAILABLE:
        return None, [], []
    
    try:
        import math
        import matplotlib.pyplot as plt
        from matplotlib.patches import Ellipse
        
        label_img = label(masks)
        regions = regionprops(label_img)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(rgb_img, cmap=plt.cm.gray)
        
        L_min_axis = []
        L_max_axis = []
        
        for props in regions:
            # Stocker les dimensions
            L_min_axis.append(props.axis_minor_length)
            L_max_axis.append(props.axis_major_length)
            
            # Centroid et orientation
            y0, x0 = props.centroid
            orientation = props.orientation
            
            # Dessiner l'ellipse
            ellipse_patch = Ellipse(
                (x0, y0),
                width=props.axis_major_length,
                height=props.axis_minor_length,
                angle=90 - np.degrees(orientation),
                edgecolor='blue',
                facecolor='none',
                linewidth=0.75,
                alpha=0.7
            )
            ax.add_patch(ellipse_patch)
            
            # Marquer le centre
            ax.plot(x0, y0, '.r', markersize=2)
        
        ax.set_title(f"Ellipses des particules ({len(regions)} particules)")
        ax.axis('off')
        
        # Sauvegarder dans un buffer
        from io import BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close(fig)
        
        # Convertir en image OpenCV
        from PIL import Image
        pil_img = Image.open(buf)
        cv2_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        return cv2_img, L_min_axis, L_max_axis
        
    except Exception as e:
        print(f"[ERREUR visualisation ellipses] {e}")
        return None, [], []