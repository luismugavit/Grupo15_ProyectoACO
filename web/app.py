"""PROCESO WEB (proceso principal): Flask + SSE.

No contiene logica de juego: lee SharedState y envia ordenes por cmd_q.
"""
import json
import time

from flask import Flask, Response, jsonify, render_template, request

import config
from core.chart import Chart
from storage import db


def create_app(shared, cmd_q):
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", players=config.PLAYERS)

    @app.post("/api/start")
    def start():
        data = request.get_json(silent=True) or {}
        players = [int(p) for p in data.get("players", list(config.PLAYERS))]
        cmd_q.put({"cmd": "start", "chart": data.get("chart", "demo"), "players": players})
        return jsonify(ok=True)

    @app.post("/api/stop")
    def stop():
        cmd_q.put({"cmd": "stop"})
        return jsonify(ok=True)

    @app.get("/api/chart/<name>")
    def chart(name):
        c = Chart.load(name)
        return jsonify(title=c.title, notes=c.notes, lookahead=config.NOTE_LOOKAHEAD_S)

    @app.get("/api/stream")
    def stream():
        """Server-Sent Events: estado en tiempo real (~30 Hz)."""
        def gen():
            while not shared.stop_event.is_set():
                yield f"data: {json.dumps(shared.snapshot())}\n\n"
                time.sleep(1 / 30)
        return Response(gen(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache"})

    @app.get("/api/highscores")
    def highscores():
        return jsonify(db.top_scores())

    @app.post("/api/debug/press/<int:player>")
    def debug_press(player):
        cmd_q.put({"cmd": "press", "player": player, "ts": time.monotonic()})
        return jsonify(ok=True)

    return app
