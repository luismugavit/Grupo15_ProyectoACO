"""Persistencia de resultados en SQLite (se usa SOLO desde un hilo del ENGINE
y desde consultas de lectura puntuales de la web; cada uno abre su conexion)."""
import sqlite3
import time

import config

SCHEMA = """CREATE TABLE IF NOT EXISTS results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL, chart TEXT, player INTEGER, name TEXT,
    score INTEGER, perfect INTEGER, good INTEGER, miss INTEGER)"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_PATH)
    con.execute(SCHEMA)
    return con


def save_result(con, chart, player, name, score, perfect, good, miss):
    con.execute("INSERT INTO results(ts,chart,player,name,score,perfect,good,miss) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (time.time(), chart, player, name, score, perfect, good, miss))
    con.commit()


def top_scores(limit: int = 10):
    con = connect()
    try:
        rows = con.execute("SELECT name,chart,score,ts FROM results "
                           "ORDER BY score DESC LIMIT ?", (limit,)).fetchall()
    finally:
        con.close()
    return [{"name": r[0], "chart": r[1], "score": r[2], "ts": r[3]} for r in rows]
