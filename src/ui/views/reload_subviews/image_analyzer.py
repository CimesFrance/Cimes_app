# -*- coding: utf-8 -*-
"""
Analyseur d'images existantes : chargement, segmentation, affichage.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import traceback
import threading
from PIL import Image, ImageTk
import cv2
import numpy as np

from src.ui.widgets.ui_utils import COLOR_CARD_BG, COLOR_STAT_BAD
from src.core.segmentation import segment_and_analyze
from src.core.granulometry import calculate_granulometric_curve_with_dna


class ImageAnalyzer:
    """
    Mixin pour ReloadView — gestion du chargement et de l'analyse d'images.
    """
    # pylint: disable=no-member,attribute-defined-outside-init,too-few-public-methods
    def _browse_and_analyze_image(self):
        file_path = filedialog.askopenfilename(
            parent=self.frame,
            title="Sélectionner une image à analyser",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if file_path:
            self.loaded_image_path = file_path
            display_path = (
                file_path if len(file_path) <= 40 else "..." + file_path[-40:]
            )
            self.selected_path_label.config(text=display_path)
            self.analyze_btn.config(state="normal")
            self._display_image_preview(file_path)

    def _display_image_preview(self, image_path):
        """ Affichage de l'aperçu de l'image dans la colonne latérale"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Impossible de lire l'image")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            self._clear_segmented_tab()
            self._clear_curve_tab()
            self.segmented_label.config(
                text="Image chargée - Cliquez sur 'Analyser' pour la segmentation"
            )
            self._display_thumbnail_in_sidebar(pil_image, image_path, image.shape)
            self.loaded_image_data = image
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._display_error_in_sidebar(f"Erreur de chargement:\n{str(e)}")

    def _display_thumbnail_in_sidebar(self, pil_image, image_path, image_shape):
        """ Affichage de l'aperçu de l'image dans la colonne latérale"""
        for widget in self.reload_left_panel.winfo_children():
            widget.destroy()
        img_frame = tk.Frame(self.reload_left_panel, bg=COLOR_CARD_BG)
        img_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(
            img_frame,
            text="Aperçu de l'image",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 10))
        max_w, max_h = 280, 200
        ratio = min(max_w / pil_image.width, max_h / pil_image.height)
        resized = pil_image.resize(
            (int(pil_image.width * ratio), int(pil_image.height * ratio)),
            Image.Resampling.LANCZOS,
        )
        tk_image = ImageTk.PhotoImage(resized)
        self.reload_image_preview = tk_image
        img_lbl = tk.Label(img_frame, image=tk_image, bg=COLOR_CARD_BG)
        img_lbl.pack()
        img_lbl.image = tk_image
        info_frame = tk.Frame(img_frame, bg=COLOR_CARD_BG)
        info_frame.pack(fill="x", pady=(10, 0))
        file_name = os.path.basename(image_path)
        if len(file_name) > 25:
            file_name = file_name[:22] + "..."
        tk.Label(
            info_frame,
            text=f"Fichier: {file_name}",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 9),
        ).pack()
        tk.Label(
            info_frame,
            text=f"Taille: {image_shape[1]}×{image_shape[0]} px",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 9),
        ).pack()

    def _display_error_in_sidebar(self, error_message):
        """ Affichage d'un message d'erreur dans la colonne latérale"""
        for widget in self.reload_left_panel.winfo_children():
            widget.destroy()
        tk.Label(
            self.reload_left_panel,
            text=error_message,
            bg=COLOR_CARD_BG,
            fg=COLOR_STAT_BAD,
            font=("Segoe UI", 10),
        ).pack(expand=True)

    def _clear_segmented_tab(self):
        """ Nettoyage de l'onglet segmenté """
        for widget in self.segmented_image_container.winfo_children():
            widget.destroy()
        self.segmented_label = tk.Label(
            self.segmented_image_container,
            text="Aucune image segmentée disponible",
            bg=COLOR_CARD_BG,
            fg="#666",
            font=("Segoe UI", 12),
        )
        self.segmented_label.pack(expand=True)

    def _clear_curve_tab(self):
        """ Nettoyage de l'onglet courbe """
        for widget in self.reload_curve_frame.winfo_children():
            widget.destroy()
        self.curve_label = tk.Label(
            self.reload_curve_frame,
            text="Aucune courbe disponible",
            bg=COLOR_CARD_BG,
            fg="#666",
            font=("Segoe UI", 12),
        )
        self.curve_label.pack(expand=True)

    def _analyze_loaded_image(self):
        """ Lancement de l'analyse de l'image chargée """
        if not self.loaded_image_path or self.loaded_image_data is None:
            messagebox.showwarning(
                "Attention", "Veuillez d'abord sélectionner une image."
            )
            return
        try:
            facteur = float(self.app.facteur_conversion.get().replace(",", "."))
            self.analyze_btn.config(state="disabled", text="Analyse en cours...")
            threading.Thread(
                target=self._process_loaded_image,
                args=(self.loaded_image_data.copy(), facteur),
            ).start()
        except ValueError:
            messagebox.showerror("Erreur", "Échelle invalide. Vérifiez les paramètres.")
            self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")

    def _process_loaded_image(self, image, facteur):
        """ Traitement de l'image chargée"""
        # pylint: disable=too-many-locals
        try:
            processed_frame = image.copy()
            # Segmentation : on passe facteur pour que particles_data ait les bonnes valeurs en mm
            masks, segmented_img, particles_data, _, l_min_axis, l_max_axis = (
                segment_and_analyze(processed_frame, facteur)
            )
            # l_min_axis est en pixels bruts — conversion pixels→mm faite ci-dessous
            tamis_exp, cumulative_raw, cumulative_corrected, minor_axes_mm = (
                calculate_granulometric_curve_with_dna(
                    particles_data,
                    l_min_axis,
                    self.app.correction_granulo["scale"].get(),
                    self.app.correction_granulo["offset"].get(),
                    facteur,
                )
            )
            capture_data = {
                "timestamp": datetime.now(),
                "image_raw": image,
                "image_processed": processed_frame,
                "segmented_image": segmented_img,
                "masks": masks,
                "particles_data": particles_data,
                "L_min_axis": l_min_axis,
                "L_max_axis": l_max_axis,
                "L_min_axis_mm": (
                    (np.array(l_min_axis) * facteur).tolist() if l_min_axis else []
                ),
                "L_max_axis_mm": (
                    (np.array(l_max_axis) * facteur).tolist() if l_max_axis else []
                ),
                "tamis_exp": tamis_exp,
                "cumulative_raw": cumulative_raw,
                "cumulative_corrected": cumulative_corrected,
                "minor_axes_mm": minor_axes_mm,
                "particles_count": len(particles_data),
                "scale": facteur,
                "source": "loaded",
            }
            self.app.after(0, lambda: self._display_loaded_results(capture_data))
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"Erreur d'analyse: {str(e)}"
            self.app.after(0, lambda: self._display_loaded_error(error_msg))
            traceback.print_exc()

    def _display_loaded_results(self, capture_data):
        """ Affichage des résultats de l'analyse de l'image chargée"""
        self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")
        self.current_reload_capture = capture_data
        self._display_segmented_image(capture_data["segmented_image"])
        self._show_loaded_curve(capture_data)
        messagebox.showinfo(
            "Analyse terminée",
            f"L'analyse est terminée.\n{capture_data['particles_count']} particules détectées.",
        )

    def _display_segmented_image(self, segmented_img):
        """ Affichage de l'image segmentée """
        if segmented_img is None:
            self.segmented_label.config(text="Segmentation non disponible")
            return
        try:
            for widget in self.segmented_image_container.winfo_children():
                widget.destroy()
            if segmented_img.ndim == 3 and segmented_img.shape[2] == 3:
                cv2image = cv2.cvtColor(segmented_img, cv2.COLOR_BGR2RGB)
            elif segmented_img.ndim == 3:
                cv2image = segmented_img
            else:
                cv2image = cv2.cvtColor(segmented_img, cv2.COLOR_GRAY2RGB)
            pil_img = Image.fromarray(cv2image)
            canvas_frame = tk.Frame(self.segmented_image_container, bg=COLOR_CARD_BG)
            canvas_frame.pack(fill="both", expand=True)
            canvas = tk.Canvas(canvas_frame, bg=COLOR_CARD_BG, highlightthickness=0)
            h_scrollbar = ttk.Scrollbar(
                canvas_frame, orient="horizontal", command=canvas.xview
            )
            v_scrollbar = ttk.Scrollbar(
                canvas_frame, orient="vertical", command=canvas.yview
            )
            canvas.configure(
                xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set
            )
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            canvas_frame.grid_rowconfigure(0, weight=1)
            canvas_frame.grid_columnconfigure(0, weight=1)
            self.segmented_tk_img = ImageTk.PhotoImage(pil_img)
            canvas.create_image(0, 0, anchor="nw", image=self.segmented_tk_img)
            canvas.image = self.segmented_tk_img
            canvas.config(scrollregion=canvas.bbox("all"))
            canvas.bind_all(
                "<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            tk.Label(
                self.segmented_image_container,
                text=f"Erreur d'affichage:\n{str(e)}",
                bg=COLOR_CARD_BG,
                fg=COLOR_STAT_BAD,
                font=("Segoe UI", 10),
            ).pack(expand=True)

    def _display_loaded_error(self, error_msg):
        """ Affichage de l'erreur d'analyse """
        self.analyze_btn.config(state="normal", text="🔬 Analyser l'image")
        self._clear_segmented_tab()
        self.segmented_label.config(text=f"❌ Erreur d'analyse\n{error_msg}")
        self._clear_curve_tab()
        self.curve_label.config(text=f"❌ Erreur d'analyse\n{error_msg}")
