from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Sequence


type Rules = List[List[CellData]]


class CellShape(StrEnum):
    SQUARE = "square"
    HEXAGONAL = "hexagonal"


class CellPlacement(StrEnum):
    ALIGNED = "aligned"
    OFFSET = "offset"


@dataclass
class CellData:
    text: str = ""
    background: str = "#ffffff"


def parse_titles(raw_text: str, count: int) -> List[str]:
    values = [item.strip() for item in raw_text.replace("\n", ",").split(",")]
    titles = [item for item in values if item]
    if len(titles) >= count:
        return titles[:count]
    for index in range(len(titles), count):
        titles.append(f"{index + 1}")
    return titles


def best_text_color(background: str) -> str:
    try:
        red = int(background[1:3], 16)
        green = int(background[3:5], 16)
        blue = int(background[5:7], 16)
    except Exception:
        return "#000000"
    brightness = (red * 299 + green * 587 + blue * 114) / 1000
    return "#000000" if brightness >= 150 else "#ffffff"


def _parse_hex_color(background: str) -> tuple[int, int, int] | None:
    try:
        return int(background[1:3], 16), int(background[3:5], 16), int(background[5:7], 16)
    except Exception:
        return None


def blend_hex_colors(backgrounds: Sequence[str]) -> str:
    red_total = 0.0
    green_total = 0.0
    blue_total = 0.0
    count = 0

    for background in backgrounds:
        parsed = _parse_hex_color(background)
        if parsed is None:
            continue
        red, green, blue = parsed
        red_total += red
        green_total += green
        blue_total += blue
        count += 1

    if count == 0:
        return "#1e1e1e"

    return f"#{round(red_total / count):02x}{round(green_total / count):02x}{round(blue_total / count):02x}"


def evolve_cell(parents: Sequence[CellData], rules: Rules, titles: List[str]) -> CellData:
    active_parents = [parent for parent in parents if parent.text in titles]
    if not active_parents:
        return CellData()
    if len(active_parents) == 1:
        parent = active_parents[0]
        return CellData(text=parent.text, background=parent.background)

    parent_texts = [parent.text for parent in active_parents[:2]]
    indexes = [titles.index(text) for text in parent_texts]
    return CellData(
        text=rules[indexes[0]][indexes[1]].text,
        background=rules[indexes[0]][indexes[1]].background,
    )


def evolve_row(
    previous_row: Sequence[CellData],
    column_count: int,
    rules: Rules,
    titles: List[str],
    nb_parents: int = 2
) -> list[CellData]:
    normalized = previous_row
    width = len(normalized) + 2
    next_row: list[CellData] = [CellData() for _ in range(width)]

    for column in range(width):
        parents = []
        for i in range(nb_parents):
            col = column + i - 1
            if 0 <= col < len(normalized):
                parents.append(normalized[col])
            else:
                parents.append(CellData())
        next_row[column] = evolve_cell(parents, rules, titles)
    return next_row


def center_row(row: Sequence[CellData]) -> list[CellData]:
    active_indexes = [index for index, cell in enumerate(row) if cell.text]
    if not active_indexes:
        return [CellData() for _ in row]

    first_active = active_indexes[0]
    last_active = active_indexes[-1]
    active_width = last_active - first_active + 1
    target_left = max(0, (len(row) - active_width) // 2)
    shift = target_left - first_active

    centered_row = [CellData() for _ in row]
    for index, cell in enumerate(row):
        target_index = index + shift
        if 0 <= target_index < len(centered_row):
            centered_row[target_index] = cell
    return centered_row


def build_automaton_rows(
    seed_rows: str,
    required_rows: int,
    column_count: int,
    rules: Rules,
    titles: List[str]
) -> list[list[CellData]]:
    seed_row = [CellData() for _ in range(column_count)]
    seed_row_list = seed_rows.strip().removeprefix("[").removesuffix("]").split(",")
    parsed_seed: list[tuple[str, int]] = []
    finite_cells = 0
    inf_cells = 0

    for seed_token in seed_row_list:
        if "*" in seed_token:
            thing, amount = seed_token.split("*")
        else:
            thing, amount = seed_token, "1"
        text = thing.strip().strip("\"")
        if amount == "inf":
            parsed_seed.append((text, -1))
            inf_cells += 1
        else:
            count = max(0, int(amount))
            parsed_seed.append((text, count))
            finite_cells += count

    blank_cells = max(0, column_count - finite_cells)
    blank_share = blank_cells // inf_cells if inf_cells else 0
    blank_remainder = blank_cells % inf_cells if inf_cells else 0

    idx = 0
    for text, count in parsed_seed:
        if count == -1:
            count = blank_share + (1 if blank_remainder > 0 else 0)
            if blank_remainder > 0:
                blank_remainder -= 1
        for _ in range(count):
            if idx >= column_count:
                break
            if text.startswith("titles[") and text.endswith("]"):
                try:
                    table_index = int(text[7:-1])
                    if 0 <= table_index < len(titles):
                        text = titles[table_index]
                except ValueError:
                    pass
            seed_row[idx] = CellData(text=text)
            idx += 1

    rows = [seed_row]

    while len(rows) < required_rows:
        rows.append(center_row(evolve_row(rows[-1], column_count, rules, titles)))

    # print(rows)
    return rows


@dataclass
class AppState:
    rows: int = 3
    cols: int = 3
    cell_size: int = 60
    shape: str = CellShape.SQUARE
    placement: str = CellPlacement.OFFSET
    titles: List[str] = field(default_factory=lambda: [f"{index + 1}" for index in range(AppState.cols)])
    cells: Rules = field(
        default_factory=lambda: [[CellData(text='1') for _ in range(AppState.cols)] for _ in range(AppState.rows)]
    )
    hide_text: bool = True
    default_colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
    starting_state: str = "[\"\"*inf,titles[0],\"\"*inf]"

    def resize_grid(self, rows: int, cols: int) -> None:
        rows = max(1, min(64, int(rows)))
        cols = max(1, min(64, int(cols)))
        old_cells = self.cells
        new_cells = [[CellData() for _ in range(cols)] for _ in range(rows)]
        for row in range(min(rows, len(old_cells))):
            for col in range(min(cols, len(old_cells[row]))):
                new_cells[row][col] = old_cells[row][col]
        self.rows = rows
        self.cols = cols
        self.cells = new_cells
        self.titles = parse_titles(", ".join(self.titles), cols)
