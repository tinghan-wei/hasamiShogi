#!/usr/bin/env python3
"""
tournament.py — round-robin Hasami Shogi tournament

Each pair of players plays TWO games: once with A as Black and once with A as White.
Scoring: Win = 2 pts, Draw = 1 pt, Loss = 0 pts.

Usage:
    python tournament.py <players_dir> [options]

Examples:
    python tournament.py players/2026/
    python tournament.py players/2026/ --recursive
    python tournament.py players/2026/ --include randomPlayer.py --move-timeout 5
"""

import argparse
import datetime
import itertools
import os
import select
import subprocess
import sys
from pathlib import Path

# Root directory (where hasamiShogi.py lives)
ROOT = Path(__file__).parent.resolve()

# Make hasamiShogi importable in child processes (both via '' in sys.path and PYTHONPATH)
CHILD_ENV = os.environ.copy()
CHILD_ENV["PYTHONPATH"] = str(ROOT) + os.pathsep + CHILD_ENV.get("PYTHONPATH", "")

import hasamiShogi  # noqa: E402  (import after ROOT is defined)

BLACK = hasamiShogi.BLACK
WHITE = hasamiShogi.WHITE


# ── Protocol helpers ──────────────────────────────────────────────────────────

def parse_move(s: str):
    s = s.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError(f"Bad move format: {s!r} (expected 4 digits like '1234')")
    r1, c1, r2, c2 = map(int, s)
    if not all(0 <= v < hasamiShogi.BOARD_SIZE for v in (r1, c1, r2, c2)):
        raise ValueError(f"Move out of bounds: {s!r}")
    return r1, c1, r2, c2


class PlayerProcess:
    """Wraps a player subprocess with send/recv helpers."""

    def __init__(self, script_path: str, move_timeout: float):
        self.path = script_path
        self.timeout = move_timeout
        self.name = Path(script_path).stem  # fallback display name

        self.proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=CHILD_ENV,
            cwd=str(ROOT),
        )

    def send(self, msg: str):
        self.proc.stdin.write(msg + "\n")
        self.proc.stdin.flush()

    def recv(self) -> str:
        ready = select.select([self.proc.stdout], [], [], self.timeout)[0]
        if not ready:
            raise TimeoutError(f"'{self.name}' timed out after {self.timeout}s")
        line = self.proc.stdout.readline()
        if not line:
            raise EOFError(f"'{self.name}' closed stdout unexpectedly (crashed?)")
        return line.strip()

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=2)
        except Exception:
            pass


# ── Single game ───────────────────────────────────────────────────────────────

def run_game(black_path: str, white_path: str, max_moves: int, move_timeout: float):
    """
    Run one game between two player scripts.

    Returns:
        winner     – BLACK, WHITE, or None (draw / move-limit)
        black_name – name the black player reported
        white_name – name the white player reported
        move_count – total half-moves played
        error_msg  – non-None string if the game ended by forfeit/crash
        history    – list of (r1,c1,r2,c2) tuples, one per half-move
        final_board – serialised board string at game end
    """
    black = PlayerProcess(black_path, move_timeout)
    white = PlayerProcess(white_path, move_timeout)
    game  = hasamiShogi.HasamiShogi()

    winner     = None
    error_msg  = None
    move_count = 0
    offender   = None   # 'black' | 'white' – who is responsible if an exception fires

    try:
        # ── Handshake ────────────────────────────────────────────────────────
        offender = "black"
        black.send("OK?")
        black.name = black.recv()

        offender = "white"
        white.send("OK?")
        white.name = white.recv()

        # ── Color assignment + Black's first move ────────────────────────────
        offender = "black"
        black.send("Black")
        first_move_str = black.recv()
        r1, c1, r2, c2 = parse_move(first_move_str)
        game.apply_move(r1, c1, r2, c2, BLACK)
        move_count = 1

        white.send("White")
        # White does NOT respond here; it waits for the first move in the loop.

        over = game.is_game_over()
        if over:
            winner = over
        else:
            last_move_str = first_move_str

            # ── Main game loop ────────────────────────────────────────────────
            for _ in range(max_moves - 1):   # -1 because Black already moved once
                current = game.turn
                if current == WHITE:
                    offender = "white"
                    eng = white
                else:
                    offender = "black"
                    eng = black

                eng.send(last_move_str)
                response = eng.recv()
                r1, c1, r2, c2 = parse_move(response)
                game.apply_move(r1, c1, r2, c2, current)
                move_count += 1
                last_move_str = response

                over = game.is_game_over()
                if over:
                    winner = over
                    break
            # Loop exhausted → draw (winner stays None)

    except (TimeoutError, EOFError, ValueError, Exception) as exc:
        error_msg = str(exc)
        winner = WHITE if offender == "black" else BLACK

    finally:
        # Notify both players of the outcome
        for color, eng in [(BLACK, black), (WHITE, white)]:
            try:
                if winner is None:
                    result = "DRAW"
                else:
                    result = "WIN" if color == winner else "LOSS"
                eng.send(f"GAME_OVER {result}")
            except Exception:
                pass
            eng.close()

    return winner, black.name, white.name, move_count, error_msg, game.history, game.serialize()


# ── Player discovery ──────────────────────────────────────────────────────────

def collect_players(directory: str, recursive: bool, extras: list) -> list:
    d = Path(directory).resolve()
    if not d.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    pattern = "**/*.py" if recursive else "*.py"
    paths = sorted(str(p) for p in d.glob(pattern))

    # Add extras (deduplicated)
    seen = set(paths)
    for extra in extras:
        p = str(Path(extra).resolve())
        if p not in seen:
            paths.append(p)
            seen.add(p)

    return paths


# ── Results table ─────────────────────────────────────────────────────────────

def print_standings(stats: dict, display_name: dict):
    """Print a sorted standings table."""
    rows = sorted(stats.items(), key=lambda x: (-x[1]["points"], -x[1]["wins"]))
    name_w = max((len(display_name.get(p, p)) for p in stats), default=6)
    name_w = max(name_w, 6)

    sep = "─" * (name_w + 36)
    fmt = f"{{:<{name_w}}}  {{:>4}}  {{:>4}}  {{:>4}}  {{:>5}}  {{:>5}}"

    print(sep)
    print(fmt.format("Player", "W", "D", "L", "Pts", "Games"))
    print(sep)
    for path, r in rows:
        name = display_name.get(path, path)
        print(fmt.format(name, r["wins"], r["draws"], r["losses"], r["points"], r["games"]))
    print(sep)


# ── Head-to-head mini-table ───────────────────────────────────────────────────

def print_h2h(h2h: dict, players: list, display_name: dict):
    """Print a head-to-head matrix (W/D/L from the row player's perspective)."""
    names = [display_name.get(p, Path(p).stem) for p in players]
    col_w = max(len(n) for n in names)
    col_w = max(col_w, 5)
    row_label_w = col_w

    # Header
    header = f"{'':>{row_label_w}}"
    for n in names:
        header += f"  {n:^{col_w}}"
    print(header)
    sep = "─" * len(header)
    print(sep)

    for i, p_row in enumerate(players):
        line = f"{names[i]:>{row_label_w}}"
        for j, p_col in enumerate(players):
            if i == j:
                line += f"  {'—':^{col_w}}"
            else:
                w, d, l = h2h.get((p_row, p_col), (0, 0, 0))
                cell = f"{w}W/{d}D/{l}L"
                line += f"  {cell:^{col_w}}"
        print(line)
    print()


# ── File report ──────────────────────────────────────────────────────────────

def _fmt_standings(stats: dict, display_name: dict) -> str:
    """Return the standings table as a plain string."""
    rows = sorted(stats.items(), key=lambda x: (-x[1]["points"], -x[1]["wins"]))
    name_w = max((len(display_name.get(p, p)) for p in stats), default=6)
    name_w = max(name_w, 6)
    sep = "-" * (name_w + 36)
    fmt = f"{{:<{name_w}}}  {{:>4}}  {{:>4}}  {{:>4}}  {{:>5}}  {{:>5}}"
    lines = [sep, fmt.format("Player", "W", "D", "L", "Pts", "Games"), sep]
    for path, r in rows:
        name = display_name.get(path, path)
        lines.append(fmt.format(name, r["wins"], r["draws"], r["losses"], r["points"], r["games"]))
    lines.append(sep)
    return "\n".join(lines)


def _fmt_h2h(h2h: dict, players: list, display_name: dict) -> str:
    """Return the head-to-head matrix as a plain string."""
    names = [display_name.get(p, Path(p).stem) for p in players]
    col_w = max(len(n) for n in names)
    col_w = max(col_w, 5)
    row_label_w = col_w
    header = f"{'':>{row_label_w}}" + "".join(f"  {n:^{col_w}}" for n in names)
    sep    = "-" * len(header)
    lines  = [header, sep]
    for i, p_row in enumerate(players):
        line = f"{names[i]:>{row_label_w}}"
        for j, p_col in enumerate(players):
            if i == j:
                line += f"  {'--':^{col_w}}"
            else:
                w, d, l = h2h.get((p_row, p_col), (0, 0, 0))
                line += f"  {f'{w}W/{d}D/{l}L':^{col_w}}"
        lines.append(line)
    return "\n".join(lines)


def _fmt_moves(history: list) -> str:
    """Format a move history as numbered half-moves, 4 per line."""
    if not history:
        return "  (no moves recorded)"
    parts = []
    for i, (r1, c1, r2, c2) in enumerate(history, 1):
        color = "B" if i % 2 == 1 else "W"
        parts.append(f"{i:>3}. {color}:{r1}{c1}{r2}{c2}")
    # 4 moves per line
    lines = []
    for i in range(0, len(parts), 4):
        lines.append("  " + "   ".join(parts[i:i+4]))
    return "\n".join(lines)


def write_report(
    out_path: str,
    args,
    players: list,
    game_records: list,
    stats: dict,
    display_name: dict,
    h2h: dict,
    started_at: datetime.datetime,
):
    """Write a full tournament report (standings + every game record) to *out_path*."""
    finished_at = datetime.datetime.now()
    duration    = finished_at - started_at

    with open(out_path, "w", encoding="utf-8") as f:
        def w(line=""):
            f.write(line + "\n")

        # ── Header ────────────────────────────────────────────────────────────
        w("Hasami Shogi Tournament Report")
        w("=" * 50)
        w(f"Started  : {started_at:%Y-%m-%d %H:%M:%S}")
        w(f"Finished : {finished_at:%Y-%m-%d %H:%M:%S}  (duration {duration})")
        w(f"Directory: {args.directory}")
        w(f"Players  : {len(players)}")
        w(f"Games    : {len(game_records)}")
        w(f"Max moves: {args.max_moves}  |  Move timeout: {args.move_timeout}s")
        w(f"Scoring  : Win=2, Draw=1, Loss=0")
        w()
        for p in players:
            w(f"  {display_name.get(p, Path(p).stem)}  <{p}>")
        w()

        # ── Standings ─────────────────────────────────────────────────────────
        w("=" * 50)
        w("  FINAL STANDINGS")
        w("=" * 50)
        w(_fmt_standings(stats, display_name))
        w()

        # ── Head-to-head ──────────────────────────────────────────────────────
        if len(players) <= 12:
            w("=" * 50)
            w("  HEAD-TO-HEAD  (row=Black, col=White; W/D/L for the row player)")
            w("=" * 50)
            w(_fmt_h2h(h2h, players, display_name))
            w()

        # ── Game records ──────────────────────────────────────────────────────
        w("=" * 50)
        w("  GAME RECORDS")
        w("=" * 50)
        for rec in game_records:
            w()
            w(f"[Game {rec['num']}]  {rec['black_name']} (B)  vs  {rec['white_name']} (W)")
            w(f"  Files  : {Path(rec['black_path']).name}  vs  {Path(rec['white_path']).name}")
            w(f"  Result : {rec['result_str']}")
            if rec["error"]:
                w(f"  Warning: {rec['error']}")
            w(f"  Moves ({rec['move_count']}):")
            w(_fmt_moves(rec["history"]))
            w(f"  Final board:")
            for board_line in rec["final_board"].splitlines():
                w(f"    {board_line}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hasami Shogi round-robin tournament",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("directory",
                        help="Directory containing player .py scripts")
    parser.add_argument("--max-moves", type=int, default=500, metavar="N",
                        help="Max half-moves per game (default: 500)")
    parser.add_argument("--move-timeout", type=float, default=10.0, metavar="T",
                        help="Seconds allowed per move (default: 10.0)")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Search subdirectories for player scripts")
    parser.add_argument("--include", metavar="FILE", action="append", default=[],
                        help="Include an extra player script (repeatable)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress per-game output; only print final standings")
    parser.add_argument("--no-h2h", action="store_true",
                        help="Skip the head-to-head matrix")
    parser.add_argument("--output", "-o", metavar="FILE", default=None,
                        help="Write full report to FILE (default: tournament_YYYYMMDD_HHMMSS.txt)")
    parser.add_argument("--no-output", action="store_true",
                        help="Do not write any report file")
    args = parser.parse_args()

    players = collect_players(args.directory, args.recursive, args.include)
    if len(players) < 2:
        print(f"Need at least 2 players, found {len(players)}.", file=sys.stderr)
        sys.exit(1)

    n_games    = len(players) * (len(players) - 1)  # each ordered pair plays once
    started_at = datetime.datetime.now()

    print(f"Hasami Shogi Tournament")
    print(f"  Players  : {len(players)}")
    print(f"  Games    : {n_games}  (each pair plays twice, swapping colours)")
    print(f"  Max moves: {args.max_moves}  |  Move timeout: {args.move_timeout}s")
    print(f"  Scoring  : Win=2, Draw=1, Loss=0")
    print()
    for p in players:
        print(f"    • {Path(p).stem}  ({p})")
    print()

    # Stats per player path
    stats = {p: {"wins": 0, "draws": 0, "losses": 0, "points": 0, "games": 0}
             for p in players}
    display_name = {p: Path(p).stem for p in players}

    # Head-to-head: (black_path, white_path) → (w, d, l) from black's perspective
    h2h: dict = {}

    game_records = []   # list of dicts, one per game, used for the file report
    game_num = 0
    for black_path, white_path in itertools.permutations(players, 2):
        game_num += 1
        b_stem = Path(black_path).stem
        w_stem = Path(white_path).stem

        if not args.quiet:
            print(f"  [{game_num:>{len(str(n_games))}}/{n_games}] "
                  f"{b_stem} (B) vs {w_stem} (W) … ", end="", flush=True)

        winner, black_name, white_name, moves, error, history, final_board = run_game(
            black_path, white_path, args.max_moves, args.move_timeout
        )

        # Update display names to what the player actually reported
        display_name[black_path] = black_name
        display_name[white_path] = white_name

        # Tally stats
        stats[black_path]["games"] += 1
        stats[white_path]["games"] += 1

        if winner == BLACK:
            stats[black_path]["wins"]   += 1
            stats[black_path]["points"] += 2
            stats[white_path]["losses"] += 1
            result_str = f"{black_name} (B) wins  [{moves} moves]"
            h2h[(black_path, white_path)] = tuple(x + d for x, d in zip(
                h2h.get((black_path, white_path), (0, 0, 0)), (1, 0, 0)))
        elif winner == WHITE:
            stats[white_path]["wins"]   += 1
            stats[white_path]["points"] += 2
            stats[black_path]["losses"] += 1
            result_str = f"{white_name} (W) wins  [{moves} moves]"
            h2h[(black_path, white_path)] = tuple(x + d for x, d in zip(
                h2h.get((black_path, white_path), (0, 0, 0)), (0, 0, 1)))
        else:
            stats[black_path]["draws"]  += 1
            stats[white_path]["draws"]  += 1
            stats[black_path]["points"] += 1
            stats[white_path]["points"] += 1
            result_str = f"Draw  [{moves} moves]"
            h2h[(black_path, white_path)] = tuple(x + d for x, d in zip(
                h2h.get((black_path, white_path), (0, 0, 0)), (0, 1, 0)))

        if not args.quiet:
            suffix = f"  ⚠ {error}" if error else ""
            print(result_str + suffix)

        game_records.append({
            "num":        game_num,
            "black_path": black_path,
            "white_path": white_path,
            "black_name": black_name,
            "white_name": white_name,
            "winner":     winner,
            "result_str": result_str,
            "move_count": moves,
            "error":      error,
            "history":    history,
            "final_board": final_board,
        })

    # ── Final output ──────────────────────────────────────────────────────────
    print()
    print("═" * 50)
    print("  FINAL STANDINGS")
    print("═" * 50)
    print_standings(stats, display_name)

    if not args.no_h2h and len(players) <= 12:   # matrix gets unwieldy for many players
        print()
        print("  HEAD-TO-HEAD  (row = Black, col = White; shown as W/D/L for the row player)")
        print()
        print_h2h(h2h, players, display_name)

    # ── Write report file ─────────────────────────────────────────────────────
    if not args.no_output:
        out_path = args.output or f"tournament_{started_at:%Y%m%d_%H%M%S}.txt"
        write_report(out_path, args, players, game_records, stats, display_name, h2h, started_at)
        print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    main()
