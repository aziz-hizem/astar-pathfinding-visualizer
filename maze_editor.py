import pygame
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from astar import AStarVisualizer  # Your astar.py file

# ---------------- CONFIG ----------------
ROWS, COLS = 20, 20
CELL_SIZE = 30
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Maze storage
MAZE_DIR = "mazes"
os.makedirs(MAZE_DIR, exist_ok=True)

# Default file
DEFAULT_FILE = os.path.join(MAZE_DIR, "maze.json")

# ---------------- GRID ----------------
def create_grid(rows, cols, default=0):
    return [[default for _ in range(cols)] for _ in range(rows)]

def load_maze(filename=DEFAULT_FILE):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return create_grid(ROWS, COLS)

def save_maze(grid, filename=DEFAULT_FILE):
    with open(filename, "w") as f:
        json.dump(grid, f)

def get_color(value):
    if value == 0: return WHITE
    elif value == 1: return BLACK
    elif value == 2: return GREEN
    elif value == 3: return RED
    return WHITE

# ---------------- MAIN APPLICATION ----------------
class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A* Pathfinding Visualizer")
        self.current_file = DEFAULT_FILE
        self.unsaved_changes = False

        # Mode and tool
        self.mode = tk.StringVar(value="edit")
        self.tool = tk.StringVar(value="wall")
        self.keyboard_layout = tk.StringVar(value="AZERTY")  # Options: AZERTY/QWERTY

        # Load grid
        self.grid = load_maze(self.current_file)
        self.start_pos = self.find_cell(2)
        self.end_pos = self.find_cell(3)

        # A* visualizer attributes and playback controls
        self.astar = None
        self.astar_running = False
        self.astar_paused = False
        self.step_mode = False
        self.speed_level = 1
        self.astar_speed = 1.0  # seconds per step at x1
        self.last_step_time = 0

        # Pygame canvas embedded in Tkinter
        self.embed_frame = tk.Frame(root, width=WIDTH, height=HEIGHT)
        self.embed_frame.grid(row=0, column=0, padx=10, pady=10)
        os.environ['SDL_WINDOWID'] = str(self.embed_frame.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'windib'  # Windows specific
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # Control panel
        self.controls = tk.Frame(root)
        self.controls.grid(row=0, column=1, sticky="n", padx=10)

        # --- Now create controls (speed_label will work because astar_speed exists) ---
        self.create_controls()

        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Key>', self.handle_key_press)

        # Run loop
        self.running = True
        self.loop()

    # ---------------- UTILITIES ----------------
    def find_cell(self, value):
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == value:
                    return (r, c)
        return None

    # ---------------- GUI CONTROLS ----------------
    def create_controls(self):
        # Mode
        tk.Label(self.controls, text="Mode:").pack(anchor="w")
        ttk.Radiobutton(self.controls, text="Edit", variable=self.mode, value="edit").pack(anchor="w")
        ttk.Radiobutton(self.controls, text="Lock", variable=self.mode, value="lock").pack(anchor="w")

        # Tool
        tk.Label(self.controls, text="Tool:").pack(anchor="w", pady=(10,0))
        ttk.Radiobutton(self.controls, text="Wall", variable=self.tool, value="wall").pack(anchor="w")
        ttk.Radiobutton(self.controls, text="Start", variable=self.tool, value="start").pack(anchor="w")
        ttk.Radiobutton(self.controls, text="End", variable=self.tool, value="end").pack(anchor="w")
        ttk.Radiobutton(self.controls, text="Erase", variable=self.tool, value="erase").pack(anchor="w")

        # Buttons
        ttk.Button(self.controls, text="Clear All", command=self.clear_all).pack(pady=(20,5))
        ttk.Button(self.controls, text="Load Maze", command=self.load_maze_file).pack(pady=5)
        ttk.Button(self.controls, text="Save", command=self.save).pack(pady=5)
        ttk.Button(self.controls, text="Save As", command=self.save_as).pack(pady=5)
        ttk.Button(self.controls, text="Options", command=self.options_menu).pack(pady=(20,0))
        ttk.Button(self.controls, text="Run A*", command=self.start_astar).pack(pady=5)
        ttk.Button(self.controls, text="Run A* Step-by-step", command=self.start_astar_stepwise).pack(pady=5)

        # Playback controls (disabled until Run A*)
        self.play_pause_btn = ttk.Button(self.controls, text="Pause", command=self.toggle_pause, state="disabled")
        self.play_pause_btn.pack(pady=5)
        step_frame = tk.Frame(self.controls)
        step_frame.pack(pady=5)
        self.speed_down_btn = ttk.Button(step_frame, text="-", command=lambda: self.change_speed(-1), state="disabled")
        self.speed_down_btn.pack(side="left")
        self.speed_label = tk.Label(step_frame, text=f"x{self.speed_level}")
        self.speed_label.pack(side="left", padx=5)
        self.speed_up_btn = ttk.Button(step_frame, text="+", command=lambda: self.change_speed(1), state="disabled")
        self.speed_up_btn.pack(side="left")
        self.step_btn = ttk.Button(self.controls, text="Step", command=self.step_astar, state="disabled")
        self.step_btn.pack(pady=5)

        ttk.Button(self.controls, text="Info", command=self.show_info).pack(pady=(20,0))

        # Only buttons (no frames) so state option is valid
        self.play_buttons = [
            self.play_pause_btn,
            self.speed_down_btn,
            self.speed_up_btn,
            self.step_btn,
        ]

    # ---------------- BUTTON CALLBACKS ----------------
    def load_maze_file(self):
        filename = filedialog.askopenfilename(initialdir=MAZE_DIR,
                                              filetypes=[("JSON files","*.json")])
        if filename:
            self.stop_astar()
            self.current_file = filename
            self.grid = load_maze(self.current_file)
            self.start_pos = self.find_cell(2)
            self.end_pos = self.find_cell(3)
            self.unsaved_changes = False

    def reset_maze(self):
        self.stop_astar()
        self.grid = create_grid(ROWS, COLS)
        self.start_pos = None
        self.end_pos = None
        self.unsaved_changes = True

    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire maze?"):
            self.reset_maze()

    def save(self):
        save_maze(self.grid, self.current_file)
        self.unsaved_changes = False
        messagebox.showinfo("Saved", f"Maze saved to {self.current_file}")

    def save_as(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json",
                                                initialdir=MAZE_DIR,
                                                filetypes=[("JSON files","*.json")])
        if filename:
            self.current_file = filename
            self.save()

    def options_menu(self):
        top = tk.Toplevel(self.root)
        top.title("Options")
        tk.Label(top, text="Keyboard Layout:").pack(anchor="w", padx=10, pady=(10,0))
        ttk.Radiobutton(top, text="AZERTY", variable=self.keyboard_layout, value="AZERTY").pack(anchor="w", padx=10)
        ttk.Radiobutton(top, text="QWERTY", variable=self.keyboard_layout, value="QWERTY").pack(anchor="w", padx=10)
        tk.Label(top, text="Made by Aziz Hizem", fg="lightgray").pack(side="bottom", pady=10)

    def show_info(self):
        info = tk.Toplevel(self.root)
        info.title("About A* Pathfinding")
        text = (
            "This project visualizes the A* pathfinding algorithm on a grid.\n\n"
            "Colors: \n"
            "- Green: start square\n"
            "- Red: goal square\n"
            "- Black: walls (blocked cells)\n"
            "- Blue: OPEN set (frontier nodes to explore)\n"
            "- Orange: CLOSED set (already explored nodes)\n"
            "- Yellow: final shortest path once found\n"
            "- Cyan: current node being expanded in this step\n\n"
            "Use 'Run A*' to watch the algorithm animate, or\n"
            "'Run A* Step-by-step' and the Step button to\n"
            "advance the search one expansion at a time."
        )
        tk.Label(info, text=text, justify="left", padx=10, pady=10).pack()

    # ---------------- MAIN LOOP ----------------
    def on_closing(self):
        if self.unsaved_changes:
            answer = messagebox.askyesnocancel("Unsaved Changes", "Save changes to the maze before closing?")
            if answer is None:
                return
            if answer:
                save_maze(self.grid, self.current_file)
        self.running = False
        pygame.quit()
        self.root.destroy()

    def loop(self):
        while self.running:
            try:
                self.handle_events()
                if not self.running:
                    break
                self.draw_grid()
                pygame.display.update()
                self.clock.tick(FPS)
                self.root.update()
            except tk.TclError:
                break

    # ---------------- EVENT HANDLING ----------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.on_closing()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and self.mode.get() == "edit":
                self.handle_click(pygame.mouse.get_pos())

    def handle_click(self, pos):
        x, y = pos
        row, col = y // CELL_SIZE, x // CELL_SIZE
        if row >= ROWS or col >= COLS:
            return
        # Editing the maze invalidates any search result shown on screen
        self.stop_astar()
        tool = self.tool.get()
        if tool == "wall":
            self.grid[row][col] = 1
        elif tool == "erase":
            if self.grid[row][col] == 2:
                self.start_pos = None
            elif self.grid[row][col] == 3:
                self.end_pos = None
            self.grid[row][col] = 0
        elif tool == "start":
            if self.start_pos:
                old_r, old_c = self.start_pos
                self.grid[old_r][old_c] = 0
            self.grid[row][col] = 2
            self.start_pos = (row, col)
        elif tool == "end":
            if self.end_pos:
                old_r, old_c = self.end_pos
                self.grid[old_r][old_c] = 0
            self.grid[row][col] = 3
            self.end_pos = (row, col)
        self.unsaved_changes = True

    def handle_key_press(self, event):
        layout = self.keyboard_layout.get()
        if layout == "AZERTY":
            mapping = {'&': "wall",'é': "start",'"': "end","'": "erase"}
        else:
            mapping = {'1': "wall",'2': "start",'3': "end",'4': "erase"}
        if event.char in mapping:
            self.tool.set(mapping[event.char])

    # ---------------- A* CONTROLS ----------------
    def _init_astar(self):
        if not self.start_pos or not self.end_pos:
            messagebox.showwarning("Missing Points", "Place start and end points first")
            return False
        walls = set()
        for r,row in enumerate(self.grid):
            for c,val in enumerate(row):
                if val==1:
                    walls.add((r,c))
        self.astar = AStarVisualizer(ROWS, COLS, walls, self.start_pos, self.end_pos)
        self.astar_paused = False
        self.last_step_time = 0
        # Enable playback controls
        for widget in self.play_buttons:
            widget.config(state="normal")
        return True

    def start_astar(self):
        if not self._init_astar():
            return
        self.astar_running = True
        self.step_mode = False
        self.play_pause_btn.config(text="Pause")

    def start_astar_stepwise(self):
        if not self._init_astar():
            return
        self.astar_running = True
        self.step_mode = True
        self.astar_paused = True  # no automatic stepping until Play is pressed
        self.play_pause_btn.config(text="Play")

    def toggle_pause(self):
        self.astar_paused = not self.astar_paused
        self.play_pause_btn.config(text="Play" if self.astar_paused else "Pause")

    def step_astar(self):
        if self.astar and self.astar_running:
            if self.astar.step():
                self.finish_astar()

    def finish_astar(self):
        """Stop stepping but keep the final state on screen."""
        self.astar_running = False
        for widget in self.play_buttons:
            widget.config(state="disabled")
        if not self.astar.found:
            messagebox.showinfo("No Path", "There is no path from start to goal.")

    def stop_astar(self):
        """Discard the current search and its drawing."""
        self.astar = None
        self.astar_running = False
        for widget in self.play_buttons:
            widget.config(state="disabled")

    def change_speed(self, delta_level):
        # Discrete speed levels x1..x10
        new_level = max(1, min(10, self.speed_level + delta_level))
        self.speed_level = new_level
        self.astar_speed = 1.0 / float(self.speed_level)
        self.speed_label.config(text=f"x{self.speed_level}")

    # ---------------- DRAW ----------------
    def draw_grid(self):
        # Base grid
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                pygame.draw.rect(self.win, get_color(val),
                                 (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.win, GRAY,
                                 (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

        if not self.astar:
            return

        # Step A* if running
        if self.astar_running:
            current_time = pygame.time.get_ticks()/1000  # seconds
            if not self.astar_paused and current_time - self.last_step_time > self.astar_speed:
                finished = self.astar.step()
                self.last_step_time = current_time
                if finished:
                    self.finish_astar()

        # Draw OPEN, CLOSED, PATH, CURRENT (kept on screen after the search ends)
        open_list, closed_set, path, current_pos = self.astar.get_state()
        for n in open_list:
            pygame.draw.rect(self.win, BLUE, (n.p[1]*CELL_SIZE, n.p[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        for p in closed_set:
            pygame.draw.rect(self.win, ORANGE, (p[1]*CELL_SIZE, p[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        for p in path:
            pygame.draw.rect(self.win, YELLOW, (p[1]*CELL_SIZE, p[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        if current_pos and not path:
            pygame.draw.rect(self.win, CYAN, (current_pos[1]*CELL_SIZE, current_pos[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE))

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MazeApp(root)
