# Cellular-automata
see https://www.youtube.com/watch?v=6rIhJLKBY2E

## Run

Start the app with:

```bash
python app.py
```

The program opens three windows:

1. Settings, where you choose the grid shape, placement, size, and titles.
2. Table, where you edit the repeating cell content and colors.
3. Renderer, which shows an infinite automaton where each row is generated from the rows above it.

## Structure

- [app.py](app.py) is a small entrypoint.
- [cellular_automata/core.py](cellular_automata/core.py) holds shared state and helpers.
- [cellular_automata/windows/settings.py](cellular_automata/windows/settings.py) contains the settings window.
- [cellular_automata/windows/table.py](cellular_automata/windows/table.py) contains the table editor.
- [cellular_automata/windows/renderer.py](cellular_automata/windows/renderer.py) contains the infinite renderer.
