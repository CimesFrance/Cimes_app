"""
Contrôleur de la caméra : démarrage, arrêt, flux live, compte-à-rebours.
"""
from typing import TYPE_CHECKING, Dict
import os
import sys
import subprocess
import time
import threading
from datetime import datetime
from tkinter import messagebox
from src.ui.widgets.camera_widget import VideoStream
from src.utils.file_manager import load_correction_parameters, get_project_root
if TYPE_CHECKING:
    import tkinter as tk
    from src.ui.views.measure_view import MeasureView


class CameraController:
    """Mixin ajouté à CimesApp pour gérer la caméra et les captures automatiques."""
    # Annotations pour Pylint (membres attendus de la classe hôte)
    url_var: 'tk.StringVar'
    capture_mode_var: 'tk.StringVar'
    start_time_var: 'tk.StringVar'
    end_time_var: 'tk.StringVar'
    last_capture_time_var: 'tk.StringVar'
    time_left_capture_var: 'tk.StringVar'
    capture_time_val_var: 'tk.StringVar'
    capture_time_unit_var: 'tk.StringVar'
    save_delay_display_var: 'tk.StringVar'
    days_vars: Dict[str, 'tk.BooleanVar']
    measure_view: 'MeasureView'
    after: callable
    after_cancel: callable
    correction_granulo: Dict[str, 'tk.DoubleVar']

    def __init__(self):
        self.video_stream = None
        self.camera_running = False
        self.last_capture_time = 0.0
        self._after_id = None
        self._countdown_id = None
        self.last_captured_frame = None
        self.correction_process = None

    def start_camera(self):
        """Démarre la caméra."""
        if self.camera_running:
            return
        rtsp_url = self.url_var.get()
        if not rtsp_url or "N/A" in rtsp_url or "configurer" in rtsp_url:
            messagebox.showerror("Erreur", "URL de caméra non configurée.")
            return
        mode = self.capture_mode_var.get()
        if mode == "automatique" and not self._is_within_operating_hours():
            messagebox.showwarning(
                "Hors plage horaire",
                "Le système est actuellement hors des heures de fonctionnement configurées.\n"
                f"Heures actives : {self.start_time_var.get()} - {self.end_time_var.get()}"
            )
            return
        if self.video_stream:
            self.video_stream.stop()
            self.video_stream = None
        self.video_stream = VideoStream(rtsp_url)
        if self.video_stream.start():
            self.camera_running = True
            self._update_camera_status_ui(True)
            self._start_live_feed()
            self.last_capture_time = time.time()
            self.last_capture_time_var.set("En cours...")
            if mode == "manuel":
                if hasattr(self, "measure_view"):
                    self.measure_view.manual_capture_btn.pack(
                        side="left", fill="x", expand=True, padx=(10, 0)
                    )
            else:
                if hasattr(self, "measure_view"):
                    self.measure_view.manual_capture_btn.pack_forget()
            if mode == "automatique":
                self._start_countdown()
        else:
            self.camera_running = False
            self._update_camera_status_ui(False)
            messagebox.showerror("Erreur", f"Impossible de se connecter à : {rtsp_url}")

    def stop_camera(self):
        """Arrête la caméra."""
        confirmation = messagebox.askyesno(
            "Confirmation", "Voulez-vous vraiment arrêter la caméra ?"
        )
        if not confirmation:
            return
        if not self.camera_running:
            return
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self._countdown_id:
            self.after_cancel(self._countdown_id)
            self._countdown_id = None
        if self.video_stream:
            self.video_stream.stop()
            self.video_stream = None
        self.camera_running = False
        self.last_captured_frame = None
        self._update_camera_status_ui(False)
        self.time_left_capture_var.set("--")
        if hasattr(self, "measure_view"):
            self.measure_view.manual_capture_btn.pack_forget()

    def _update_camera_status_ui(self, is_running):
        """Délègue la mise à jour de l'UI au measure_view."""
        if hasattr(self, "measure_view"):
            self.measure_view.update_camera_status_ui(is_running)

    def _start_live_feed(self):
        """Démarre la mise à jour du flux vidéo (30 fps)."""
        def update():
            if self.video_stream and self.video_stream.running:
                frame = self.video_stream.get_frame()
                if frame is not None and hasattr(self, "measure_view"):
                    self.measure_view.update_live_feed(frame)
                self._after_id = self.after(30, update)
            else:
                if self._after_id:
                    self.after_cancel(self._after_id)
                    self._after_id = None
                self.last_captured_frame = None
                if hasattr(self, "measure_view") and self.measure_view.live_label:
                    self.measure_view.live_label.config(
                        image="",
                        text="Flux caméra (Hors-ligne)\nConfigurer dans Paramètres."
                    )
        update()

    def _start_countdown(self):
        """Compte-à-rebours pour les captures automatiques."""
        def update():
            mode = self.capture_mode_var.get()
            if not self.camera_running:
                if self._countdown_id:
                    self.after_cancel(self._countdown_id)
                    self._countdown_id = None
                self.time_left_capture_var.set("--")
                return
            if mode == "manuel":
                self.time_left_capture_var.set("Mode manuel")
                if self._countdown_id:
                    self.after_cancel(self._countdown_id)
                    self._countdown_id = None
                return
            delay_seconds = self._get_capture_delay_seconds()
            if delay_seconds <= 0:
                self.time_left_capture_var.set("Immédiat")
                if hasattr(self, "measure_view") and not self.measure_view.is_segmenting:
                    self.measure_view.perform_capture()
                self._countdown_id = self.after(1000, update)
                return
            time_elapsed = time.time() - self.last_capture_time
            time_left = delay_seconds - time_elapsed
            is_ready = hasattr(self, "measure_view") and not self.measure_view.is_segmenting
            if time_left <= 0 and is_ready:
                self.measure_view.perform_capture()
                self.last_capture_time = time.time()
            elif hasattr(self, "measure_view") and self.measure_view.is_segmenting:
                self.time_left_capture_var.set("Capture en cours...")
            else:
                self.time_left_capture_var.set(f"{max(0, int(time_left) + 1)} s")
            self._countdown_id = self.after(1000, update)
        update()

    def _get_capture_delay_seconds(self):
        """Calcule le délai de capture en secondes."""
        mode = self.capture_mode_var.get()
        if mode == "manuel":
            return 0
        try:
            val = float(self.capture_time_val_var.get().replace(",", "."))
            unit = self.capture_time_unit_var.get()
            if unit == "min":
                return val * 60
            if unit == "h":
                return val * 3600
            return val
        except ValueError:
            return 0

    def _is_within_operating_hours(self):
        """Vérifie si l'heure actuelle est dans les heures de fonctionnement."""
        try:
            now = datetime.now()
            day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            current_day = day_names[now.weekday()]
            if not self.days_vars[current_day].get():
                return False
            start_time = datetime.strptime(self.start_time_var.get(), "%H:%M").time()
            end_time = datetime.strptime(self.end_time_var.get(), "%H:%M").time()
            current_time = now.time()
            return start_time <= current_time <= end_time
        except (ValueError, KeyError, AttributeError):
            return True

    def _change_correction(self):
        """Lance le subprocess de correction et recharge les paramètres à la fermeture."""
        if self.correction_process is not None and self.correction_process.poll() is None:
            return
        if getattr(sys, 'frozen', False):
            # En mode frozen, on relance l'exécutable avec un argument spécial
            self.correction_process = subprocess.Popen([sys.executable, "--module-correction"])
        else:
            root_dir = get_project_root()
            script_path = os.path.join(root_dir, "modules", "app_change_corr_params", "main.py")
            script_path = os.path.normpath(script_path)
            # pylint: disable=consider-using-with
            self.correction_process = subprocess.Popen([sys.executable, script_path])

        def wait_and_update():
            """ Attend la fermeture du subprocess et met à jour les paramètres. """
            self.correction_process.wait()
            self.after(0, _update_params)

        def _update_params():
            """ Met à jour les paramètres de correction. """
            try:
                vars_corr = load_correction_parameters()
                self.correction_granulo["scale"].set(vars_corr["scale"])
                self.correction_granulo["offset"].set(vars_corr["offset"])
            except (ValueError, KeyError, IOError):
                pass

        threading.Thread(target=wait_and_update, daemon=True).start()
