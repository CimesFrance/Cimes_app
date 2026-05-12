"""
Pipeline de capture : déclenchement, traitement en arrière-plan, sauvegarde.
"""

import threading
import time
import queue
from datetime import datetime
from tkinter import messagebox
import numpy as np

from src.core.segmentation import segment_and_analyze
from src.core.granulometry import calculate_granulometric_curve_with_dna
from src.core.calibration import undistort_img
from src.utils.file_manager import save_capture_data


class CapturePipeline:
    """
    Mixin pour MeasureView — gère toute la chaîne de capture/analyse.
    Prérequis : l'objet possède self.app et les labels self.segmented_label,
    self.curve_label, self.captured_label.
    """
    # pylint: disable=no-member,attribute-defined-outside-init,too-few-public-methods

    def _manual_capture(self):
        """Capture manuelle déclenchée par l'utilisateur."""

        if not self.app.camera_running:
            messagebox.showwarning(
                "Caméra non démarrée", "Veuillez démarrer la caméra d'abord."
            )
            return
        if self.is_segmenting:
            messagebox.showinfo(
                "Capture en cours", "Une capture est déjà en cours. Veuillez patienter."
            )
            return
        self.perform_capture()

    def perform_capture(self):
        """Déclenche la capture et lance l'analyse en background."""
        frame_to_analyze = self.app.last_captured_frame
        if frame_to_analyze is None:
            print("Aucune frame disponible.")
            self.last_capture_time = time.time()
            return
        if self.is_segmenting:
            print("Capture déjà en cours.")
            return
        self.is_segmenting = True
        self.last_capture_time = time.time()
        # Afficher l'image capturée avec corrections si actives
        frame_for_display = frame_to_analyze.copy()
        if (
            self.app.use_undistortion_var.get()
            and self.app.mtx is not None
            and self.app.dist is not None
        ):
            frame_for_display = undistort_img(
                self.app.dist, self.app.mtx, frame_for_display
            )
        self._update_display_label(
            self.captured_label, frame_for_display, "captured_tk_img"
        )
        self._init_queue_if_needed()
        threading.Thread(
            target=self._process_capture_in_background, args=(frame_to_analyze.copy(),)
        ).start()

    def _process_capture_in_background(self, frame_to_analyze):
        """Analyse complète en thread séparé pour ne pas bloquer l'UI."""
        try:
            processed_frame = frame_to_analyze.copy()
            if (
                self.app.use_undistortion_var.get()
                and self.app.mtx is not None
                and self.app.dist is not None
            ):
                processed_frame = undistort_img(
                    self.app.dist, self.app.mtx, processed_frame
                )
            # Coefficient de conversion pixel→mm, synchronisé avec l'onglet Paramètres
            facteur = float(self.app.facteur_conversion.get().replace(",", "."))
            print(f"[INFO] Facteur de conversion appliqué : {facteur} mm/px")
            # Segmentation : on passe facteur pour que particles_data ait les bonnes valeurs en mm
            masks, segmented_img, particles_data, _, l_min_axis, l_max_axis = (
                segment_and_analyze(processed_frame, facteur)
            )
            # l_min_axis est en pixels bruts — conversion pixels→mm
            # effectuée une seule fois ci-dessous
            tamis_exp, cumulative_raw, cumulative_corrected, minor_axes_mm = (
                calculate_granulometric_curve_with_dna(
                    particles_data,
                    l_min_axis,
                    self.app.correction_granulo["scale"].get(),
                    self.app.correction_granulo["offset"].get(),
                    facteur,
                )
            )
            self.particles_table_data = [
                {
                    "id": i + 1,
                    "minor_mm": p.get("minor_axis_mm", 0),
                    "major_mm": p.get("major_axis_mm", 0),
                }
                for i, p in enumerate(particles_data)
                if p.get("minor_axis_mm", 0) > 0.1 and p.get("major_axis_mm", 0) > 0.1
            ]
            capture_data = {
                "id": len(self.app.capture_history) + 1,
                "timestamp": datetime.now(),
                "image_raw": frame_to_analyze,
                "image_processed": processed_frame,
                "segmented_image": segmented_img,
                "masks": masks,
                "particles_data": particles_data,
                "l_min_axis": l_min_axis,
                "l_max_axis": l_max_axis,
                "l_min_axis_mm": (
                    (np.array(l_min_axis) * facteur).tolist() if l_min_axis else []
                ),
                "l_max_axis_mm": (
                    (np.array(l_max_axis) * facteur).tolist() if l_max_axis else []
                ),
                "tamis_exp": tamis_exp,
                "cumulative_raw": cumulative_raw,
                "cumulative_corrected": cumulative_corrected,
                "minor_axes_mm": minor_axes_mm,
                "particles_count": len(particles_data),
                "scale": facteur,
            }
            self.capture_queue.put(("results", capture_data))
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Erreur traitement: {e}")
            self.capture_queue.put(("error", e))

    def _init_queue_if_needed(self):
        """Initialise la file de traitement si elle n'existe pas."""
        if not hasattr(self, "capture_queue"):
            self.capture_queue = queue.Queue()
            self._check_capture_queue()

    def _check_capture_queue(self):
        """Vérifie la file de traitement et met à jour l'interface."""
        try:
            while True:
                msg_type, data = self.capture_queue.get_nowait()
                if msg_type == "results":
                    self._update_capture_results(data)
                elif msg_type == "error":
                    self._capture_error(data)
        except queue.Empty:
            pass
        if hasattr(self, "app") and self.app:
            self.app.after(100, self._check_capture_queue)

    def _update_capture_results(self, capture_data):
        """Met à jour l'interface avec les résultats (appelé dans le thread principal)."""
        self.is_segmenting = False
        self.app.capture_history.append(capture_data)
        self.app.current_capture_index = len(self.app.capture_history) - 1
        self.app.captured_count += 1
        self.app.images_count_var.set(str(self.app.captured_count))
        self.app.last_capture_time_var.set(
            capture_data["timestamp"].strftime("%Y/%m/%d %H:%M:%S")
        )
        self.app.particles_count_var.set(str(capture_data["particles_count"]))
        if capture_data["segmented_image"] is not None:
            self._update_display_label(
                self.segmented_label,
                capture_data["segmented_image"],
                "segmented_tk_img",
            )
        else:
            self.segmented_label.config(
                image="", text="Segmentation non disponible\nCellpose non installé"
            )
        if len(capture_data["tamis_exp"]) > 0:
            self._display_granulometric_curve(
                capture_data["tamis_exp"],
                capture_data["cumulative_raw"],
                (
                    capture_data["cumulative_corrected"]
                    if self.app.show_corrected_curve_var.get()
                    else None
                ),
            )
        else:
            self._display_granulometric_curve([], [])
        save_capture_data(capture_data, self.app.results_path_var.get(), self.app)
        if hasattr(self.app, "curve_view"):
            self.app.curve_view._update_capture_history_display()  # pylint: disable=protected-access
            self.app.curve_view._update_curve_view_for_capture(capture_data["id"])  # pylint: disable=protected-access
            self.app.curve_view._update_particles_table()  # pylint: disable=protected-access
            self.app.curve_view.update_statistics_display(capture_data)
        self.app.daily_data.append(capture_data)

    def _capture_error(self, error):
        """Affiche une erreur de capture."""

        self.is_segmenting = False
        error_msg = str(error)
        self.segmented_label.config(
            image="", text=f"Erreur de traitement\n{error_msg[:60]}..."
        )
        self.curve_label.config(image="", text="Analyse interrompue")
        messagebox.showerror(
            "Erreur d'analyse",
            f"Une erreur est survenue lors du traitement de la capture :\n\n{error_msg}",
        )
