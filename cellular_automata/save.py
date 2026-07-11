from typing import Any
import json

from .core import AppState, CellData, CellPlacement, CellShape


def save(app_state: AppState, file_path: str) -> None:
    """Save the current application state to a JSON file."""
    data: dict[str, Any] = {
        "rows": app_state.rows,
        "cols": app_state.cols,
        "shape": app_state.shape,
        "placement": app_state.placement,
        "titles": app_state.titles,
        "cells": [[{"text": cell.text, "background": cell.background} for cell in row] for row in app_state.cells],
        "hide_text": getattr(app_state, "hide_text", False),
        "mirror": getattr(app_state, "mirror", True),
    }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def load(file_path: str) -> AppState:
    """Load the application state from a JSON file."""
    with open(file_path, "r") as f:
        data: dict[str, Any] = json.load(f)

    app_state = AppState(
        rows=data.get("rows", 3),
        cols=data.get("cols", 3),
        shape=data.get("shape", CellShape.SQUARE),
        placement=data.get("placement", CellPlacement.OFFSET),
        titles=data.get("titles", [f"{index + 1}" for index in range(data.get("cols", 3))]),
        cells=[
            [CellData(text=cell.get("text", ""), background=cell.get("background", "#ffffff")) for cell in row]
            for row in data.get("cells", [[{"text": ""}] * data.get("cols", 3)] * data.get("rows", 3))
        ],
        hide_text=data.get("hide_text", False),
        mirror=data.get("mirror", True),
    )
    return app_state
