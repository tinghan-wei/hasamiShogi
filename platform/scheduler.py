import itertools
import logging
import os
import threading
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

import db
import runner

log = logging.getLogger(__name__)

PLAYERS_DIR         = Path(__file__).parent / "players"
TOURNAMENT_INTERVAL = int(os.environ.get("TOURNAMENT_INTERVAL", "60"))  # minutes
TOP_N               = int(os.environ.get("TOP_N", "8"))

_lock      = threading.Lock()
_scheduler = None


def _color_to_id(winner_color, black_id, white_id):
    if winner_color == runner.BLACK:
        return black_id
    if winner_color == runner.WHITE:
        return white_id
    return None  # draw


def run_upload_matches(new_player_id, new_player_path):
    """Play a newly uploaded player against the current top-N. Runs in a thread."""
    opponents = db.get_top_n_players(TOP_N, exclude_id=new_player_id)
    if not opponents:
        log.info("No opponents available for upload match")
        return

    tid = db.create_tournament("upload")
    try:
        for opp in opponents:
            opp_path = str(PLAYERS_DIR / opp["filename"])
            pairs = [
                (new_player_id, new_player_path, opp["id"], opp_path),
                (opp["id"], opp_path, new_player_id, new_player_path),
            ]
            for bp_id, bp_path, wp_id, wp_path in pairs:
                result    = runner.run_game(bp_path, wp_path)
                winner_id = _color_to_id(result["winner"], bp_id, wp_id)
                db.insert_game(
                    tid, bp_id, wp_id, winner_id,
                    result["move_count"], result["result_type"],
                    result["error_msg"], result["history"], result["final_board"],
                )

        db.recompute_rankings()
        db.finish_tournament(tid)
        log.info("Upload matches done for player %d", new_player_id)

    except Exception as exc:
        log.error("Upload matches failed: %s", exc)
        db.finish_tournament(tid, "failed")


def run_full_tournament(kind="scheduled"):
    """Round-robin among all active players. Thread-safe via lock."""
    if not _lock.acquire(blocking=False):
        log.info("Tournament already running, skipping (%s)", kind)
        return None

    try:
        players = db.get_all_players()
        if len(players) < 2:
            log.info("Not enough players for a tournament (%d)", len(players))
            return None

        log.info("Starting %s tournament with %d players", kind, len(players))
        tid = db.create_tournament(kind)

        for bp, wp in itertools.permutations(players, 2):
            bp_path = str(PLAYERS_DIR / bp["filename"])
            wp_path = str(PLAYERS_DIR / wp["filename"])
            result    = runner.run_game(bp_path, wp_path)
            winner_id = _color_to_id(result["winner"], bp["id"], wp["id"])
            db.insert_game(
                tid, bp["id"], wp["id"], winner_id,
                result["move_count"], result["result_type"],
                result["error_msg"], result["history"], result["final_board"],
            )
            outcome = (
                "draw" if winner_id is None
                else ("B wins" if winner_id == bp["id"] else "W wins")
            )
            log.info("  %s (B) vs %s (W): %s", bp["name"], wp["name"], outcome)

        db.recompute_rankings()
        db.finish_tournament(tid)
        log.info("Tournament %d complete", tid)
        return tid

    except Exception as exc:
        log.error("Tournament failed: %s", exc)
        return None

    finally:
        _lock.release()


def trigger_now():
    """Start a manual full tournament in a background thread."""
    t = threading.Thread(target=run_full_tournament, args=("manual",), daemon=True)
    t.start()


def start_scheduler(app):
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        run_full_tournament,
        "interval",
        minutes=TOURNAMENT_INTERVAL,
        id="tournament",
        misfire_grace_time=300,
    )
    _scheduler.start()
    log.info("Scheduler started: tournament every %d minutes", TOURNAMENT_INTERVAL)


def get_next_run():
    """Return the next scheduled tournament time (datetime with tz), or None."""
    if _scheduler is None:
        return None
    job = _scheduler.get_job("tournament")
    return job.next_run_time if job else None
