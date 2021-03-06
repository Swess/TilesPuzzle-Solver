import copy
from typing import List, Tuple
from solvers import ISolvable
import numpy as np

PuzzleInternalState = np.ndarray
PuzzleTilePos = Tuple[int, int]
IntDirection2D = Tuple[int, int]
PuzzleMove = Tuple[int, PuzzleTilePos, IntDirection2D]  # Cost, TileToMove, Direction


# Main Puzzle objects
# Also represents a unique puzzle entire state
class Puzzle(ISolvable):
    """Puzzle grid with X & Y Axis representation with a coordinate system with the origin
    at the top left of the grid."""

    def __init__(self, grid: PuzzleInternalState, dimension: Tuple[int, int],
                 empty_tile_position: PuzzleTilePos) -> None:
        super().__init__()
        if len(dimension) < 2 or dimension[0] < 2 or dimension[1] < 2:
            raise ValueError("Invalid puzzle dimensions. Width & Height needs greater or equal than 2.")

        self.__dimensions = dimension
        self.__grid = grid
        self.__tile_pos = empty_tile_position

    @classmethod
    def from_state(cls, state: PuzzleInternalState, tile_pos: PuzzleTilePos = None) -> '__class__':
        if tile_pos is None:
            pos = Puzzle.locate_tile(state, 0)
        else:
            pos = tile_pos

        p = cls(state, (state.shape[1], state.shape[0]), pos)

        return p

    @classmethod
    def from_int_list(cls, int_list: List[int], dimension: Tuple[int, int]) -> '__class__':
        grid = np.reshape(int_list, (dimension[1], dimension[0]))
        return cls.from_state(grid)

    def get_internal_state(self):
        return self.__grid

    def get_dimensions(self):
        return self.__dimensions

    def get_current_pos(self):
        return self.__tile_pos

    # Puzzle have 2D coordinate system origin at top left of the image
    def __getitem__(self, pos: Tuple[int, int]) -> int:
        return self.__grid[pos[1], pos[0]]

    def __setitem__(self, key: Tuple[int, int], value) -> None:
        self.__grid[key[1], key[0]] = value

    @staticmethod
    def locate_tile(state: PuzzleInternalState, tile: int) -> Tuple[int, int]:
        x, y = 0, 0

        for row in state:
            for t in row:
                if t == tile:
                    return x, y
                x += 1

            y += 1
            x = 0

        raise Exception(f"No tile marked as '{tile}' found in the puzzle definition.")

    def get_moves(self) -> List[PuzzleMove]:
        moves: List[PuzzleMove] = []
        w, h = self.__dimensions
        x, y = self.__tile_pos

        def cost(tile: PuzzleTilePos) -> int:
            # Wrapped Horizontally
            if (w > 2) and ((tile[0] == 0 and x == w - 1) or (tile[0] == w - 1 and x == 0)):
                return 2

            # Wrapped Vertically
            if (h > 2) and ((tile[1] == 0 and y == h - 1) or (tile[1] == h - 1 and y == 0)):
                return 2

            # Default: Regular
            return 1

        # Adjacent tiles (Regular [Cost: 1] & Wrapping [Cost: 2])
        top = x, ((y - 1) % h)
        right = ((x + 1) % w), y
        bottom = x, ((y + 1) % h)
        left = ((x - 1) % w), y

        # No duplicate tiles if wrapped with Width or Height of 2
        laterals = []
        if top == bottom:
            laterals.append((top, (0, -1)))
        else:
            laterals.append((top, (0, -1)))
            laterals.append((bottom, (0, 1)))

        if right == left:
            laterals.append((right, (-1, 0)))
        else:
            laterals.append((right, (-1, 0)))
            laterals.append((left, (1, 0)))

        # Add with tile's cost
        for t in laterals:
            moves.append((cost(t[0]), t[0], t[1]))

        # Diagonals
        diagonals = []
        if (h, w) != (2, 2):  # Don't consider 2x2 puzzles
            d1, d2, dir1, dir2 = None, None, None, None
            # Top left || Bottom Right
            if (x, y) == (0, 0) or (x, y) == (w - 1, h - 1):
                d1, dir1 = (((x - 1) % w), ((y - 1) % h)), (1, 1)
                d2, dir2 = (((x + 1) % w), ((y + 1) % h)), (-1, -1)

            # Top right || Bottom Left
            if (x, y) == (w - 1, 0) or (x, y) == (0, h - 1):
                d1, dir1 = (((x - 1) % w), ((y + 1) % h)), (1, -1)
                d2, dir2 = (((x + 1) % w), ((y - 1) % h)), (-1, 1)

            if d1 and d2:
                diagonals.append((d1, dir1))
                diagonals.append((d2, dir2))

        # Add with tile's cost
        for t in diagonals:
            moves.append((3, t[0], t[1]))

        # [(cost, (tile.x, tile.y), 2D_Direction), ...]
        return moves

    def compute_move(self, from_state: '__class__', move_to_apply: PuzzleMove) -> '__class__':
        def swap(a, p1: PuzzleTilePos, p2: PuzzleTilePos):
            # Tuple unpacking swap is more efficient
            a[p1], a[p2] = a[p2], a[p1]

        w, h = self.__dimensions
        cost, tile_pos, direction = move_to_apply
        tile_x, tile_y = tile_pos
        new_empty_tile_pos = ((tile_x + direction[0]) % w), ((tile_y + direction[1]) % h)

        computed_state = copy.deepcopy(from_state)
        swap(computed_state, tile_pos, new_empty_tile_pos)

        return Puzzle.from_state(computed_state.__grid, tile_pos)

    def __eq__(self, o: object) -> bool:
        # Reference to same obj
        if self is o:
            return True

        if not isinstance(o, Puzzle):
            return False

        # Compare only internal state
        return np.array_equal(self.__grid, o.__grid)

    def __ne__(self, o: object) -> bool:
        return not __eq__(o)

    def to_single_line_str(self):
        str_l = []
        for r in self.__grid.tolist():
            for c in r:
                str_l.append(str(c))
        return " ".join(str_l)

    def __str__(self) -> str:
        return np.array_str(self.__grid)

    def __hash__(self):
        return hash(str(self.__grid))


# ======
def find_goals(puzzle: Puzzle) -> Tuple[Puzzle, Puzzle]:
    dim = puzzle.get_dimensions()
    count = dim[0] * dim[1]
    lin = np.arange(count)
    lin = np.append(lin[1:], lin[0])  # 0 tile is last

    goal1 = np.reshape(lin, (dim[1], dim[0]))

    goal2 = np.reshape(lin, (dim[0], dim[1])).T
    return Puzzle.from_state(goal1), Puzzle.from_state(goal2)


def parse_puzzle(p_list: list, dimension: Tuple[int, int]) -> Puzzle:
    int_arr = np.array(p_list, dtype=np.uint32)
    return Puzzle.from_int_list(list(int_arr), dimension)


def load_puzzles(puzzle_filename, dimension: Tuple[int, int]) -> List[Puzzle]:
    with open(puzzle_filename, "r") as file:
        p_lines = file.readlines()

    p_list = list(map(lambda l: l.split(), p_lines))
    return list(map(lambda l: parse_puzzle(l, dimension), p_list))
