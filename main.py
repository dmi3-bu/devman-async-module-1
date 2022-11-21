import time
import curses
import asyncio
import random
from itertools import cycle

TIC_TIMEOUT = 0.1
STARS_COUNT = 100
PADDING = 1
SYMBOLS = ['+', '*', '.', ':']
STAR_SIZE = 1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258
ROCKET_FRAME_1 = open('frames/rocket_frame_1.txt').read()
ROCKET_FRAME_2 = open('frames/rocket_frame_2.txt').read()
ROCKET_FRAMES = [
    ROCKET_FRAME_1, ROCKET_FRAME_1, ROCKET_FRAME_2, ROCKET_FRAME_2
]
INIT_ROCKET_ROW = 4
INIT_ROCKET_COLUMN = 20


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


ROCKET_ROWS, ROCKET_COLS = get_frame_size(ROCKET_FRAMES[0])


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    global MAX_ROW, MAX_COLUMN
    MAX_ROW, MAX_COLUMN = canvas.getmaxyx()

    objects = []
    for _ in range(STARS_COUNT):
        row = random.randint(0 + PADDING, MAX_ROW - PADDING - STAR_SIZE)
        column = random.randint(0 + PADDING, MAX_COLUMN - PADDING - STAR_SIZE)
        sign = random.choice(SYMBOLS)
        star = blink(canvas, row, column, sign)
        objects.append(star)

    shot = fire(canvas, INIT_ROCKET_ROW - 2, INIT_ROCKET_COLUMN + 2)
    spaceship = animate_spaceship(canvas, ROCKET_FRAMES)
    objects.extend([shot, spaceship])

    while True:
        for object in objects.copy():
            try:
                object.send(None)
            except StopIteration:
                objects.remove(object)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, symbol='*'):
    while True:
        for _ in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        while True:
            canvas.addstr(row, column, symbol, curses.A_DIM)
            if random.randint(0, 5) == 0:
                break
            await asyncio.sleep(0)

        for _ in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for _ in range(5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for _ in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, frames):
    row = INIT_ROCKET_ROW
    column = INIT_ROCKET_COLUMN
    for frame in cycle(frames):
        row_dir, column_dir, space_pr = read_controls(canvas)
        row = limit_boundary(row + row_dir, 0 + PADDING,
                             MAX_ROW - ROCKET_ROWS - PADDING)
        column = limit_boundary(column + column_dir, 0 + PADDING,
                                MAX_COLUMN - ROCKET_COLS - PADDING)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, True)


def limit_boundary(dimension, min_dim, max_dim):
    dimension = max(dimension, min_dim)
    dimension = min(dimension, max_dim)
    return dimension


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 2

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -2

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
