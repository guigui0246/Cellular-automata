from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from ..core import AppState, CellData, build_automaton_rows, best_text_color


class RendererWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, state: AppState) -> None:
        super().__init__(master)
        self.state = state
        self.title("Renderer")
        self.geometry("1100x800")

        self.toolbar = ttk.Frame(self, padding=(8, 8, 8, 4))
        self.toolbar.pack(fill="x")
        ttk.Button(self.toolbar, text="Center view", command=self.center_view).pack(side="left")
        self.status = ttk.Label(self.toolbar, text="Drag with the left or middle mouse button to pan")
        self.status.pack(side="left", padx=(12, 0))

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e1e")
        self.canvas.pack(fill="both", expand=True)

        self.pan_x = 0.0
        self.pan_y = 0.0
        self.drag_anchor = None
        self.pending_redraw = None
        self.row_cache: list[list[CellData]] = []

        self.canvas.bind("<Configure>", self.schedule_redraw)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-4>", self.zoom)
        self.canvas.bind("<Button-5>", self.zoom)
        self.bind("<Control-r>", lambda _event: self.center_view())
        self.after(100, self.center_view)

    def center_view(self) -> None:
        if self.canvas.winfo_width() > 1 and self.canvas.winfo_height() > 1:
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.schedule_redraw()

    def schedule_redraw(self, _event: tk.Event | None = None) -> None:
        if self.pending_redraw is not None:
            self.after_cancel(self.pending_redraw)
        self.pending_redraw = self.after(16, self.redraw)

    def start_pan(self, event: tk.Event) -> None:
        self.drag_anchor = (event.x, event.y, self.pan_x, self.pan_y)

    def pan(self, event: tk.Event) -> None:
        if self.drag_anchor is None:
            return
        start_x, start_y, pan_x, pan_y = self.drag_anchor  # type: ignore
        self.pan_x: float = pan_x - (event.x - start_x)
        self.pan_y: float = pan_y - (event.y - start_y)
        self.schedule_redraw()

    def zoom(self, event: tk.Event) -> None:
        if getattr(event, "num", None) == 4:
            self.zoom_at(getattr(event, "x", None), getattr(event, "y", None), 0.9)
            return
        if getattr(event, "num", None) == 5:
            self.zoom_at(getattr(event, "x", None), getattr(event, "y", None), 1.1)
            return
        delta = getattr(event, "delta", 0)
        if delta > 0:
            self.zoom_at(getattr(event, "x", None), getattr(event, "y", None), 0.9)
        elif delta < 0:
            self.zoom_at(getattr(event, "x", None), getattr(event, "y", None), 1.1)

    def zoom_at(self, anchor_x: int | None, anchor_y: int | None, factor: float) -> None:
        if anchor_x is None or anchor_y is None:
            anchor_x = self.canvas.winfo_width() // 2
            anchor_y = self.canvas.winfo_height() // 2

        old_size = float(self.state.cell_size)
        self.state.cell_size = max(16, min(180, int(self.state.cell_size * factor)))

        if self.state.cell_size != old_size:
            scale = self.state.cell_size / old_size
            center_x = self.canvas.winfo_width() / 2
            center_y = self.canvas.winfo_height() / 2
            self.pan_x = scale * self.pan_x + (scale - 1.0) * (anchor_x - center_x)
            self.pan_y = scale * self.pan_y + (scale - 1.0) * (anchor_y - center_y)
        self.schedule_redraw()

    def invalidate_cache(self) -> None:
        self.row_cache = []

    def _cell_fill(self, cell: CellData) -> str:
        background = cell.background.lower()
        if background not in {"#ffffff", "#fff"}:
            return cell.background
        if not cell.text.strip():
            return "#ffffff"
        if cell.text in self.state.titles:
            index = self.state.titles.index(cell.text)
            return self.state.default_colors[index % len(self.state.default_colors)]
        return cell.background

    def _cell_outline(self, fill: str) -> str:
        return "#ffffff"

    def redraw(self) -> None:
        self.pending_redraw = None
        self.canvas.delete("all")

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.status.configure(
            text=(
                f"{self.state.shape} / {self.state.placement} / size {self.state.cell_size} "
                f"/ seed rows {self.state.rows}"
            )
        )

        if self.state.shape == "hexagonal":
            self._draw_hex_grid(width, height)
        else:
            self._draw_square_grid(width, height)

    def _row_for_generation(self, generation: int) -> list[CellData]:
        required_rows = max(generation + 1, self.state.rows)
        if len(self.row_cache) < required_rows:
            self.row_cache = build_automaton_rows(
                self.state.starting_state,
                required_rows,
                self.state.cols,
                self.state.cells,
                self.state.titles
            )
        return self.row_cache[generation]

    def _draw_square_grid(self, width: int, height: int) -> None:
        size = float(self.state.cell_size)
        offset = size / 2 if self.state.placement == "offset" else 0.0
        visible_columns = max(1, int(math.ceil(width / size)) + 4)
        top = math.floor((self.pan_y - height / 2 - size * 2) / size) - 2
        bottom = math.ceil((self.pan_y + height / 2 + size * 2) / size) + 2
        center_x = width / 2
        center_y = height / 2

        for row in range(max(0, top), bottom + 1):
            row_shift = offset if row % 2 else 0.0
            row_cells = self._row_for_generation(row)
            row_center = (len(row_cells) - 1) / 2.0
            first_visible = int(round(row_center - visible_columns / 2))
            last_visible = first_visible + visible_columns
            for col in range(first_visible, last_visible + 1):
                x0 = center_x + (col - row_center) * size + row_shift - self.pan_x
                y0 = center_y + row * size - self.pan_y
                x1 = x0 + size
                y1 = y0 + size
                cell = row_cells[col] if 0 <= col < len(row_cells) else CellData()
                fill = self._cell_fill(cell)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=self._cell_outline(fill), width=1)
                if cell.text and not self.state.hide_text:
                    self.canvas.create_text(
                        (x0 + x1) / 2,
                        (y0 + y1) / 2,
                        text=cell.text,
                        fill=best_text_color(fill),
                        font=("Segoe UI", max(8, int(size / 4)), "bold"),
                    )

    def _draw_hex_grid(self, width: int, height: int) -> None:
        radius = float(self.state.cell_size) / 2.0
        column_step = math.sqrt(3) * radius
        row_step = 1.5 * radius
        visible_columns = max(1, int(math.ceil(width / column_step)) + 4)
        top = math.floor((self.pan_y - height / 2 - row_step * 2) / row_step) - 3
        bottom = math.ceil((self.pan_y + height / 2 + row_step * 2) / row_step) + 3
        center_x = width / 2
        center_y = height / 2

        for row in range(max(0, top), bottom + 1):
            y = center_y + row * row_step - self.pan_y
            row_shift = column_step / 2 if self.state.placement == "offset" and row % 2 else 0.0
            row_cells = self._row_for_generation(row)
            row_center = (len(row_cells) - 1) / 2.0
            first_visible = int(round(row_center - visible_columns / 2))
            last_visible = first_visible + visible_columns
            for col in range(first_visible, last_visible + 1):
                x = center_x + (col - row_center) * column_step + row_shift - self.pan_x
                cell = row_cells[col] if 0 <= col < len(row_cells) else CellData()
                points = []
                for angle_degrees in (30, 90, 150, 210, 270, 330):
                    angle = math.radians(angle_degrees)
                    points.extend((x + radius * math.cos(angle), y + radius * math.sin(angle)))
                fill = self._cell_fill(cell)
                self.canvas.create_polygon(points, fill=fill, outline=self._cell_outline(fill), width=1)
                if cell.text and not self.state.hide_text:
                    self.canvas.create_text(
                        x,
                        y,
                        text=cell.text,
                        fill=best_text_color(fill),
                        font=("Segoe UI", max(7, int(radius / 2.2)), "bold"),
                    )
