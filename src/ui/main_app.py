# -*- coding: utf-8 -*-
"""
Application principale CIMES — coordinateur des vues.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from src.ui.widgets.ui_utils import (
    COLOR_BG_DARK, COLOR_ACCENT, COLOR_TEXT_LIGHT,
    COLOR_FRAME_BG, LOGO_PATH, configure_styles, creer_dossier
)
from src.ui.app_init.variables import initialize_variables
from src.ui.app_init.camera_controller import CameraController
from src.ui.views.measure_view import MeasureView
from src.ui.views.curve_view import CurveView
from src.ui.views.reload_view import ReloadView
from src.ui.views.param_view import ParamView
from src.utils.file_manager import (
    load_calibration_files, ensure_results_directory,
    load_correction_parameters
)
from src.utils.config_manager import (
    load_sensor_settings, load_report_configuration, load_calibration_settings
)


class CimesApp(CameraController, tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("1600x1000")
        self.minsize(1400, 800)
        self.configure(bg=COLOR_FRAME_BG)
        self.title("CIMES - Analyse granulométrique")

        configure_styles(self)
        initialize_variables(self)
        self._initialize_views()
        self._setup_initial_configuration()
        self._start_auto_updates()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ------------------------------------------------------------------
    # Fermeture
    # ------------------------------------------------------------------
    def _on_closing(self):
        if hasattr(self, "correction_process") and self.correction_process.poll() is None:
            try:
                self.correction_process.terminate()
            except Exception:
                pass
        if hasattr(self, "param_view") and hasattr(self.param_view, "calibration_process"):
            if self.param_view.calibration_process.poll() is None:
                try:
                    self.param_view.calibration_process.terminate()
                except Exception:
                    pass
        self.destroy()

    # ------------------------------------------------------------------
    # Construction des vues
    # ------------------------------------------------------------------
    def _initialize_views(self):
        self._create_header()
        self.content_frame = tk.Frame(self, bg=COLOR_FRAME_BG)
        self.content_frame.pack(side="top", fill="both", expand=True)

        self.measure_view = MeasureView(self.content_frame, self)
        self.curve_view   = CurveView(self.content_frame, self)
        self.reload_view  = ReloadView(self.content_frame, self)
        self.param_view   = ParamView(self.content_frame, self)

        self.show_measure_view()
        self._set_active_nav("measure")

    def _create_header(self):
        header_height = 90
        header = tk.Frame(self, bg=COLOR_BG_DARK, height=header_height)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        # Logo section
        logo_container = tk.Frame(header, bg=COLOR_BG_DARK)
        logo_container.pack(side="left", padx=30, fill="y")

        try:
            img = Image.open(LOGO_PATH)
            display_height = 70  # Increased from 60
            ratio = img.width / img.height if img.height > 0 else 1
            logo_img = img.resize((int(display_height * ratio), display_height), Image.Resampling.LANCZOS)
            self.logo_header = ImageTk.PhotoImage(logo_img)
            tk.Label(logo_container, image=self.logo_header, bg=COLOR_BG_DARK).pack(expand=True)
        except Exception:
            tk.Label(logo_container, text="CIMES", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT,
                     font=("Segoe UI", 18, "bold")).pack(expand=True)

        # Navigation section
        self.nav_container = tk.Frame(header, bg=COLOR_BG_DARK)
        self.nav_container.pack(side="right", padx=30, fill="y")
        
        # This will contain the buttons and the indicator
        nav_buttons_frame = tk.Frame(self.nav_container, bg=COLOR_BG_DARK)
        nav_buttons_frame.pack(side="top", fill="x")

        nav_items = [
            ("measure",  "Mesure"),
            ("curve",    "Courbe"),
            ("reload",   "Recharger"),
            ("param",    "Paramètres"),
        ]
        
        self.nav_buttons = {}
        for key, label in nav_items:
            # We use a container for each button to manage the indicator
            btn_box = tk.Frame(nav_buttons_frame, bg=COLOR_BG_DARK)
            btn_box.pack(side="left", padx=5)
            
            btn = ttk.Button(btn_box, text=label, style="Nav.TButton",
                             command=lambda k=key: self._on_nav_clicked(k))
            btn.pack(side="top", pady=(22, 0))
            self.nav_buttons[key] = btn
            
            # Sub-indicator line (hidden by default)
            line = tk.Frame(btn_box, bg=COLOR_ACCENT, height=3)
            line.pack(side="top", fill="x", pady=(2, 0))
            line.pack_forget() # Hidden initially
            btn.indicator = line
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, True))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, False))

        self.change_corr_btn = ttk.Button(
            nav_buttons_frame, text="Modifier correction",
            style="Nav.TButton",
            command=self._change_correction
        )
        self.change_corr_btn.pack(side="left", padx=(15, 0), pady=(22, 0))

    def _on_nav_hover(self, btn, key, is_entering):
        if hasattr(self, "current_view_key") and self.current_view_key == key:
            return
        # Hover effect is handled by style.map mostly, but we can add more here if needed
        pass

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _set_active_nav(self, key):
        self.current_view_key = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(style="NavActive.TButton") # White text
                btn.indicator.pack(side="top", fill="x", pady=(2, 0))
            else:
                btn.configure(style="Nav.TButton") # Dimmed text
                btn.indicator.pack_forget()

    def _on_nav_clicked(self, key):
        if key == "measure":
            self.show_measure_view()
        elif key == "curve":
            self.show_curve_view()
            if hasattr(self, "curve_view"):
                self.curve_view._update_curve_view()
        elif key == "reload":
            self.show_reload_view()
        elif key == "param":
            self.show_param_view()
        self._set_active_nav(key)

    def _raise_view(self, view):
        for v in [self.measure_view, self.curve_view, self.reload_view, self.param_view]:
            if v and hasattr(v, "frame"):
                v.frame.pack_forget()
        if view and hasattr(view, "frame"):
            view.frame.pack(fill="both", expand=True)

    def show_measure_view(self): self._raise_view(self.measure_view)
    def show_curve_view(self):   self._raise_view(self.curve_view)
    def show_reload_view(self):  self._raise_view(self.reload_view)
    def show_param_view(self):   self._raise_view(self.param_view)

    # ------------------------------------------------------------------
    # Configuration initiale
    # ------------------------------------------------------------------
    def _setup_initial_configuration(self):
        self._update_clock()
        self._load_initial_settings()
        self._load_calibration_files_automatically()
        ensure_results_directory(self.results_path_var.get())
        self._update_active_params_display()
        self._update_save_delay_display()

    def _load_initial_settings(self):
        load_sensor_settings(self)
        load_report_configuration(self)
        load_calibration_settings(self)

    def _load_calibration_files_automatically(self):
        self.mtx, self.dist, self.calib_path = load_calibration_files()
        if self.mtx is not None:
            self.use_undistortion_var.set(True)
        if self.homo_matrix is not None:
            self.use_homography_var.set(True)

    # ------------------------------------------------------------------
    # Mises à jour automatiques
    # ------------------------------------------------------------------
    def _start_auto_updates(self):
        self.after(1000, self._update_clock)
        self.url_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.capture_time_val_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.capture_time_unit_var.trace_add("write", lambda *a: self._update_save_delay_display())
        self.results_path_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.start_time_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.end_time_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.capture_mode_var.trace_add("write", lambda *a: self._on_capture_mode_changed())
        self.facteur_conversion.trace_add("write", lambda *a: self._on_scale_changed())

    def _update_clock(self):
        self.datetime_var.set(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        self.after(1000, self._update_clock)

    def _update_active_params_display(self):
        if hasattr(self, "measure_view"):
            self.measure_view.update_active_params_display()

    def _update_save_delay_display(self):
        mode = self.capture_mode_var.get()
        if mode == "automatique":
            self.save_delay_display_var.set(
                f"{self.capture_time_val_var.get()} {self.capture_time_unit_var.get()}"
            )
        else:
            self.save_delay_display_var.set("Manuel")
        self._update_active_params_display()

    def _on_capture_mode_changed(self):
        self._update_active_params_display()
        if hasattr(self, "param_view"):
            self.param_view._toggle_capture_controls()

    def _on_scale_changed(self):
        try:
            scale_value = float(self.facteur_conversion.get().replace(",", "."))
            if scale_value <= 0:
                return
            self._update_active_params_display()
            if hasattr(self, "curve_view") and self.curve_view.frame.winfo_ismapped():
                self.curve_view._update_curve_view()
        except ValueError:
            pass
