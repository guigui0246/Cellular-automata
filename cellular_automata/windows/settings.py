from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from ..core import AppState, CellPlacement, CellShape, parse_titles


class SettingsWindow(ttk.Frame):
    def __init__(self, master: tk.Tk, state: AppState, on_apply: Callable[[], None]) -> None:
        super().__init__(master, padding=12)
        self.app_state = state
        self.on_apply = on_apply

        self.rows_var = tk.StringVar(value=str(state.rows))
        self.cols_var = tk.StringVar(value=str(state.cols))
        self.size_var = tk.StringVar(value=str(state.cell_size))
        self.shape_var = tk.StringVar(value=state.shape)
        self.placement_var = tk.StringVar(value=state.placement)
        self.titles_var = tk.StringVar(value=", ".join(state.titles))
        self.hide_text_var = tk.BooleanVar(value=state.hide_text)

        self._build()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        ttk.Label(
            self, text="Settings", font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._add_field("Rows", self.rows_var, 1)
        self._add_field("Columns", self.cols_var, 2)
        self._add_field("Cell size", self.size_var, 3)

        ttk.Label(self, text="Shape").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(
            self, textvariable=self.shape_var, values=list(CellShape), state="readonly"
        ).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(self, text="Placement").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Combobox(
            self, textvariable=self.placement_var, values=list(CellPlacement), state="readonly"
        ).grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(self, text="Column/Row titles").grid(row=6, column=0, sticky="nw", pady=4)
        ttk.Entry(self, textvariable=self.titles_var).grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(
            self, text="Hide text", variable=self.hide_text_var
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self,
            text="The table window repeats these cells infinitely in the renderer.\nUse commas or new lines for titles.",
            justify="left",
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 12))

        button_row = ttk.Frame(self)
        button_row.grid(row=9, column=0, columnspan=2, sticky="ew")
        button_row.columnconfigure(0, weight=1)
        ttk.Button(button_row, text="Apply settings", command=self.apply).grid(row=0, column=1, sticky="e")

        self.pack(fill="both", expand=True)

    def _add_field(self, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

    def apply(self) -> None:
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            cell_size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Rows, columns, and cell size must be integers.")
            return

        self.app_state.shape = self.shape_var.get()
        self.app_state.placement = self.placement_var.get()
        self.app_state.resize_grid(rows, cols)
        self.app_state.cell_size = cell_size
        self.app_state.titles = parse_titles(self.titles_var.get(), self.app_state.cols)
        self.app_state.hide_text = self.hide_text_var.get()
        self.on_apply()
