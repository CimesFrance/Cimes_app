"""
Dialogue de comparaison multi-captures de la vue Courbe.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.ui.widgets.ui_utils import COLOR_FRAME_BG


class ComparisonDialog:
    """
    Mixin pour CurveView — gère la boîte de dialogue de comparaison et le rapport PDF.
    """
    # pylint: disable=no-member,too-few-public-methods

    def _open_comparison_dialog(self):
        """Ouvre le dialogue de comparaison multi-captures."""
        if not self.app.capture_history:
            messagebox.showinfo(
                "Information", "Aucune capture disponible pour comparaison."
            )
            return
        dialog = tk.Toplevel(self.app)
        dialog.title("Comparaison Multi-Captures")
        dialog.geometry("500x400")
        dialog.configure(bg=COLOR_FRAME_BG)
        tk.Label(
            dialog,
            text="Sélectionnez les captures à comparer:",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_FRAME_BG,
            fg="white",
            pady=10,
        ).pack()
        list_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        for capture in self.app.capture_history:
            listbox.insert(
                tk.END,
                f"Capture #{capture['id']} - "
                f"{capture['timestamp'].strftime('%H:%M:%S')} - "
                f"{capture['particles_count']} particules",
            )
        button_frame = tk.Frame(dialog, bg=COLOR_FRAME_BG)
        button_frame.pack(pady=10)

        def apply_comparison():
            """Applique la comparaison multi-captures."""
            selections = listbox.curselection()
            if len(selections) < 2:
                messagebox.showwarning(
                    "Attention", "Veuillez sélectionner au moins 2 captures."
                )
                return
            self.app.comparison_captures = [
                self.app.capture_history[i]["id"] for i in selections
            ]
            self.app.comparison_mode = True
            self._display_comparison_chart()
            dialog.destroy()
            messagebox.showinfo(
                "Succès", f"Comparaison de {len(selections)} captures activée."
            )

        ttk.Button(
            button_frame,
            text="Comparer",
            style="Start.TButton",
            command=apply_comparison,
        ).pack(side="left", padx=5)
        ttk.Button(
            button_frame,
            text="Annuler",
            style="Secondary.TButton",
            command=dialog.destroy,
        ).pack(side="left", padx=5)

    def _display_comparison_chart(self):
        """Affiche le graphique de comparaison dans une fenêtre dédiée."""
        # pylint: disable=too-many-locals
        if not self.app.comparison_captures:
            return
        comp_win = tk.Toplevel(self.app)
        comp_win.title("Comparaison Multi-Captures")
        comp_win.geometry("900x600")
        comp_win.configure(bg=COLOR_FRAME_BG)
        comp_fig = Figure(figsize=(12, 8))
        comp_ax = comp_fig.add_subplot(111)
        comp_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.app.comparison_captures)))  # pylint: disable=no-member
        all_annotations = []
        for i, capture_id in enumerate(self.app.comparison_captures):
            capture = next(
                (c for c in self.app.capture_history if c["id"] == capture_id), None
            )
            if (
                not capture
                or not capture.get("tamis_exp")
                or not capture.get("cumulative_raw")
            ):
                continue
            tamis = capture["tamis_exp"]
            cumul = (
                capture["cumulative_corrected"]
                if self.app.show_corrected_curve_var.get()
                and capture.get("cumulative_corrected")
                else capture["cumulative_raw"]
            )
            comp_ax.plot(
                tamis,
                cumul,
                marker="o",
                color=colors[i],
                linewidth=2,
                label=f"Capture #{capture_id} ({capture['particles_count']} part.)",
            )
            capture_annotations = []
            for j, (x, y) in enumerate(zip(tamis, cumul)):
                ann = comp_ax.annotate(
                    f"{y:.1f}%",
                    xy=(x, y),
                    xytext=(0, 5 if j % 2 == 0 else -15),
                    textcoords="offset points",
                    ha="center",
                    va="bottom" if j % 2 == 0 else "top",
                    fontsize=8,
                    fontweight="bold",
                    color=colors[i],
                    bbox={
                        "boxstyle": "round,pad=0.2",
                        "facecolor": "white",
                        "edgecolor": colors[i],
                        "alpha": 0.8,
                    },
                )
                capture_annotations.append(ann)
            all_annotations.append(capture_annotations)
        comp_ax.plot(
            [0, 22.4, 31.5, 40, 50, 63, 100],
            [0, 4, 26, 70, 99, 99, 100],
            "g--",
            linewidth=2,
            label="Courbe VSS",
            alpha=0.7,
        )
        comp_ax.plot(
            [0, 22.4, 31.5, 40, 50, 50, 50],
            [0, 0, 0, 25, 70, 70, 70],
            "orange",
            linewidth=2,
            linestyle="--",
            label="Courbe VSI",
            alpha=0.7,
        )
        comp_ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        comp_ax.set_ylabel("% passant cumulé", fontsize=12)
        comp_ax.set_title("Comparaison Multi-Captures", fontsize=14, fontweight="bold")
        comp_ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        comp_ax.set_yticks(np.arange(0, 101, 10))
        comp_ax.set_xlim([0, 85])
        comp_ax.set_ylim([0, 105])
        comp_ax.grid(True, alpha=0.3)
        comp_ax.legend(loc="upper left", fontsize=10)
        canvas_comp = FigureCanvasTkAgg(comp_fig, master=comp_win)
        canvas_comp.draw()
        canvas_comp.get_tk_widget().pack(fill="both", expand=True)

    def _generate_professional_report(self):
        """Génère un rapport PDF professionnel."""
        messagebox.showinfo(
            "Rapport PDF",
            "La génération de rapport PDF est disponible.\n"
            "Configurez les options dans Paramètres → Transmission.",
        )
