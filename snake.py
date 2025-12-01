"""Terminal-based Snake game using curses (no external dependencies).

Scoring WINNING_SCORE foods reveals the CTF flag. The flag is read from:
 - ./flag.txt if present, else
 - environment variable CTF_FLAG if set, else
 - a placeholder message.

Controls: arrow keys or WASD, 'q' to quit.
"""

import curses
import time
import random
import os
import sys

WINNING_SCORE = 10
GRID_WIDTH = 30
GRID_HEIGHT = 20
TICK = 0.12  # seconds between moves


def load_flag():
    # Prefer local flag file (safe in CTFs). Fallback to env var if present.
    fn = os.path.join(os.path.dirname(__file__), "flag.txt")
    if os.path.exists(fn):
        try:
            with open(fn, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return "FLAG{could_not_read_flag_file}"
    env_flag = os.environ.get("CTF_FLAG")
    if env_flag:
        return env_flag
    return "Cyberfellas123"


class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        random.seed()
        self.reset()

    def reset(self):
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)  # right
        self._direction_history = []
        self.score = 0
        self.food = self._spawn_food()
        self.game_over = False
        self.victory = False

    def _spawn_food(self):
        while True:
            p = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if p not in self.snake:
                return p

    def step(self):
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        # collision with walls
        if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
            self.game_over = True
            return
        # collision with self
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)
        ate = False
        if new_head == self.food:
            ate = True
            self.score += 1
            if self.score >= WINNING_SCORE:
                self.victory = True
                return
            self.food = self._spawn_food()

        if not ate:
            self.snake.pop()

    def change_direction(self, new_dir):
        # prevent reversing
        if (new_dir[0] * -1, new_dir[1] * -1) == self.direction:
            return
        self.direction = new_dir

    def draw(self):
        self.stdscr.clear()
        # draw border
        for x in range(GRID_WIDTH + 2):
            self.stdscr.addch(0, x, "#")
            self.stdscr.addch(GRID_HEIGHT + 1, x, "#")
        for y in range(1, GRID_HEIGHT + 1):
            self.stdscr.addch(y, 0, "#")
            self.stdscr.addch(y, GRID_WIDTH + 1, "#")

        # draw food
        fx, fy = self.food
        self.stdscr.addch(fy + 1, fx + 1, "*")

        # draw snake
        for i, (x, y) in enumerate(self.snake):
            ch = "@" if i == 0 else "o"
            self.stdscr.addch(y + 1, x + 1, ch)

        # HUD
        self.stdscr.addstr(GRID_HEIGHT + 3, 0, f"Score: {self.score} / {WINNING_SCORE}    q: quit")
        self.stdscr.refresh()


def run(stdscr):
    # configure curses
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # check terminal size
    max_y, max_x = stdscr.getmaxyx()
    needed_x = GRID_WIDTH + 4
    needed_y = GRID_HEIGHT + 6
    if max_x < needed_x or max_y < needed_y:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Terminal too small. Need at least {needed_x}x{needed_y} (cols x rows).")
        stdscr.addstr(2, 0, "Resize the terminal and try again.")
        stdscr.refresh()
        stdscr.getch()
        return

    game = Game(stdscr)

    last_time = time.time()
    while True:
        # input
        c = stdscr.getch()
        if c != -1:
            if c in (ord('q'), ord('Q')):
                break
            elif c in (curses.KEY_UP, ord('w'), ord('W')):
                game.change_direction((0, -1))
            elif c in (curses.KEY_DOWN, ord('s'), ord('S')):
                game.change_direction((0, 1))
            elif c in (curses.KEY_LEFT, ord('a'), ord('A')):
                game.change_direction((-1, 0))
            elif c in (curses.KEY_RIGHT, ord('d'), ord('D')):
                game.change_direction((1, 0))
            elif c == ord('r') and (game.game_over or game.victory):
                game.reset()

        # tick
        now = time.time()
        if now - last_time >= TICK and not (game.game_over or game.victory):
            game.step()
            last_time = now

        # draw
        game.draw()

        if game.game_over:
            stdscr.addstr(GRID_HEIGHT + 5, 0, "GAME OVER! Press r to restart or q to quit.")
            stdscr.refresh()
            time.sleep(0.05)
            continue

        if game.victory:
            flag = load_flag()
            stdscr.clear()
            stdscr.addstr(0, 0, "CONGRATULATIONS! You reached the goal.")
            stdscr.addstr(2, 0, f"Flag: {flag}")
            stdscr.addstr(4, 0, "Press r to play again or q to quit.")
            stdscr.refresh()
            # wait for r or q
            while True:
                k = stdscr.getch()
                if k in (ord('q'), ord('Q')):
                    return
                if k in (ord('r'), ord('R')):
                    game.reset()
                    break
                time.sleep(0.05)


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
