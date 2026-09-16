class Node:
    def __init__(self, position, g_score, h_score, parent):
        self.p = position       # (row, col)
        self.g = g_score        # cost from start to this node
        self.h = h_score        # heuristic (Manhattan distance to end)
        self.f = g_score + h_score  # total estimated cost
        self.pa = parent        # parent node (for reconstructing path)


def get_best_node(open_list):
    best_f = open_list[0].f
    best_node = open_list[0]
    best_index = 0
    for i in range(len(open_list)):
        if open_list[i].f < best_f:
            best_f = open_list[i].f
            best_node = open_list[i]
            best_index = i

    return (best_node, best_index)


def get_manhattan(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_valid_neighbors(position, ROWS, COLS, walls, closed_set):
    row, col = position
    neighbors = [(row-1, col), (row+1, col), (row, col+1), (row, col-1)]
    filtered = []

    for n in neighbors:
        r,c = n
        if 0<=r<ROWS and 0<=c<COLS and n not in walls and n not in closed_set:
            filtered.append(n)
    return filtered


class AStarVisualizer:
    """Stepwise A* for visualization"""
    def __init__(self, ROWS, COLS, walls, start, end):
        self.ROWS = ROWS
        self.COLS = COLS
        self.walls = walls
        self.start = start
        self.end = end

        self.open_list = [Node(start, 0, get_manhattan(start, end), None)]
        self.closed_set = set()
        self.current = None
        self.found = False
        self.path = []

    def step(self):
        """Perform one step of A* algorithm"""
        if not self.open_list or self.found:
            return True  # Finished

        self.current, idx = get_best_node(self.open_list)
        self.open_list.pop(idx)
        self.closed_set.add(self.current.p)

        if self.current.p == self.end:
            self.found = True
            # reconstruct path
            node = self.current
            self.path = [node.p]
            while node.pa is not None:
                node = node.pa
                self.path.append(node.p)
            self.path.reverse()
            return True  # Finished

        # Expand neighbors
        neighbors = get_valid_neighbors(self.current.p, self.ROWS, self.COLS, self.walls, self.closed_set)
        for n in neighbors:
            tentative_g = self.current.g + 1
            # check if neighbor in open
            for node in self.open_list:
                if node.p == n:
                    if tentative_g < node.g:
                        node.g = tentative_g
                        node.f = node.g + node.h
                        node.pa = self.current
                    break
            else:
                new_node = Node(n, tentative_g, get_manhattan(n, self.end), self.current)
                self.open_list.append(new_node)
        return False  # Not finished yet

    def get_state(self):
        """Return current state for drawing"""
        return self.open_list, self.closed_set, self.path, self.current.p if self.current else None