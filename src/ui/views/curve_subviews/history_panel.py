# -*- coding: utf-8 -*-
"""
Historique des captures et tableau des particules de la vue Courbe.
"""
import tkinter as tk
from tkinter import ttk

from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG
)


class HistoryPanel:
    """
    Mixin pour CurveView — gère l'historique et le tableau des particules.
    """

    def _create_particles_table(self, parent):
        """Crée le tableau des particules."""
        table_frame = tk.Frame(parent, bg=COLOR_CARD_BG)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "minor_mm", "major_mm")
        self.particles_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.particles_tree.heading("id",        text="ID")
        self.particles_tree.heading("minor_mm",  text="Axe Mineur (mm)")
        self.particles_tree.heading("major_mm",  text="Axe Majeur (mm)")

        self.particles_tree.column("id",       width=50,  anchor="center")
        self.particles_tree.column("minor_mm", width=150, anchor="center")
        self.particles_tree.column("major_mm", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.particles_tree.yview)
        self.particles_tree.configure(yscrollcommand=scrollbar.set)

        self.particles_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _update_particles_table(self):
        """Met à jour le tableau des particules avec la dernière capture."""
        if not self.particles_tree:
            return
        for item in self.particles_tree.get_children():
            self.particles_tree.delete(item)
        if hasattr(self.app, "measure_view") and hasattr(self.app.measure_view, "particles_table_data"):
            for particle in self.app.measure_view.particles_table_data:
                self.particles_tree.insert("", "end", values=(
                    particle["id"],
                    f"{particle['minor_mm']:.2f}",
                    f"{particle['major_mm']:.2f}",
                ))

    def _update_particles_table_for_capture(self, index):
        """Met à jour le tableau pour une capture spécifique par index."""
        if 0 <= index < len(self.app.capture_history):
            capture = self.app.capture_history[index]
            particles_data = [
                {"id": i + 1, "minor_mm": p["minor_axis_mm"], "major_mm": p["major_axis_mm"]}
                for i, p in enumerate(capture.get("particles_data", []))
            ]
            if hasattr(self.app, "measure_view"):
                self.app.measure_view.particles_table_data = particles_data
            self._update_particles_table()

    def _update_capture_history_display(self):
        """Met à jour l'affichage de l'historique des captures."""
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        if not self.app.capture_history:
            tk.Label(self.history_frame, text="Aucune capture disponible",
                     bg=COLOR_CARD_BG, fg="#666", font=("Segoe UI", 10)).pack(pady=20)
            return

        for i in range(len(self.app.capture_history) - 1, -1, -1):
            idx = i
            capture = self.app.capture_history[idx]

            frame = tk.Frame(self.history_frame, bg=COLOR_CARD_BG, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=2, padx=2)

            bg_color = "#e3f2fd" if idx == self.app.current_capture_index else COLOR_CARD_BG
            if idx == self.app.current_capture_index:
                frame.configure(bg="#e3f2fd")

            content_frame = tk.Frame(frame, bg=bg_color)
            content_frame.pack(fill="x", padx=8, pady=4)

            title_frame = tk.Frame(content_frame, bg=bg_color)
            title_frame.pack(fill="x")

            tk.Label(title_frame, text=f"#{capture['id']}",
                     bg=bg_color, font=("Segoe UI", 9, "bold")).pack(side="left")
            tk.Label(title_frame,
                     text=f" {capture['timestamp'].strftime('%H:%M')}",
                     bg=bg_color, font=("Segoe UI", 8)).pack(side="left", padx=(0, 5))

            info_frame = tk.Frame(content_frame, bg=bg_color)
            info_frame.pack(fill="x", pady=(2, 0))
            tk.Label(info_frame, text=f"Objets: {capture['particles_count']}",
                     bg=bg_color, font=("Segoe UI", 8)).pack(side="left")

            btn_frame = tk.Frame(content_frame, bg=bg_color)
            btn_frame.pack(fill="x", pady=(3, 0))
            ttk.Button(btn_frame, text="Afficher", style="Secondary.TButton",
                       command=lambda i=idx: self._select_capture(i)).pack(side="right")

        self.history_frame.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        self._setup_mousewheel_scrolling()

    def _setup_mousewheel_scrolling(self):
        """Configure le défilement avec la roulette pour l'historique."""
        def on_mousewheel(event):
            if (hasattr(event, "delta") and event.delta < 0) or event.num == 5:
                self.history_canvas.yview_scroll(1, "units")
            elif (hasattr(event, "delta") and event.delta > 0) or event.num == 4:
                self.history_canvas.yview_scroll(-1, "units")
            return "break"

        self.history_canvas.bind("<MouseWheel>", on_mousewheel)
        self.history_canvas.bind("<Button-4>", on_mousewheel)
        self.history_canvas.bind("<Button-5>", on_mousewheel)
        self.history_frame.bind("<MouseWheel>", on_mousewheel)
        self.history_frame.bind("<Button-4>", on_mousewheel)
        self.history_frame.bind("<Button-5>", on_mousewheel)

        def bind_to_children(widget):
            for child in widget.winfo_children():
                child.bind("<MouseWheel>", on_mousewheel)
                child.bind("<Button-4>", on_mousewheel)
                child.bind("<Button-5>", on_mousewheel)
                bind_to_children(child)

        bind_to_children(self.history_frame)

    def _select_capture(self, index):
        """Sélectionne une capture dans l'historique."""
        if 0 <= index < len(self.app.capture_history):
            self.app.current_capture_index = index
            self._update_capture_history_display()
            self._update_curve_view_for_capture(self.app.capture_history[index]["id"])
            self._update_histogram_for_capture(self.app.capture_history[index]["id"])
            self._update_capture_info()
            self._update_particles_table_for_capture(index)
            self.update_statistics_display(self.app.capture_history[index])

    def _prev_capture(self):
        if self.app.current_capture_index > 0:
            self._select_capture(self.app.current_capture_index - 1)

    def _next_capture(self):
        if self.app.current_capture_index < len(self.app.capture_history) - 1:
            self._select_capture(self.app.current_capture_index + 1)

    def _update_capture_info(self):
        """Met à jour les informations de la capture sélectionnée."""
        if not self.app.capture_history or self.app.current_capture_index < 0:
            self.capture_info_label.config(text="Aucune capture disponible")
            return
        capture = self.app.capture_history[self.app.current_capture_index]
        self.capture_info_label.config(
            text=f"Capture #{capture['id']}\n"
                 f"{capture['timestamp'].strftime('%H:%M:%S')}\n"
                 f"Objets: {capture['particles_count']}"
        )
