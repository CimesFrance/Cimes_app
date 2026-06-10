# -*- coding: utf-8 -*-
"""
Panneau de graphiques : courbe granulométrique et histogramme de distribution.
"""

import numpy as np
import matplotlib.pyplot as plt


class ChartPanel:
    """
    Mixin pour CurveView — gère les deux onglets de graphiques.
    """
    # pylint: disable=no-member,attribute-defined-outside-init,too-few-public-methods

    def _update_curve_view(self):
        """Met à jour la courbe de la dernière capture."""
        if self.app.capture_history and self.app.current_capture_index >= 0:
            capture = self.app.capture_history[self.app.current_capture_index]
            self._update_curve_view_for_capture(capture["id"])
        else:
            self._clear_curve_chart()

    def _clear_curve_chart(self):
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            "Capturez des images pour voir les courbes granulométriques",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            fontsize=12,
            color="gray",
        )
        self.ax.set_title(
            "Courbe Granulométrique Cumulative", fontsize=14, fontweight="bold"
        )
        self.ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        self.ax.set_ylabel("% passant", fontsize=12)
        self.ax.grid(True)
        self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        self.ax.set_xticklabels(
            ["0", "22.4", "31.5", "40", "50", "63", "80"], fontsize=11
        )
        self.ax.set_yticks(np.arange(0, 101, 10))
        self.ax.set_yticklabels(
            [f"{int(y)}%" for y in np.arange(0, 101, 10)], fontsize=11
        )
        self.ax.set_xlim([0, 80])
        self.ax.set_ylim([0, 105])
        self.canvas.draw()

    def _update_curve_view_for_capture(self, capture_id):
        """Met à jour la courbe granulométrique pour une capture spécifique."""
        if capture_id is None:
            self._clear_curve_chart()
            return

        capture = next(
            (c for c in self.app.capture_history if c["id"] == capture_id), None
        )

        if not capture or not capture.get("tamis_exp"):
            self._clear_curve_chart()
            return

        self.ax.clear()

        self.ax.plot(
            [0, 22.4, 31.5, 40, 50, 63, 100],
            [0, 4, 26, 70, 99, 99, 100],
            "g--",
            linewidth=1.5,
            label="VSS",
        )
        self.ax.plot(
            [0, 22.4, 31.5, 40, 50, 50, 50],
            [0, 0, 0, 25, 70, 70, 70],
            color="orange",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label="VSI",
        )

        tamis = capture["tamis_exp"]
        if self.app.show_corrected_curve_var.get() and capture.get(
            "cumulative_corrected"
        ):
            cumul = capture["cumulative_corrected"]
            label = "Courbe corrigée (DNA)"
        else:
            cumul = capture["cumulative_raw"]
            label = "Courbe brute"

        self.ax.plot(tamis, cumul, "b-o", linewidth=2, markersize=4, label=label)

        self.ax.set_xlabel("Taille du tamis (mm)", fontsize=12)
        self.ax.set_ylabel("% passant cumulé", fontsize=12)
        self.ax.set_title(
            f"Courbe Granulométrique - Capture #{capture['id']}",
            fontsize=14,
            fontweight="bold",
        )
        self.ax.set_xticks([0, 22.4, 31.5, 40, 50, 63, 80])
        self.ax.set_xticklabels(
            ["0", "22.4", "31.5", "40", "50", "63", "80"], fontsize=11
        )
        self.ax.set_yticks(np.arange(0, 101, 10))
        self.ax.set_yticklabels(
            [f"{int(y)}%" for y in np.arange(0, 101, 10)], fontsize=11
        )
        self.ax.set_xlim([0, 85])
        self.ax.set_ylim([0, 105])
        self.ax.grid(True)
        self.ax.legend(loc="upper left", fontsize=10)

        for i, (x, y) in enumerate(zip(tamis, cumul)):
            self.ax.annotate(
                f"{y:.1f}%",
                xy=(x, y),
                xytext=(0, 5 if i % 2 == 0 else -15),
                textcoords="offset points",
                ha="center",
                va="bottom" if i % 2 == 0 else "top",
                fontsize=9,
                fontweight="bold",
                bbox={
                    "boxstyle": "round,pad=0.2",
                    "facecolor": "white",
                    "edgecolor": "lightblue",
                    "alpha": 0.8,
                },
            )

        self.canvas.draw()

    def _update_histogram_for_capture(self, capture_id):
        """Met à jour l'histogramme de distribution pour une capture."""
        capture = next(
            (c for c in self.app.capture_history if c["id"] == capture_id), None
        )

        if not capture:
            self.hist_ax.clear()
            self.hist_ax.text(
                0.5,
                0.5,
                "Aucune capture sélectionnée",
                ha="center",
                va="center",
                transform=self.hist_ax.transAxes,
                fontsize=12,
                color="gray",
            )
            self.hist_ax.set_xlabel("Taille (mm)", fontsize=12)
            self.hist_ax.set_ylabel("Nombre de particules", fontsize=12)
            self.hist_ax.set_title(
                "Distribution Granulométrique des Particules",
                fontsize=14,
                fontweight="bold",
            )
            self.hist_ax.grid(True)
            self.hist_canvas.draw()
            return

        self.hist_ax.clear()

        if capture.get("minor_axes_mm") and len(capture["minor_axes_mm"]) > 0:
            try:
                minor_axes_mm = np.array(
                    [x for x in capture["minor_axes_mm"] if x > 0.0]
                )
                if len(minor_axes_mm) == 0:
                    raise ValueError("Pas de données après filtrage.")

                bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
                bin_labels = [
                    "<10",
                    "10-20",
                    "20-30",
                    "30-40",
                    "40-50",
                    "50-60",
                    "60-70",
                    "70-80",
                    ">80",
                ]

                hist, _ = np.histogram(minor_axes_mm, bins=bins)
                colors = plt.cm.viridis(np.linspace(0, 1, len(hist)))  # pylint: disable=no-member
                bars = self.hist_ax.bar(
                    range(len(hist)), hist, color=colors, edgecolor="black", alpha=0.8
                )

                for bar_rect, val in zip(bars, hist):
                    self.hist_ax.text(
                        bar_rect.get_x() + bar_rect.get_width() / 2.0,
                        bar_rect.get_height() + 0.5,
                        f"{val}",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                    )

                self.hist_ax.set_xlabel("Taille des particules (mm)", fontsize=12)
                self.hist_ax.set_ylabel("Nombre de particules", fontsize=12)
                self.hist_ax.set_title(
                    f"Distribution Granulométrique - Capture #{capture['id']}",
                    fontsize=14,
                    fontweight="bold",
                )
                self.hist_ax.set_xticks(range(len(bin_labels)))
                self.hist_ax.set_xticklabels(bin_labels, rotation=45, fontsize=10)
                self.hist_ax.grid(True, linestyle="--", axis="y")

                mean_size = np.mean(minor_axes_mm)
                median_size = np.median(minor_axes_mm)
                stats_text = (
                    f"Total particules: {len(minor_axes_mm)}\n"
                    f"Moyenne: {mean_size:.1f} mm\n"
                    f"Médiane: {median_size:.1f} mm"
                )
                self.hist_ax.text(
                    0.02,
                    0.98,
                    stats_text,
                    transform=self.hist_ax.transAxes,
                    verticalalignment="top",
                    fontsize=9,
                    bbox={
                        "boxstyle": "round",
                        "facecolor": "wheat",
                        "alpha": 0.5,
                    },
                )

                self.hist_ax.set_ylim([0, max(hist) * 1.2 if max(hist) > 0 else 1])
                self.hist_fig.tight_layout(pad=3.0)

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.hist_ax.text(
                    0.5,
                    0.5,
                    f"Erreur lors du tracé\n{str(e)[:50]}",
                    ha="center",
                    va="center",
                    transform=self.hist_ax.transAxes,
                    fontsize=12,
                    color="red",
                )
                self.hist_ax.grid(True)
        else:
            self.hist_ax.text(
                0.5,
                0.5,
                "Aucune donnée de distribution disponible",
                ha="center",
                va="center",
                transform=self.hist_ax.transAxes,
                fontsize=12,
                color="gray",
            )
            self.hist_ax.set_xlabel("Taille (mm)", fontsize=12)
            self.hist_ax.set_ylabel("Nombre de particules", fontsize=12)
            self.hist_ax.set_title(
                "Distribution Granulométrique des Particules",
                fontsize=14,
                fontweight="bold",
            )
            self.hist_ax.grid(True)

        self.hist_canvas.draw()
