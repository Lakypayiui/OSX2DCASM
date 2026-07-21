import pygame
import csv
from typing import Optional, Dict, List, Any
from core.config import *
from widgets.button import Button  

class GraphWidget:
    """
    Widget para graficar series temporales (una gráfica por widget).
    Diseñado para mostrar entropía o población en el simulador de autómatas celulares.
    """

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        data_ref: Dict[str, List],
        title: str = "Gráfica",
        xlabel: str = "Tiempo (pasos)",
        ylabel: str = "Valor",
        show_exports: bool = True,
        line_color: tuple[int, int, int] = (255, 100, 100),
        bg_color: tuple[int, int, int] = (30, 30, 35),
    ) -> None:
        """
        Inicializa el widget de gráfica.

        Args:
            rect: Posición y tamaño (x, y, width, height).
            data_ref: Referencia mutable a los datos. Debe ser un dict con:
                      {'time': list[float|int], 'values': list[float|int]}
            title: Título de la gráfica.
            xlabel: Etiqueta del eje X.
            ylabel: Etiqueta del eje Y.
            show_exports: Mostrar botones de exportar imagen y CSV.
            line_color: Color de la línea de la gráfica.
            bg_color: Color de fondo del área de gráfica.
        """
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.data_ref: Dict[str, List] = data_ref
        self.title: str = title
        self.xlabel: str = xlabel
        self.ylabel: str = ylabel
        self.line_color: tuple[int, int, int] = line_color
        self.bg_color: tuple[int, int, int] = bg_color

        self.show_exports: bool = show_exports
        self.dirty: bool = True
        self.graph_surface: Optional[pygame.Surface] = None

        # Padding para ejes y etiquetas
        self.padding_left = 65
        self.padding_right = 20
        self.padding_top = 45
        self.padding_bottom = 50

        # Botones de exportación
        self.btn_export_img: Optional[Button] = None
        self.btn_export_csv: Optional[Button] = None

        if self.show_exports:
            btn_h = 32
            btn_w = 140
            gap = 12
            y = self.rect.bottom - btn_h - 12

            self.btn_export_img = Button(
                rect=(self.rect.left + 20, y, btn_w, btn_h),
                label="Guardar Imagen",
                toggle=False,
                bg=(70, 70, 80),
                fg=(240, 240, 240)
            )
            self.btn_export_csv = Button(
                rect=(self.rect.left + 20 + btn_w + gap, y, btn_w, btn_h),
                label="Exportar CSV",
                toggle=False,
                bg=(70, 70, 80),
                fg=(240, 240, 240)
            )

    def set_dirty(self) -> None:
        """Marca la gráfica como sucia para que se redibuje en el próximo draw."""
        self.dirty = True

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """
        Procesa eventos (principalmente clicks en los botones).

        Returns:
            True si se procesó un evento importante (click en botón).
        """
        clicked = False

        if self.btn_export_img:
            if self.btn_export_img.handle_event(ev):
                self._export_image()
                clicked = True

        if self.btn_export_csv:
            if self.btn_export_csv.handle_event(ev):
                self._export_csv()
                clicked = True

        return clicked

    def _export_image(self) -> None:
        """Exporta la gráfica actual como imagen PNG."""
        if self.graph_surface:
            try:
                filename = f"graph_{pygame.time.get_ticks()}.png"
                pygame.image.save(self.graph_surface, filename)
                print(f"✅ Gráfica guardada como {filename}")
            except Exception as e:
                print(f"❌ Error al guardar imagen: {e}")

    def _export_csv(self) -> None:
        """Exporta los datos a un archivo CSV."""
        try:
            time_data = self.data_ref.get('time', [])
            values_data = self.data_ref.get('values', [])

            filename = f"data_{pygame.time.get_ticks()}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([self.xlabel, self.ylabel])
                for t, v in zip(time_data, values_data):
                    writer.writerow([t, v])

            print(f"✅ Datos exportados a {filename}")
        except Exception as e:
            print(f"❌ Error al exportar CSV: {e}")

    def _draw_graph(self, surf: pygame.Surface) -> None:
        """Dibuja la gráfica en un surface interno (cache)."""
        if not self.rect.width or not self.rect.height:
            return

        graph_w = self.rect.width - self.padding_left - self.padding_right
        graph_h = self.rect.height - self.padding_top - self.padding_bottom

        if graph_w <= 0 or graph_h <= 0:
            return

        # Crear surface para la gráfica
        self.graph_surface = pygame.Surface((self.rect.width, self.rect.height))
        self.graph_surface.fill(self.bg_color)

        time_data = self.data_ref.get('time', [])
        values_data = self.data_ref.get('values', [])

        if len(time_data) < 2 or len(values_data) < 2:
            # Mensaje si no hay suficientes datos
            font = pygame.font.SysFont(None, 32)
            text = font.render("Esperando datos...", True, (180, 180, 180))
            self.graph_surface.blit(text, (self.rect.width//2 - text.get_width()//2,
                                         self.rect.height//2 - text.get_height()//2))
            return

        # Calcular rangos
        min_val = min(values_data)
        max_val = max(values_data)
        if max_val == min_val:
            max_val += 1

        # Dibujar fondo del área de gráfica
        graph_rect = pygame.Rect(
            self.padding_left, self.padding_top, graph_w, graph_h
        )
        pygame.draw.rect(self.graph_surface, (20, 20, 25), graph_rect)

        # Dibujar ejes
        axis_color = (200, 200, 200)
        pygame.draw.line(self.graph_surface, axis_color,
                        (self.padding_left, self.padding_top + graph_h),
                        (self.padding_left + graph_w, self.padding_top + graph_h), 2)  # X
        pygame.draw.line(self.graph_surface, axis_color,
                        (self.padding_left, self.padding_top),
                        (self.padding_left, self.padding_top + graph_h), 2)          # Y

        # Dibujar línea de datos
        points = []
        for i in range(len(time_data)):
            x = self.padding_left + int(i / (len(time_data) - 1) * graph_w)
            y_norm = (values_data[i] - min_val) / (max_val - min_val)
            y = self.padding_top + int(graph_h * (1 - y_norm))
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.aalines(self.graph_surface, self.line_color, False, points, 2)

        # Título
        font_title = pygame.font.SysFont(None, 28, bold=True)
        title_surf = font_title.render(self.title, True, P_FG)
        self.graph_surface.blit(title_surf, (self.rect.width//2 - title_surf.get_width()//2, 12))

        # Etiquetas de ejes
        font_label = pygame.font.SysFont(None, 22)
        # X label
        xlabel_surf = font_label.render(self.xlabel, True, (220, 220, 220))
        self.graph_surface.blit(xlabel_surf,
                               (self.rect.width//2 - xlabel_surf.get_width()//2,
                                self.rect.height - 28))

        # Y label (rotada)
        ylabel_surf = font_label.render(self.ylabel, True, (220, 220, 220))
        ylabel_rot = pygame.transform.rotate(ylabel_surf, 90)
        self.graph_surface.blit(ylabel_rot,
                               (18, self.rect.height//2 - ylabel_rot.get_width()//2))

        # Pequeños ticks (opcional)
        pygame.draw.line(self.graph_surface, axis_color,
                        (self.padding_left, self.padding_top + graph_h),
                        (self.padding_left - 8, self.padding_top + graph_h), 2)
        pygame.draw.line(self.graph_surface, axis_color,
                        (self.padding_left, self.padding_top),
                        (self.padding_left - 8, self.padding_top), 2)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        """
        Dibuja el widget completo en la superficie destino.

        Args:
            surf: Superficie donde dibujar (normalmente la pantalla).
            font: Fuente para los botones.
        """
        # Redibujar gráfica solo si es necesario
        if self.dirty or self.graph_surface is None:
            self._draw_graph(surf)
            self.dirty = False

        if self.graph_surface:
            surf.blit(self.graph_surface, self.rect.topleft)

        # Dibujar botones
        if self.btn_export_img:
            self.btn_export_img.draw(surf, font)
        if self.btn_export_csv:
            self.btn_export_csv.draw(surf, font)

        # Borde del widget
        pygame.draw.rect(surf, P_BORDER, self.rect, 1, border_radius=6)