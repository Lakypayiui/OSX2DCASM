"""Time-series graph widget for the cellular-automaton simulator.

Plots one data series (e.g. entropy or population) against time steps.
Includes inline export buttons next to the title and axis tick labels.
"""

from __future__ import annotations

import csv
from typing import Optional

import pygame

from core.config import P_BORDER, P_FG
from widgets.button import Button
from widgets.base_widget import BaseWidget


class GraphWidget(BaseWidget):
    """Interactive time-series graph widget.

    Reads data from a mutable ``data_ref`` dictionary with keys
    ``"time"`` and ``"values"`` and plots it as a line chart.
    Export-to-image and export-to-CSV buttons sit beside the title.

    Inherits the common widget interface from
    :class:`~widgets.interactive_widget.InteractiveWidget`.
    """

    # ------------------------------------------------------------------
    # Layout constants
    # ------------------------------------------------------------------

    PADDING_LEFT: int = 85
    PADDING_RIGHT: int = 20
    PADDING_TOP: int = 55
    PADDING_BOTTOM: int = 50

    TICK_COUNT: int = 5
    TICK_LENGTH: int = 5
    TICK_COLOR: tuple[int, int, int] = (200, 200, 200)
    TICK_FONT_SIZE: int = 16

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        data_ref: dict[str, list[float]],
        font: pygame.font.Font,
        title: str = "Graph",
        xlabel: str = "Time (steps)",
        ylabel: str = "Value",
        show_exports: bool = True,
        line_color: tuple[int, int, int] = (255, 100, 100),
        bg_color: tuple[int, int, int] = (30, 30, 35),
    ) -> None:
        """Initialise the graph widget.

        Args:
            rect: Position and size as ``(x, y, width, height)``.
            data_ref: Mutable reference to the data series.  Must be a dict
                with keys ``"time"`` and ``"values"``, each a list of
                ``float`` or ``int``.
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            show_exports: Whether to show the export buttons.
            line_color: Colour of the data line.
            bg_color: Background colour of the graph area.
        """
        self.rect = pygame.Rect(rect)
        self.font = font
        self.data_ref = data_ref
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.line_color = line_color
        self.bg_color = bg_color

        self.show_exports = show_exports
        self.dirty = True
        self.graph_surface: Optional[pygame.Surface] = None

        # Export buttons (compact, placed beside the title)
        self.btn_export_img: Optional[Button] = None
        self.btn_export_csv: Optional[Button] = None

        if self.show_exports:
            btn_h = 22
            btn_w = 90
            gap = 6
            y = self.rect.top + 6

            self.btn_export_img = Button(
                rect=(self.rect.right - btn_w * 2 - gap - 16, y, btn_w, btn_h),
                label="Save PNG",
                font=self.font,
                toggle=False,
                bg=(70, 70, 80),
                fg=(240, 240, 240),
            )
            self.btn_export_csv = Button(
                rect=(self.rect.right - btn_w - 8, y, btn_w, btn_h),
                label="Export CSV",
                font=self.font,
                toggle=False,
                bg=(70, 70, 80),
                fg=(240, 240, 240),
            )

    # ------------------------------------------------------------------
    # InteractiveWidget interface
    # ------------------------------------------------------------------

    def set_dirty(self) -> None:
        """Flag the graph for redraw on the next ``draw`` call."""
        self.dirty = True

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Process pygame events (mainly export-button clicks).

        Args:
            ev: Pygame event to process.

        Returns:
            ``True`` if an export button was clicked.
        """
        if not self.enabled:
            return False

        clicked = False

        if self.btn_export_img and self.btn_export_img.handle_event(ev):
            self._export_image()
            clicked = True

        if self.btn_export_csv and self.btn_export_csv.handle_event(ev):
            self._export_csv()
            clicked = True

        return clicked

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the full widget onto the target surface.

        Args:
            surf: Target pygame surface (usually the screen).
        """
        if self.dirty or self.graph_surface is None:
            self._draw_graph()
            self.dirty = False

        if self.graph_surface:
            surf.blit(self.graph_surface, self.rect.topleft)

        # Draw inline export buttons
        if self.btn_export_img:
            self.btn_export_img.draw(surf)
        if self.btn_export_csv:
            self.btn_export_csv.draw(surf)

        # Widget border
        pygame.draw.rect(surf, P_BORDER, self.rect, 1, border_radius=6)

    # ------------------------------------------------------------------
    # Internal graph rendering
    # ------------------------------------------------------------------

    def _draw_graph(self) -> None:
        """Render the graph on an internal cached surface."""
        w, h = self.rect.width, self.rect.height
        if not w or not h:
            return

        graph_w = w - self.PADDING_LEFT - self.PADDING_RIGHT
        graph_h = h - self.PADDING_TOP - self.PADDING_BOTTOM
        if graph_w <= 0 or graph_h <= 0:
            return

        self.graph_surface = pygame.Surface((w, h))
        self.graph_surface.fill(self.bg_color)

        time_data = self.data_ref.get("time", [])
        values_data = self.data_ref.get("values", [])

        if len(time_data) < 2 or len(values_data) < 2:
            # Not enough data yet
            no_data_font = pygame.font.SysFont(None, 32)
            text = no_data_font.render("Waiting for data...", True, (180, 180, 180))
            self.graph_surface.blit(
                text,
                (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2),
            )
            return

        min_val = min(values_data)
        max_val = max(values_data)
        if max_val == min_val:
            max_val += 1

        # Background for the graph area
        graph_rect = pygame.Rect(
            self.PADDING_LEFT, self.PADDING_TOP, graph_w, graph_h
        )
        pygame.draw.rect(self.graph_surface, (20, 20, 25), graph_rect)

        # Draw axes
        axis_color = (200, 200, 200)
        x_axis_y = self.PADDING_TOP + graph_h
        pygame.draw.line(
            self.graph_surface, axis_color,
            (self.PADDING_LEFT, x_axis_y),
            (self.PADDING_LEFT + graph_w, x_axis_y), 2,
        )  # X axis
        pygame.draw.line(
            self.graph_surface, axis_color,
            (self.PADDING_LEFT, self.PADDING_TOP),
            (self.PADDING_LEFT, x_axis_y), 2,
        )  # Y axis

        # Data line
        points: list[tuple[int, int]] = []
        n = len(time_data)
        for i in range(n):
            x = self.PADDING_LEFT + int(i / (n - 1) * graph_w)
            y_norm = (values_data[i] - min_val) / (max_val - min_val)
            y = self.PADDING_TOP + int(graph_h * (1 - y_norm))
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.aalines(
                self.graph_surface, self.line_color, False, points, 2
            )

        # Title (left-aligned so buttons can sit on the right)
        font_title = pygame.font.SysFont(None, 28, bold=True)
        title_surf = font_title.render(self.title, True, P_FG)
        self.graph_surface.blit(title_surf, (self.PADDING_LEFT, 8))

        # Axis labels
        font_label = pygame.font.SysFont(None, 22)
        # X-axis label
        xlabel_surf = font_label.render(self.xlabel, True, (220, 220, 220))
        self.graph_surface.blit(
            xlabel_surf,
            (w // 2 - xlabel_surf.get_width() // 2, h - 28),
        )
        # Y-axis label (rotated)
        ylabel_surf = font_label.render(self.ylabel, True, (220, 220, 220))
        ylabel_rot = pygame.transform.rotate(ylabel_surf, 90)
        self.graph_surface.blit(
            ylabel_rot,
            (10, h // 2 - ylabel_rot.get_height() // 2),
        )

        # Axis tick marks and values
        self._draw_ticks(graph_w, graph_h, min_val, max_val, n, axis_color)

    def _draw_ticks(
        self,
        graph_w: int,
        graph_h: int,
        y_min: float,
        y_max: float,
        data_len: int,
        axis_color: tuple[int, int, int],
    ) -> None:
        """Draw tick marks and numeric labels on both axes.

        Args:
            graph_w: Width of the graph area in pixels.
            graph_h: Height of the graph area in pixels.
            y_min: Minimum Y-axis value.
            y_max: Maximum Y-axis value.
            data_len: Number of data points (affects X-axis ticks).
            axis_color: Colour for tick lines and labels.
        """
        assert self.graph_surface is not None
        tick_font = pygame.font.SysFont(None, self.TICK_FONT_SIZE)
        x_axis_y = self.PADDING_TOP + graph_h

        # ── Y-axis ticks (value labels) ──
        for i in range(self.TICK_COUNT + 1):
            frac = i / self.TICK_COUNT
            val = y_min + frac * (y_max - y_min)
            y_px = x_axis_y - int(frac * graph_h)

            # Tick line
            pygame.draw.line(
                self.graph_surface, self.TICK_COLOR,
                (self.PADDING_LEFT - self.TICK_LENGTH, y_px),
                (self.PADDING_LEFT, y_px), 1,
            )
            # Label
            if abs(val) < 1e4:
                label = f"{val:.3f}" if val != int(val) else f"{int(val)}"
            else:
                label = f"{val:.3e}"
            lbl_surf = tick_font.render(label, True, self.TICK_COLOR)
            self.graph_surface.blit(
                lbl_surf,
                (self.PADDING_LEFT - self.TICK_LENGTH - lbl_surf.get_width() - 4,
                 y_px - lbl_surf.get_height() // 2),
            )

        # ── X-axis ticks (step numbers) ──
        for i in range(self.TICK_COUNT + 1):
            frac = i / self.TICK_COUNT
            x_px = self.PADDING_LEFT + int(frac * graph_w)

            # Tick line
            pygame.draw.line(
                self.graph_surface, self.TICK_COLOR,
                (x_px, x_axis_y),
                (x_px, x_axis_y + self.TICK_LENGTH), 1,
            )
            # Label (step number)
            step = int(frac * (data_len - 1)) if data_len > 1 else 0
            lbl_surf = tick_font.render(str(step), True, self.TICK_COLOR)
            self.graph_surface.blit(
                lbl_surf,
                (x_px - lbl_surf.get_width() // 2,
                 x_axis_y + self.TICK_LENGTH + 3),
            )

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def _export_image(self) -> None:
        """Export the current graph as a PNG file."""
        if self.graph_surface:
            try:
                filename = f"graph_{pygame.time.get_ticks()}.png"
                pygame.image.save(self.graph_surface, filename)
                print(f"Graph saved as {filename}")
            except Exception as e:
                print(f"Error saving graph image: {e}")

    def _export_csv(self) -> None:
        """Export the data series to a CSV file."""
        try:
            time_data = self.data_ref.get("time", [])
            values_data = self.data_ref.get("values", [])

            filename = f"data_{pygame.time.get_ticks()}.csv"
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([self.xlabel, self.ylabel])
                for t, v in zip(time_data, values_data):
                    writer.writerow([t, v])

            print(f"Data exported to {filename}")
        except Exception as e:
            print(f"Error exporting CSV: {e}")
