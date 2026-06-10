"""
Ce module contient les fonctions de segmentation et d'analyse des particules.
"""

import numpy as np

# Vérifier disponibilité de skimage
try:
    from skimage.measure import label, regionprops
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

# Vérifier disponibilité de Cellpose
try:
    import torch
    from cellpose import models, utils
    CELLPOSE_AVAILABLE = True
except ImportError:
    CELLPOSE_AVAILABLE = False

import cv2
from src.core.calibration import undistort_img, homo_and_pixel_conversion


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
    hsv_img = np.zeros((img.shape[0], img.shape[1], 3), np.float32)
    hsv_img[:, :, 2] = np.clip((img / 255.0 if img.max() > 1 else img) * 1.5, 0, 1)
    hues = np.linspace(0, 1, masks.max() + 1)[np.random.permutation(masks.max())]
    for n in range(int(masks.max())):
        ipix = (masks == n + 1).nonzero()
        if colors is None:
            hsv_img[ipix[0], ipix[1], 0] = hues[n]
        else:
            hsv_img[ipix[0], ipix[1], 0] = colors[n, 0]
        hsv_img[ipix[0], ipix[1], 1] = 1.0
    rgb_img = (utils.hsv_to_rgb(hsv_img) * 255).astype(np.uint8)
    return rgb_img


def segment_and_analyze(
    image,
    scale_mm_per_pixel=1.0,
    min_area_px=10,
    min_axis_px=1.0,
    use_undistortion=False,
    mtx=None,
    dist=None,
    use_homography=False,
    homo_matrix=None,
):
    """
    Segment and analyze particles in an image.

    Args:
        image (int or float, 2D or 3D array): Image of size [Ly x Lx (x nchan)].
        scale_mm_per_pixel (float, optional): Scale in mm per pixel. Defaults to 1.0.
        min_area_px (int, optional): Minimum area in pixels. Defaults to 10.
        min_axis_px (int, optional): Minimum axis in pixels. Defaults to 1.0.
        use_undistortion (bool, optional): Whether to use undistortion. Defaults to False.
        mtx (int or float, 2D array, optional): Camera matrix. Defaults to None.
        dist (int or float, 1D array, optional): Distortion coefficients. Defaults to None.
        use_homography (bool, optional): Whether to use homography. Defaults to False.
        homo_matrix (int or float, 3x3 array, optional): Homography matrix. Defaults to None.
    
    Returns:
        tuple: (masks, overlay_bgr, particles_data, flows, l_min_axis, l_max_axis)
            - masks (int, 2D array): Masks where 0=NO masks; 1,2,...=mask labels.
            - overlay_bgr (uint8, 3D array): Array of masks overlaid on grayscale image.
            - particles_data (list): List of particle data.
            - flows (int or float, 3D array): Flows.
            - l_min_axis (int or float, 1D array): Minimum axes.
            - l_max_axis (int or float, 1D array): Maximum axes.
    """
    # pylint: disable=no-member, too-many-arguments, too-many-positional-arguments
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    print("\n=== DÉBUT SEGMENTATION ===")
    if image is None:
        raise ValueError("L'image fournie pour la segmentation est nulle (None).")
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Format d'image invalide pour la segmentation : {image.shape}"
        )
    if not CELLPOSE_AVAILABLE:
        raise ImportError(
            "Le module Cellpose n'est pas installé ou n'a pas pu être chargé. "
            "Veuillez vérifier l'installation des dépendances."
        )
    # Appliquer les corrections si demandées
    processed_image = image.copy()
    if use_undistortion and mtx is not None and dist is not None:
        processed_image = undistort_img(dist, mtx, processed_image)
    if use_homography and homo_matrix is not None:
        processed_image = homo_and_pixel_conversion(processed_image, homo_matrix)
    # Suite du traitement
    rgb_img = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
    print("[OK] Image convertie en RGB")
    
    use_gpu = torch.cuda.is_available()
    print(f"[DEBUG] Torch version: {torch.__version__}")
    print(f"[DEBUG] CUDA available: {use_gpu}")
    if use_gpu:
        print(f"[DEBUG] CUDA device: {torch.cuda.get_device_name(0)}")
    
    print(f"Chargement modèle Cellpose (model_type='cyto2', GPU={use_gpu})…")
    try:
        # Utilisation de cyto2
        model = models.Cellpose(gpu=use_gpu, model_type='cyto2')
        print("[OK] Modèle chargé")
    except Exception as e:
        print(f"[ERREUR] Échec du chargement du modèle: {e}")
        raise

    # Appel Cellpose avec paramètres ajustés
    print(f"[DEBUG] Lancement de model.eval sur image de taille {rgb_img.shape}")
    try:
        # model.eval de Cellpose (wrapper)
        masks, flows, styles, diams = model.eval(
            rgb_img,
            diameter=None, # None permet à Cellpose d'estimer la taille automatiquement
            channels=[0, 0],
            flow_threshold=0.4,
            cellprob_threshold=0.0,
            resample=True # Améliore la qualité des contours
        )
        print("[OK] Segmentation faite")
    except Exception as e:
        print(f"[ERREUR] Échec de model.eval: {e}")
        raise

    unique_masks = np.unique(masks)
    num_particles = len(unique_masks) - 1
    print(f"[OK] Particules détectées par Cellpose : {num_particles}")
    # cv2.imwrite(r"C:\Users\loic.ngassa\Downloads\img_seg.png", img_seg)
    overlay = rgb_img.copy()
    if num_particles > 0:
        for mask_id in unique_masks[1:]:
            mask = masks == mask_id
            color = np.random.randint(0, 255, 3)
            overlay[mask] = color
    overlay_bgr = cv2.cvtColor(mask_overlay(rgb_img, masks), cv2.COLOR_RGB2BGR)
    # overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    # Analyse SKIMAGE avec filtrage
    particles_data = []
    l_min_axis = []
    l_max_axis = []
    if SKIMAGE_AVAILABLE and num_particles > 0:
        try:
            label_img = label(masks)
            regions = regionprops(label_img)
            print(f"[INFO] Régions détectées par skimage : {len(regions)}")
            for props in regions:
                minor = props.axis_minor_length
                major = props.axis_major_length
                # FILTRER les particules trop petites ou invalides
                if (
                    minor < min_axis_px
                    or major < min_axis_px
                    or props.area < min_area_px
                ):
                    continue
                # Stocker en pixels
                l_min_axis.append(minor)
                l_max_axis.append(major)
                # Convertir en mm
                minor_mm = minor * scale_mm_per_pixel
                major_mm = major * scale_mm_per_pixel
                particles_data.append(
                    {
                        "area": props.area,
                        "minor_axis_px": minor,
                        "major_axis_px": major,
                        "minor_axis_mm": minor_mm,
                        "major_axis_mm": major_mm,
                        "centroid": props.centroid,
                        "orientation": props.orientation,
                        "perimeter": props.perimeter,
                    }
                )
            print(f"[OK] Particules valides après filtrage : {len(particles_data)}")
            if l_min_axis:
                print(
                    f"[OK] Axe mineur min/max : "
                    f"{np.min(l_min_axis):.1f}/{np.max(l_min_axis):.1f} px"
                )
                print(
                    f"[OK] Axe majeur min/max : "
                    f"{np.min(l_max_axis):.1f}/{np.max(l_max_axis):.1f} px"
                )
            else:
                print("[ATTENTION] Aucune particule valide après filtrage")
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'analyse des particules avec skimage : {e}"
            ) from e
    print("=== FIN SEGMENTATION ===")
    return masks, overlay_bgr, particles_data, flows, l_min_axis, l_max_axis
