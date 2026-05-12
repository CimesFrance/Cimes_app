"""
Vue Mesure — coordinateur.
Construit le layout et délègue la capture à CapturePipeline,
le rendu graphique à ChartRenderer.
"""

import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2

from src.ui.widgets.ui_utils import (
    COLOR_FRAME_BG,
    COLOR_CARD_BG,
    COLOR_STATUS_RUNNING,
    COLOR_STATUS_STOPPED,
    COLOR_ACCENT,
    create_display_card,
    display_read_only_param,
)
from src.ui.views.measure_subviews.capture_pipeline import CapturePipeline
from src.ui.views.measure_subviews.chart_renderer import ChartRenderer


class MeasureView(CapturePipeline, ChartRenderer):
    """Classe principale de la vue Mesure"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, parent, app):
        """
        Initialise la vue Mesure.
        
        Args:
            parent: Widget parent
            app: Instance de l'application principale
        """
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=COLOR_FRAME_BG)
        # Variables locales
        self.captured_tk_img = None
        self.segmented_tk_img = None
        self.curve_tk_img = None
        self.live_tk_img = None
        self.particles_table_data = []
        self.is_segmenting = False
        self.last_capture_time = time.time()
        # Initialisation UI pour Pylint (W0201)
        self.start_btn = None
        self.stop_btn = None
        self.manual_capture_btn = None
        self.status_indicator = None
        self.status_circle = None
        self.status_label = None
        self.params_active_frame = None
        self.live_label = None
        self.captured_label = None
        self.segmented_label = None
        self.curve_label = None

        self._build_ui()

    def _build_ui(self):
        """Construit le layout de la vue Mesure."""
        self.frame.columnconfigure(0, weight=0, minsize=400)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self._setup_left_panel()
        self._setup_right_panel()

    def _setup_left_panel(self):
        """Configure le panneau latéral gauche (contrôles et statistiques)."""
        info_card = ttk.Frame(self.frame, style="Card.TFrame")
        info_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tk.Label(
            info_card,
            text="Capteur - contrôles",
            bg="#e5e7eb",
            fg=COLOR_ACCENT,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
        ).pack(fill="x")
        tk.Label(info_card, text="Facteur de conversion actuel :").pack(fill="x")
        tk.Label(info_card, textvariable=self.app.facteur_conversion).pack(fill="x")
        inner = tk.Frame(info_card, bg=COLOR_CARD_BG, padx=20, pady=10)
        inner.pack(fill="both", expand=True)
        # Boutons de contrôle
        button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        button_frame.pack(fill="x", pady=(0, 20))
        self.start_btn = ttk.Button(
            button_frame,
            text="▶ Démarrer",
            style="Start.TButton",
            command=self.app.start_camera,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.stop_btn = ttk.Button(
            button_frame,
            text="◼ Arrêter",
            style="Stop.TButton",
            command=self.app.stop_camera,
        )
        self.stop_btn.pack(side="left", fill="x", expand=True)
        self.manual_capture_btn = ttk.Button(
            button_frame,
            text="Capture Manuelle",
            style="Secondary.TButton",
            command=self._manual_capture,
        )
        self.manual_capture_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.manual_capture_btn.pack_forget()
        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=10)
        # État du capteur
        tk.Label(
            inner,
            text="État du capteur",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(5, 0))
        status_row = tk.Frame(inner, bg=COLOR_CARD_BG)
        status_row.pack(anchor="w")
        self.status_indicator = tk.Canvas(
            status_row, width=16, height=16, bg=COLOR_CARD_BG, highlightthickness=0
        )
        self.status_indicator.pack(side="left", padx=(0, 8))
        self.status_circle = self.status_indicator.create_oval(
            1, 1, 15, 15, fill=COLOR_STATUS_STOPPED, outline=""
        )
        self.status_label = tk.Label(
            status_row,
            textvariable=self.app.status_var,
            bg=COLOR_CARD_BG,
            fg=COLOR_STATUS_STOPPED,
            font=("Segoe UI", 11, "bold"),
        )
        self.status_label.pack(side="left")
        tk.Label(
            status_row,
            textvariable=self.app.status_detail_var,
            bg=COLOR_CARD_BG,
            fg="#6b7280",
            font=("Segoe UI", 9, "italic"),
        ).pack(side="left", padx=5)
        # Paramètres actifs
        tk.Label(
            inner,
            text="Paramètres actifs",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(15, 0))
        self.params_active_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
        self.params_active_frame.pack(fill="x", pady=5)
        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=10)
        # Statistiques de session
        tk.Label(
            inner,
            text="Statistiques de session",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(5, 0))
        tk.Label(
            inner, text="Heure système :", bg=COLOR_CARD_BG, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
        tk.Label(
            inner, textvariable=self.app.datetime_var, bg=COLOR_CARD_BG, fg="#4b5563"
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Temps avant prochaine capture :",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))
        tk.Label(
            inner,
            textvariable=self.app.time_left_capture_var,
            bg=COLOR_CARD_BG,
            fg=COLOR_STATUS_RUNNING,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Particules détectées (dernière capture) :",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))
        tk.Label(
            inner,
            textvariable=self.app.particles_count_var,
            bg=COLOR_CARD_BG,
            fg="#2C3E50",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Total images capturées :",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))
        tk.Label(
            inner,
            textvariable=self.app.images_count_var,
            bg=COLOR_CARD_BG,
            fg=COLOR_ACCENT,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Horodatage dernière capture :",
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))
        tk.Label(
            inner,
            textvariable=self.app.last_capture_time_var,
            bg=COLOR_CARD_BG,
            font=("Segoe UI", 10, "italic"),
        ).pack(anchor="w")

    def _setup_right_panel(self):
        """Configure la grille d'images (panneau droit)."""
        grid_frame = tk.Frame(self.frame, bg=COLOR_FRAME_BG)
        grid_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.rowconfigure(1, weight=1)
        camera_card = create_display_card(
            grid_frame,
            "Flux caméra temps réel",
            0,
            0,
            (0, 5),
            "Flux caméra (Hors-ligne)\nConfigurer dans Paramètres.",
        )
        self.live_label = camera_card.winfo_children()[1].winfo_children()[0]
        cap_card = create_display_card(
            grid_frame, "Image capturée", 0, 1, (5, 0), "Aucune image capturée."
        )
        self.captured_label = cap_card.winfo_children()[1].winfo_children()[0]
        seg_card = create_display_card(
            grid_frame, "Masque segmenté", 1, 0, (0, 5), "En attente de segmentation..."
        )
        self.segmented_label = seg_card.winfo_children()[1].winfo_children()[0]
        curve_card = create_display_card(
            grid_frame,
            "Courbe granulométrique",
            1,
            1,
            (5, 0),
            "En attente de données pour la courbe...",
        )
        self.curve_label = curve_card.winfo_children()[1].winfo_children()[0]
    # ── Méthodes d'interface ────────────────────────────────────────────
    def update_active_params_display(self):
        """Met à jour l'affichage des paramètres actifs."""
        for widget in self.params_active_frame.winfo_children():
            widget.destroy()
        url_display = self.app.url_var.get()
        if len(url_display) > 30:
            url_display = url_display[:27] + "..."
        try:
            scale_value = float(self.app.facteur_conversion.get().replace(",", "."))
            scale_display = f"{scale_value:.4f}"
        except (ValueError, TypeError, AttributeError):
            scale_display = self.app.facteur_conversion.get()
        path_display = self.app.results_path_var.get()
        if len(path_display) > 30:
            path_display = path_display[:15] + "..." + path_display[-15:]
        mode = self.app.capture_mode_var.get()
        mode_display = "Automatique" if mode == "automatique" else "Manuel"
        display_read_only_param(
            self.params_active_frame, "Mode capture :", mode_display
        )
        display_read_only_param(
            self.params_active_frame, "URL/IP active :", url_display
        )
        if mode == "automatique":
            display_read_only_param(
                self.params_active_frame,
                "Délai capture :",
                self.app.save_delay_display_var.get(),
            )
            display_read_only_param(
                self.params_active_frame,
                "Heures actives :",
                f"{self.app.start_time_var.get()} - {self.app.end_time_var.get()}",
            )
        else:
            display_read_only_param(
                self.params_active_frame, "Délai capture :", "Manuel"
            )
            display_read_only_param(
                self.params_active_frame, "Heures actives :", "Non applicable"
            )
        display_read_only_param(
            self.params_active_frame, "Chemin résultats :", path_display
        )
        display_read_only_param(
            self.params_active_frame, "Échelle :", f"{scale_display} mm/px"
        )

    def update_camera_status_ui(self, is_running):
        """Met à jour l'interface selon l'état de la caméra."""
        if is_running:
            self.status_indicator.itemconfig(
                self.status_circle, fill=COLOR_STATUS_RUNNING
            )
            self.status_label.config(fg=COLOR_STATUS_RUNNING)
            self.app.status_var.set("EN COURS")
            self.app.status_detail_var.set("(En ligne)")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            if self.app.capture_mode_var.get() == "manuel":
                self.manual_capture_btn.pack(
                    side="left", fill="x", expand=True, padx=(10, 0)
                )
            else:
                self.manual_capture_btn.pack_forget()
        else:
            self.status_indicator.itemconfig(
                self.status_circle, fill=COLOR_STATUS_STOPPED
            )
            self.status_label.config(fg=COLOR_STATUS_STOPPED)
            self.app.status_var.set("ARRÊTÉE")
            self.app.status_detail_var.set("(Hors-ligne)")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.manual_capture_btn.pack_forget()

    def update_live_feed(self, frame):
        """Met à jour le flux vidéo en direct."""
        if frame is not None and hasattr(self, "live_label") and self.live_label:
            self.app.last_captured_frame = frame
            try:
                cv2image = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv2image)
                container = self.live_label.image_container
                cw = container.winfo_width()
                ch = container.winfo_height()
                if cw > 10 and ch > 10:
                    ratio = min(cw / pil_img.width, ch / pil_img.height)
                    if ratio < 0.1:
                        ratio = max(cw / pil_img.width, ch / pil_img.height)
                    resized_img = pil_img.resize(
                        (int(pil_img.width * ratio), int(pil_img.height * ratio)),
                        Image.Resampling.LANCZOS,
                    )
                    self.live_tk_img = ImageTk.PhotoImage(resized_img)
                    self.live_label.config(image=self.live_tk_img, text="")
                    self.live_label.image = self.live_tk_img
                    if (
                        self.app.use_undistortion_var.get() and self.app.mtx is not None
                    ) or (
                        self.app.use_homography_var.get()
                        and self.app.homo_matrix is not None
                    ):
                        self.live_label.config(
                            text="✓ Corrections actives (appliquées lors de l'analyse)",
                            compound="bottom",
                        )
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Erreur d'affichage: {e}")
        else:
            if hasattr(self, "live_label") and self.live_label:
                self.live_label.config(
                    image="",
                    text="Flux caméra (Hors-ligne)\nConfigurer dans Paramètres.",
                )
