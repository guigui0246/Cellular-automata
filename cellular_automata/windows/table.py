from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, ttk
from typing import Callable

from ..core import AppState, best_text_color


class TableWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, state: AppState, on_change: Callable[[], None]) -> None:
        super().__init__(master)
        self.state = state
        self.on_change = on_change
        self.title("Table")
        self.geometry("900x700")

        self.container = ttk.Frame(self, padding=8)
        self.container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.container, highlightthickness=0)
        self.scroll_x = ttk.Scrollbar(self.container, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_inner)

        self.rebuild()

    def _update_scroll_region(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_inner(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.inner_id, width=max(event.width, self.inner.winfo_reqwidth()))

    def _set_cell_text(self, row: int, col: int, value: str) -> None:
        if self.state.cells[row][col].text == value:
            return
        self.state.cells[row][col].text = value
        self.on_change()

    def rebuild(self) -> None:
        for child in self.inner.winfo_children():
            child.destroy()

        ttk.Label(self.inner, text="").grid(row=0, column=0, padx=4, pady=4)
        for col, title in enumerate(self.state.titles):
            ttk.Label(self.inner, text=title, anchor="center", padding=4).grid(row=0, column=col + 1, sticky="nsew")

        for row_index in range(self.state.rows):
            ttk.Label(self.inner, text=self.state.titles[row_index], anchor="center", padding=4).grid(
                row=row_index + 1,
                column=0,
                sticky="nsew",
            )
            for col_index in range(self.state.cols):
                cell = self.state.cells[row_index][col_index]
                cell_frame = ttk.Frame(self.inner, padding=2)
                cell_frame.grid(row=row_index + 1, column=col_index + 1, sticky="nsew")
                text_var = tk.StringVar(value=cell.text)
                text_picker = ttk.Combobox(
                    cell_frame, textvariable=text_var, values=list(self.state.titles) + [""], state="readonly"
                )
                text_picker.grid(row=0, column=0, sticky="ew")
                text_picker.bind(
                    "<<ComboboxSelected>>",
                    lambda _event, row=row_index, col=col_index, variable=text_var: self._set_cell_text(
                        row,
                        col,
                        variable.get(),
                    ),
                )

                tk.Button(
                    cell_frame,
                    text="BG",
                    width=4,
                    relief="flat",
                    bg=cell.background,
                    fg=best_text_color(cell.background),
                    command=lambda r=row_index, c=col_index: self.choose_color(r, c),
                ).grid(row=0, column=1, sticky="e", padx=(4, 0))
                cell_frame.columnconfigure(0, weight=1)

        for index in range(self.state.cols + 1):
            self.inner.columnconfigure(index, weight=1)
        self._update_scroll_region()

    def choose_color(self, row: int, col: int) -> None:
        color = colorchooser.askcolor(title=f"Choose color for cell {row + 1}, {col + 1}")
        if not color or not color[1]:
            return
        self.state.cells[row][col].background = color[1]
        self.rebuild()
        self.on_change()
