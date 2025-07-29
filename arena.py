#!/usr/bin/env python3
import subprocess, sys
import hasamiShogi

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

def run_arena(black_arg, white_arg, max_moves=500):
    global arena
    arena = hasamiShogi()
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
                    r1, c1, r2, c2 = parse_moves(firstMv)
                    arena.apply_move(r1,c1,r2,c2, hasamiShogi.BLACK)
                    break
                except:
                    print("Invalid move for Black")
            
        elif color == hasamiShogi.WHITE:
            eng.send("White")

    for move_num in range(1, max_moves+1):
        print("")
        print("")
        print(arena.serialize())

        eng = engines[arena.turn]
        eng.send(f"{arena.last_move[0]}{arena.last_move[1]}{arena.last_move[2]}{arena.last_move[3]}")
        # eng.send(arena.serialize())
        # eng.send("YOUR_MOVE")
        line = eng.recv()
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
    return winner

if __name__=="__main__":
    if len(sys.argv)!=3:
        print("Usage: arena.py <black_cmd|manual> <white_cmd|manual>")
        sys.exit(1)
    run_arena(sys.argv[1], sys.argv[2])
