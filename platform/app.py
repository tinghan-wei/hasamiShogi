import logging
import os
import re
import threading
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

import db
import scheduler
import security

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

PLAYERS_DIR = Path(__file__).parent / "players"
PLAYERS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024  # 100 KB hard limit


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def leaderboard():
    rankings    = db.get_ranking_rows()
    total_games = sum(r["games"] for r in rankings) // 2
    last_t      = db.get_last_tournament_time()
    next_run    = scheduler.get_next_run()
    return render_template(
        "leaderboard.html",
        rankings=rankings,
        total_games=total_games,
        last_tournament=last_t,
        next_run=next_run,
    )


@app.route("/player/<int:player_id>")
def player_detail(player_id):
    player = db.get_player(player_id)
    if player is None:
        flash("Player not found.", "danger")
        return redirect(url_for("leaderboard"))
    stats = db.get_player_stats(player_id)
    games = db.get_recent_games(player_id, limit=30)
    return render_template("player.html", player=player, stats=stats, games=games)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    name = request.form.get("name", "").strip()
    f    = request.files.get("file")

    # ── Validate name ─────────────────────────────────────────────────────────
    if not name or not re.fullmatch(r"[A-Za-z0-9_]{1,32}", name):
        flash("Player name must be 1–32 characters: letters, digits, underscores only.", "danger")
        return render_template("upload.html")

    # ── Validate file ─────────────────────────────────────────────────────────
    if not f or not f.filename:
        flash("Please select a .py file.", "danger")
        return render_template("upload.html")

    if not f.filename.lower().endswith(".py"):
        flash("Only .py files are accepted.", "danger")
        return render_template("upload.html")

    source = f.read().decode("utf-8", errors="replace")

    # ── AST security check ────────────────────────────────────────────────────
    ok, reason = security.check_player_source(source)
    if not ok:
        flash(
            f"Upload rejected — {reason}. "
            "See the allowed imports list below.",
            "danger",
        )
        return render_template("upload.html")

    # ── Save file ─────────────────────────────────────────────────────────────
    filename = f"{name}.py"
    filepath = PLAYERS_DIR / filename
    filepath.write_text(source, encoding="utf-8")

    # ── Register in DB ────────────────────────────────────────────────────────
    try:
        player_id, is_new = db.upsert_player(name, filename)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        flash(f"Database error: {e}", "danger")
        return render_template("upload.html")

    top_n = int(os.environ.get("TOP_N", "8"))
    if is_new:
        msg = f'"{name}" registered! Playing against up to {top_n} top players in the background.'
    else:
        msg = f'"{name}" updated! Playing new immediate games in the background.'

    flash(msg + " Refresh in a minute to see results.", "success")

    t = threading.Thread(
        target=scheduler.run_upload_matches,
        args=(player_id, str(filepath)),
        daemon=True,
    )
    t.start()

    return redirect(url_for("leaderboard"))


@app.route("/run-tournament", methods=["POST"])
def run_tournament_now():
    scheduler.trigger_now()
    flash("Full tournament started — results will appear in a few minutes.", "info")
    return redirect(url_for("leaderboard"))


# ── Startup ───────────────────────────────────────────────────────────────────

db.init_db()
scheduler.start_scheduler(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
