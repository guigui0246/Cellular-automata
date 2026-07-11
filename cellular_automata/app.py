from __future__ import annotations

import tkinter as tk

from .core import AppState
from .windows.renderer import RendererWindow
from .windows.settings import SettingsWindow
from .windows.table import TableWindow


class Application:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Settings")
        self.root.geometry("420x420")
        self.state = AppState()

        self.renderer = RendererWindow(self.root, self.state)
        self.table = TableWindow(self.root, self.state, self.on_state_change)
        self.settings = SettingsWindow(self.root, self.state, self.on_apply_settings)
        self.root.protocol("WM_DELETE_WINDOW", self.close_all)
        self.renderer.protocol("WM_DELETE_WINDOW", self.close_all)
        self.table.protocol("WM_DELETE_WINDOW", self.close_all)

    def on_apply_settings(self) -> None:
        self.table.rebuild()
        self.on_state_change()

    def on_state_change(self) -> None:
        self.renderer.invalidate_cache()
        self.renderer.schedule_redraw()

    def close_all(self) -> None:
        for window in (self.renderer, self.table, self.root):
            try:
                window.destroy()
            except tk.TclError:
                pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    Application().run()


if __name__ == "__main__":
    main()
