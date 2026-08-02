#!/usr/bin/env python3
import subprocess, sys
import hasamiShogi
import pickle
import pygame
import time

CELL_SIZE = 60
MARGIN = 40
PANEL_WIDTH = 160
DELAY = 0.3     # seconds

def init_display(nameB, nameW):
    pygame.init()
    board_size = hasamiShogi.BOARD_SIZE * CELL_SIZE + 2 * MARGIN
    screen = pygame.display.set_mode((board_size + PANEL_WIDTH, board_size))
    pygame.display.set_caption(f"{nameB} (B) vs {nameW} (W)")
    return screen

def draw_captures(screen, captures):
    board_size = hasamiShogi.BOARD_SIZE * CELL_SIZE + 2 * MARGIN
    panel = pygame.Rect(board_size, 0, PANEL_WIDTH, board_size)
    pygame.draw.rect(screen, (200,200,200), panel)
    pygame.draw.line(screen, (0,0,0), (board_size, 0), (board_size, board_size), 1)

    title_font = pygame.font.Font(None, 28)
    count_font = pygame.font.Font(None, 40)
    cx = board_size + PANEL_WIDTH // 2

    title = title_font.render("Captured", True, (0,0,0))
    screen.blit(title, title.get_rect(center=(cx, 30)))

    # Black captures (pieces Black has captured, i.e. White pieces removed)
    pygame.draw.circle(screen, (0,0,0), (cx - 30, 80), 14)
    text = count_font.render(str(captures.get(hasamiShogi.BLACK, 0)), True, (0,0,0))
    screen.blit(text, text.get_rect(midleft=(cx, 68)))

    # White captures
    pygame.draw.circle(screen, (255,255,255), (cx - 30, 130), 14)
    pygame.draw.circle(screen, (0,0,0), (cx - 30, 130), 14, 2)
    text = count_font.render(str(captures.get(hasamiShogi.WHITE, 0)), True, (0,0,0))
    screen.blit(text, text.get_rect(midleft=(cx, 118)))

def draw_board(screen, board, captures=None):
    screen.fill((200,200,200))

    # Draw board cells
    for r in range(len(board)):
        for c in range(len(board)):
            x, y = MARGIN + c*CELL_SIZE, MARGIN + r*CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (255,255,255), rect)
            pygame.draw.rect(screen, (0,0,0), rect, 1)
            p = board[r][c]
            if p == hasamiShogi.BLACK:
                pygame.draw.circle(screen, (0,0,0), rect.center, CELL_SIZE//2-5)
            elif p == hasamiShogi.WHITE:
                pygame.draw.circle(screen, (255,255,255), rect.center, CELL_SIZE//2-5)
                pygame.draw.circle(screen, (0,0,0), rect.center, CELL_SIZE//2-5, 2)
    
    # Draw coordinate labels
    font = pygame.font.Font(None, 24)
    
    # Column labels (0-8)
    for c in range(len(board)):
        x = MARGIN + c*CELL_SIZE + CELL_SIZE//2
        # Top
        text = font.render(str(c), True, (0,0,0))
        text_rect = text.get_rect(center=(x, MARGIN//2))
        screen.blit(text, text_rect)
        # Bottom
        text = font.render(str(c), True, (0,0,0))
        text_rect = text.get_rect(center=(x, MARGIN + len(board)*CELL_SIZE + MARGIN//2))
        screen.blit(text, text_rect)
    
    # Row labels (0-8)
    for r in range(len(board)):
        y = MARGIN + r*CELL_SIZE + CELL_SIZE//2
        # Left
        text = font.render(str(r), True, (0,0,0))
        text_rect = text.get_rect(center=(MARGIN//2, y))
        screen.blit(text, text_rect)
        # Right
        text = font.render(str(r), True, (0,0,0))
        text_rect = text.get_rect(center=(MARGIN + len(board)*CELL_SIZE + MARGIN//2, y))
        screen.blit(text, text_rect)

    if captures is not None:
        draw_captures(screen, captures)

    pygame.display.flip()

class Engine:
    def send(self, line): pass
    def recv(self): return None
    def close(self): pass

class ProcessEngine(Engine):
    def __init__(self, cmd):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    def send(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()
    def recv(self):
        return self.p.stdout.readline().strip()
    def close(self):
        self.p.kill()

class ManualEngine(Engine):
    def __init__(self, color):
        self.color = color
    def send(self, line):
        if line == "OK?":
            name = input("Enter name: ").strip()
            self._last = name
        elif line == "BOARD":
            print("\n  " + " ".join(map(str, range(hasamiShogi.BOARD_SIZE))))
            for i,row in enumerate(arena.board):
                print(f"{i} " + " ".join(row))
        elif line == "Black":
            print("Black")
            while True:
                mv = input(f"[Manual {self.color}] enter move r1c1r2c2: ").strip()
                try:
                    parse_moves(mv)
                    self._last = mv
                    break
                except:
                    print("Failed")                
        elif line == "White":
            print("White")
        elif "GAME_OVER" in line:
            print(line)
        else:
            # prompt user for move
            mv = input(f"[Manual {self.color}] enter move r1c1r2c2: ").strip()
            try:
                parse_moves(mv)
            except:
                print("Failed")
            self._last = mv
                
        # ignore COLOR and GAME_OVER
    def recv(self):
        return getattr(self, "_last", "")
    def close(self):
        pass

def make_engine(arg, color):
    if arg.lower()=="manual":
        return ManualEngine(color)
    else:
        return ProcessEngine(arg.split())

def in_bounds(r1, c1, r2, c2):
    return all(0 <= v < hasamiShogi.BOARD_SIZE for v in (r1, c1, r2, c2))

def parse_moves(s):
    s = s.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError("Move must be 4 digits, e.g. '1234'")
    r1, c1, r2, c2 = map(int, s)
    if not in_bounds(r1, c1, r2, c2):
        raise ValueError("Move out of range")
    return r1, c1, r2, c2

def run_arena(black_arg, white_arg, max_moves=500, delay=DELAY):
    global arena
    arena = hasamiShogi.HasamiShogi()

    engines = {
        hasamiShogi.BLACK: make_engine(black_arg, hasamiShogi.BLACK),
        hasamiShogi.WHITE: make_engine(white_arg, hasamiShogi.WHITE)
    }
    
    # send COLOR to both
    for color, eng in engines.items():
        eng.send(f"OK?")
        line = eng.recv()
        eng.name = line
        if color == hasamiShogi.BLACK:
            while True:
                eng.send("Black")
                try:
                    firstMv = eng.recv()
                    nameB = eng.name
                    r1, c1, r2, c2 = parse_moves(firstMv)
                    arena.apply_move(r1,c1,r2,c2, hasamiShogi.BLACK)
                    break
                except:
                    print("Invalid move for Black")
            
        elif color == hasamiShogi.WHITE:
            eng.send("White")
            nameW = eng.name
    
    screen = init_display(nameB, nameW)

    for move_num in range(1, max_moves+1):
        print("")
        print("")
        print(arena.serialize())
        draw_board(screen, arena.board, arena.captures)

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                return

        eng = engines[arena.turn]
        eng.send(f"{arena.last_move[0]}{arena.last_move[1]}{arena.last_move[2]}{arena.last_move[3]}")
        # eng.send(arena.serialize())
        # eng.send("YOUR_MOVE")
        think_start = time.time()
        line = eng.recv()
        think_time = time.time() - think_start
        remaining = delay - think_time
        if remaining > 0:
            time.sleep(remaining)
        try:
            r1, c1, r2, c2 = parse_moves(line)
            # r1,c1,r2,c2 = map(int, line.split())
            arena.apply_move(r1,c1,r2,c2, arena.turn)

        # we should try the move and if it fails, go here
        except:
            print(f"{arena.turn} failed to move: '{line}'")
            winner = hasamiShogi.WHITE if arena.turn==hasamiShogi.BLACK else hasamiShogi.BLACK
            break

        over = arena.is_game_over()
        if over:
            winner = over
            break
    else:
        winner = None  # draw

    # notify GAME_OVER
    for color, eng in engines.items():
        if winner is None:
            result="DRAW"
        else:
            result="WIN" if color==winner else "LOSS"
        eng.send(f"GAME_OVER {result}")
        eng.close()

    print("Result:", winner or "DRAW")
    with open("history.pkl", "wb") as f:
        pickle.dump(arena.history, f)

    show_result(screen, winner)
    return winner

def show_result(screen, winner):
    draw_board(screen, arena.board, arena.captures)

    if winner is None:
        msg = "Draw!"
    else:
        msg = f"{'Black' if winner == hasamiShogi.BLACK else 'White'} wins!"
    msg += "  (close window to exit)"

    font = pygame.font.Font(None, 36)
    text = font.render(msg, True, (200, 0, 0))
    size = hasamiShogi.BOARD_SIZE * CELL_SIZE + 2 * MARGIN
    text_rect = text.get_rect(center=(size // 2, size // 2))
    pygame.draw.rect(screen, (255, 255, 0), text_rect.inflate(20, 20))
    screen.blit(text, text_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for evt in pygame.event.get():
            if evt.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
        time.sleep(0.05)
    pygame.quit()

if __name__=="__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: arena.py <black_cmd|manual> <white_cmd|manual> [delay_seconds]")
        sys.exit(1)
    delay = DELAY
    if len(sys.argv) == 4:
        try:
            delay = float(sys.argv[3])
        except ValueError:
            print("delay_seconds must be a number")
            sys.exit(1)
    run_arena(sys.argv[1], sys.argv[2], delay=delay)
