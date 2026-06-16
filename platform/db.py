import os
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "tournament.db")))

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    filename    TEXT    NOT NULL UNIQUE,
    uploaded_at TEXT    NOT NULL DEFAULT (datetime('now')),
    active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tournaments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT    NOT NULL CHECK(kind IN ('upload','scheduled','manual')),
    started_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    status      TEXT    NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS games (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    black_id      INTEGER NOT NULL REFERENCES players(id),
    white_id      INTEGER NOT NULL REFERENCES players(id),
    winner_id     INTEGER          REFERENCES players(id),
    move_count    INTEGER NOT NULL DEFAULT 0,
    result_type   TEXT    NOT NULL DEFAULT 'normal',
    error_msg     TEXT,
    move_history  TEXT,
    final_board   TEXT,
    played_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rankings (
    player_id  INTEGER PRIMARY KEY REFERENCES players(id),
    points     INTEGER NOT NULL DEFAULT 0,
    wins       INTEGER NOT NULL DEFAULT 0,
    draws      INTEGER NOT NULL DEFAULT 0,
    losses     INTEGER NOT NULL DEFAULT 0,
    games      INTEGER NOT NULL DEFAULT 0,
    win_pct    REAL    NOT NULL DEFAULT 0.0,
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def _connect():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _connect()
    conn.executescript(SCHEMA)
    conn.close()


# ── Players ───────────────────────────────────────────────────────────────────

def upsert_player(name, filename):
    """Insert or update a player by name. Returns (player_id, is_new)."""
    conn = _connect()
    row = conn.execute("SELECT id FROM players WHERE name=?", (name,)).fetchone()
    if row:
        conn.execute(
            "UPDATE players SET filename=?, uploaded_at=datetime('now') WHERE id=?",
            (filename, row["id"]),
        )
        conn.commit()
        conn.close()
        return row["id"], False
    cur = conn.execute("INSERT INTO players (name, filename) VALUES (?, ?)", (name, filename))
    player_id = cur.lastrowid
    conn.execute("INSERT OR IGNORE INTO rankings (player_id) VALUES (?)", (player_id,))
    conn.commit()
    conn.close()
    return player_id, True


def get_player(player_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
    conn.close()
    return row


def get_all_players():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM players WHERE active=1 ORDER BY uploaded_at"
    ).fetchall()
    conn.close()
    return rows


def get_top_n_players(n, exclude_id=None):
    conn = _connect()
    if exclude_id is not None:
        rows = conn.execute("""
            SELECT p.*, COALESCE(r.points, 0) AS points
            FROM players p
            LEFT JOIN rankings r ON r.player_id = p.id
            WHERE p.active=1 AND p.id != ?
            ORDER BY COALESCE(r.points, 0) DESC, p.uploaded_at ASC
            LIMIT ?
        """, (exclude_id, n)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.*, COALESCE(r.points, 0) AS points
            FROM players p
            LEFT JOIN rankings r ON r.player_id = p.id
            WHERE p.active=1
            ORDER BY COALESCE(r.points, 0) DESC, p.uploaded_at ASC
            LIMIT ?
        """, (n,)).fetchall()
    conn.close()
    return rows


# ── Tournaments ───────────────────────────────────────────────────────────────

def create_tournament(kind):
    conn = _connect()
    cur = conn.execute("INSERT INTO tournaments (kind) VALUES (?)", (kind,))
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def finish_tournament(tournament_id, status="done"):
    conn = _connect()
    conn.execute(
        "UPDATE tournaments SET finished_at=datetime('now'), status=? WHERE id=?",
        (status, tournament_id),
    )
    conn.commit()
    conn.close()


def get_last_tournament_time():
    conn = _connect()
    row = conn.execute(
        "SELECT finished_at FROM tournaments WHERE status='done' ORDER BY finished_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["finished_at"] if row else None


# ── Games ─────────────────────────────────────────────────────────────────────

def insert_game(tournament_id, black_id, white_id, winner_id,
                move_count, result_type, error_msg, move_history, final_board):
    conn = _connect()
    conn.execute("""
        INSERT INTO games
            (tournament_id, black_id, white_id, winner_id, move_count, result_type,
             error_msg, move_history, final_board)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tournament_id, black_id, white_id, winner_id, move_count, result_type,
          error_msg, json.dumps(move_history), final_board))
    conn.commit()
    conn.close()


def get_recent_games(player_id, limit=20):
    conn = _connect()
    rows = conn.execute("""
        SELECT g.*,
               pb.name AS black_name,
               pw.name AS white_name
        FROM games g
        JOIN players pb ON pb.id = g.black_id
        JOIN players pw ON pw.id = g.white_id
        WHERE g.black_id=? OR g.white_id=?
        ORDER BY g.played_at DESC
        LIMIT ?
    """, (player_id, player_id, limit)).fetchall()
    conn.close()
    return rows


# ── Rankings ──────────────────────────────────────────────────────────────────

def recompute_rankings():
    conn = _connect()
    conn.execute("""
        INSERT OR REPLACE INTO rankings
            (player_id, wins, draws, losses, games, points, win_pct, updated_at)
        SELECT
            p.id,
            SUM(CASE WHEN g.winner_id = p.id THEN 1 ELSE 0 END),
            SUM(CASE WHEN g.winner_id IS NULL THEN 1 ELSE 0 END),
            SUM(CASE WHEN g.winner_id IS NOT NULL AND g.winner_id != p.id THEN 1 ELSE 0 END),
            COUNT(*),
            SUM(CASE WHEN g.winner_id = p.id THEN 2
                     WHEN g.winner_id IS NULL THEN 1
                     ELSE 0 END),
            ROUND(100.0 * SUM(CASE WHEN g.winner_id = p.id THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0), 1),
            datetime('now')
        FROM players p
        JOIN games g ON g.black_id = p.id OR g.white_id = p.id
        WHERE p.active = 1
        GROUP BY p.id
    """)
    conn.commit()
    conn.close()


def get_ranking_rows():
    conn = _connect()
    rows = conn.execute("""
        SELECT p.id, p.name, p.uploaded_at,
               COALESCE(r.points,  0)   AS points,
               COALESCE(r.wins,    0)   AS wins,
               COALESCE(r.draws,   0)   AS draws,
               COALESCE(r.losses,  0)   AS losses,
               COALESCE(r.games,   0)   AS games,
               COALESCE(r.win_pct, 0.0) AS win_pct
        FROM players p
        LEFT JOIN rankings r ON r.player_id = p.id
        WHERE p.active = 1
        ORDER BY COALESCE(r.points, 0) DESC,
                 COALESCE(r.wins, 0) DESC,
                 p.uploaded_at ASC
    """).fetchall()
    conn.close()
    return rows


def get_player_stats(player_id):
    conn = _connect()
    row = conn.execute("""
        SELECT p.id, p.name, p.uploaded_at,
               COALESCE(r.points,  0)   AS points,
               COALESCE(r.wins,    0)   AS wins,
               COALESCE(r.draws,   0)   AS draws,
               COALESCE(r.losses,  0)   AS losses,
               COALESCE(r.games,   0)   AS games,
               COALESCE(r.win_pct, 0.0) AS win_pct
        FROM players p
        LEFT JOIN rankings r ON r.player_id = p.id
        WHERE p.id = ?
    """, (player_id,)).fetchone()
    conn.close()
    return row
