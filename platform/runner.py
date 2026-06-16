import os
import select
import subprocess
import sys
from pathlib import Path

# Add repo root so hasamiShogi is importable here and passed to child processes
REPO_ROOT = str(Path(__file__).parent.parent.resolve())
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import hasamiShogi  # noqa: E402

BLACK = hasamiShogi.BLACK  # 'B'
WHITE = hasamiShogi.WHITE  # 'W'

USE_DOCKER   = os.environ.get("USE_DOCKER", "true").lower() not in ("false", "0", "no")
MOVE_TIMEOUT = float(os.environ.get("MOVE_TIMEOUT", "10"))
MAX_MOVES    = int(os.environ.get("MAX_MOVES", "500"))


def _parse_move(s):
    s = s.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError(f"Bad move: {s!r}")
    r1, c1, r2, c2 = map(int, s)
    if not all(0 <= v < hasamiShogi.BOARD_SIZE for v in (r1, c1, r2, c2)):
        raise ValueError(f"Out of range: {s!r}")
    return r1, c1, r2, c2


class _Player:
    def __init__(self, script_path, timeout):
        self.timeout = timeout
        self.name = Path(script_path).stem  # fallback name

        if USE_DOCKER:
            cmd = [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--read-only",
                "--memory", "128m",
                "--cpus", "0.5",
                "--pids-limit", "64",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
                "-v", f"{REPO_ROOT}:/repo:ro",
                "-v", f"{Path(script_path).resolve()}:/player.py:ro",
                "-e", "PYTHONPATH=/repo",
                "-e", "PYTHONUNBUFFERED=1",
                "-w", "/repo",
                "python:3.11-slim",
                "python", "/player.py",
            ]
            env = None
        else:
            cmd = [sys.executable, str(script_path)]
            env = os.environ.copy()
            env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **({"env": env} if env is not None else {}),
        )

    def send(self, msg):
        self.proc.stdin.write(msg + "\n")
        self.proc.stdin.flush()

    def recv(self):
        ready = select.select([self.proc.stdout], [], [], self.timeout)[0]
        if not ready:
            raise TimeoutError(f"'{self.name}' timed out after {self.timeout}s")
        line = self.proc.stdout.readline()
        if not line:
            raise EOFError(f"'{self.name}' closed stdout (crashed)")
        return line.strip()

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=3)
        except Exception:
            pass


def run_game(black_path, white_path, max_moves=None, move_timeout=None):
    """
    Run one game between two player scripts.

    Returns a dict:
        winner       – 'B', 'W', or None (draw/move-limit)
        black_name   – name the Black player reported
        white_name   – name the White player reported
        move_count   – half-moves played
        result_type  – 'normal' | 'forfeit' | 'draw'
        error_msg    – str or None
        history      – list of [r1,c1,r2,c2]
        final_board  – serialised board string
    """
    if max_moves is None:
        max_moves = MAX_MOVES
    if move_timeout is None:
        move_timeout = MOVE_TIMEOUT

    black = _Player(black_path, move_timeout)
    white = _Player(white_path, move_timeout)
    game  = hasamiShogi.HasamiShogi()

    winner      = None
    result_type = "draw"
    error_msg   = None
    offender    = None

    try:
        offender = "black"
        black.send("OK?")
        black.name = black.recv()

        offender = "white"
        white.send("OK?")
        white.name = white.recv()

        offender = "black"
        black.send("Black")
        first = black.recv()
        r1, c1, r2, c2 = _parse_move(first)
        game.apply_move(r1, c1, r2, c2, BLACK)

        white.send("White")

        over = game.is_game_over()
        if over:
            winner, result_type = over, "normal"
        else:
            last = first
            for _ in range(max_moves - 1):
                cur = game.turn
                if cur == WHITE:
                    offender, eng = "white", white
                else:
                    offender, eng = "black", black

                eng.send(last)
                resp = eng.recv()
                r1, c1, r2, c2 = _parse_move(resp)
                game.apply_move(r1, c1, r2, c2, cur)
                last = resp

                over = game.is_game_over()
                if over:
                    winner, result_type = over, "normal"
                    break
            # loop exhausted without winner → draw

    except Exception as exc:
        error_msg   = str(exc)
        winner      = WHITE if offender == "black" else BLACK
        result_type = "forfeit"

    finally:
        for color, eng in [(BLACK, black), (WHITE, white)]:
            try:
                s = "DRAW" if winner is None else ("WIN" if color == winner else "LOSS")
                eng.send(f"GAME_OVER {s}")
            except Exception:
                pass
            eng.close()

    return {
        "winner":      winner,
        "black_name":  black.name,
        "white_name":  white.name,
        "move_count":  len(game.history),
        "result_type": result_type,
        "error_msg":   error_msg,
        "history":     [list(m) for m in game.history],
        "final_board": game.serialize(),
    }
