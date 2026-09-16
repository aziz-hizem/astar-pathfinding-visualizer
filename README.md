# A* Pathfinding Visualizer

An interactive maze editor that visualizes the **A\* search algorithm** step by step. Draw walls, place a start and a goal, then watch the algorithm explore the grid and find the shortest path.

A\* is a classic *informed search* algorithm from artificial intelligence, used for route planning in games, robotics and navigation. It is implemented here from scratch, without any pathfinding library.

Built with **Python**, **Pygame** (grid rendering) embedded inside a **Tkinter** window (controls).

<!-- Screenshot / GIF: docs/demo.gif -->

## Features

- **Maze editor**: paint walls, place start/goal and erase cells with the mouse (20×20 grid)
- **Animated A\***: watch the search run, with pause/resume and speed control (x1 to x10)
- **Step-by-step mode**: advance the search one node expansion at a time to study how it works
- **Handles unreachable goals**: reports when no path exists
- **Save / load mazes** as JSON files (`mazes/` folder), with a prompt for unsaved changes on exit
- **Keyboard shortcuts** for tools, with AZERTY and QWERTY layouts

### Color legend

| Color | Meaning |
|---|---|
| 🟩 Green | Start cell |
| 🟥 Red | Goal cell |
| ⬛ Black | Wall |
| 🟦 Blue | Open set (frontier still to explore) |
| 🟧 Orange | Closed set (already explored) |
| 🟨 Yellow | Final shortest path |
| Cyan | Node currently being expanded |

## How the algorithm works

Each cell is a node scored with `f = g + h`:

- `g`: number of moves from the start
- `h`: Manhattan distance to the goal (admissible on a 4-directional grid, so the path found is optimal)

At each step the node with the lowest `f` is taken from the open set, moved to the closed set, and its unvisited neighbors (up, down, left, right) are added or updated. When the goal is reached, the path is rebuilt by following parent links back to the start.

The implementation lives in [`astar.py`](astar.py) and is written from scratch as a stepwise class (`AStarVisualizer`) so the GUI can render the state after every expansion.

## Getting started

Requires **Python 3.10+** on **Windows** (the Pygame canvas is embedded into Tkinter using a Windows video driver).

```bash
git clone https://github.com/aziz-hizem/astar-pathfinding-visualizer.git
cd astar-pathfinding-visualizer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python maze_editor.py
```

## Usage

1. Choose **Edit** mode and a tool (**Wall**, **Start**, **End**, **Erase**), then click on the grid.
2. Click **Run A\*** to animate the search, or **Run A\* Step-by-step** and press **Step** to advance manually.
3. Use **Pause/Play** and **− / +** to control the animation.
4. **Save**, **Save As** and **Load Maze** manage maze files in `mazes/`.

| Tool | AZERTY key | QWERTY key |
|---|---|---|
| Wall | `&` | `1` |
| Start | `é` | `2` |
| End | `"` | `3` |
| Erase | `'` | `4` |

> Editing the maze clears the previous search result. Changes are only written to disk when you press **Save**.

## Project structure

```
astar-pathfinding-visualizer/
├── astar.py          # Stepwise A* implementation
├── maze_editor.py    # Tkinter + Pygame editor and visualizer
├── mazes/            # Saved mazes (JSON grids)
│   ├── maze.json     # Default maze loaded at startup
│   └── maze2.json
└── requirements.txt
```

Maze files are 20×20 JSON grids where `0` = empty, `1` = wall, `2` = start, `3` = goal.

## License

[MIT](LICENSE)
