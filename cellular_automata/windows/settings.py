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
        self.mirror_var = tk.BooleanVar(value=state.mirror)
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

        ttk.Checkbutton(
            self, text="Mirror cells", variable=self.mirror_var
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self,
            text="Use commas or new lines for titles.",
            justify="left",
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 12))

        button_row = ttk.Frame(self)
        button_row.grid(row=10, column=0, columnspan=2, sticky="ew")
        button_row.columnconfigure(0, weight=1)
        ttk.Button(button_row, text="Apply settings", command=self.apply).grid(row=0, column=1, sticky="e")
        ttk.Button(button_row, text="Save settings and table", command=self.save).grid(row=0, column=2, sticky="e")
        ttk.Button(button_row, text="Load settings and table", command=self.load).grid(row=0, column=3, sticky="e")

        self.pack(fill="both", expand=True)

    def _add_field(self, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

    def apply(self) -> None:
        mirror = self.mirror_var.get()
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            cell_size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Rows, columns, and cell size must be integers.")
            return

        if mirror and rows != cols:
            messagebox.showerror("Invalid settings", "Rows and columns must be equal when mirroring is enabled.")
            return

        self.app_state.shape = self.shape_var.get()
        self.app_state.placement = self.placement_var.get()
        self.app_state.resize_grid(rows, cols)
        self.app_state.cell_size = cell_size
        self.app_state.titles = parse_titles(self.titles_var.get(), self.app_state.cols)
        self.app_state.hide_text = self.hide_text_var.get()
        self.app_state.mirror = mirror
        self.on_apply()

    def save(self) -> None:
        from ..save import save
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if file_path:
            self.apply()
            save(self.app_state, file_path)
            messagebox.showinfo("Settings saved", f"Settings and table saved to {file_path}")

    def load(self) -> None:
        from ..save import load
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if file_path:
            try:
                loaded_state = load(file_path)
                self.app_state.rows = loaded_state.rows
                self.app_state.cols = loaded_state.cols
                self.app_state.cell_size = loaded_state.cell_size
                self.app_state.shape = loaded_state.shape
                self.app_state.placement = loaded_state.placement
                self.app_state.titles = loaded_state.titles
                self.app_state.cells = loaded_state.cells
                self.app_state.hide_text = loaded_state.hide_text
                self.app_state.mirror = loaded_state.mirror

                # Update the UI to reflect the loaded settings
                self.rows_var.set(str(self.app_state.rows))
                self.cols_var.set(str(self.app_state.cols))
                self.size_var.set(str(self.app_state.cell_size))
                self.shape_var.set(self.app_state.shape)
                self.placement_var.set(self.app_state.placement)
                self.titles_var.set(", ".join(self.app_state.titles))
                self.hide_text_var.set(self.app_state.hide_text)
                self.mirror_var.set(self.app_state.mirror)

                self.on_apply()
                messagebox.showinfo("Settings loaded", f"Settings and table loaded from {file_path}")
            except Exception as e:
                messagebox.showerror("Error loading settings", f"An error occurred while loading settings: {e}")
