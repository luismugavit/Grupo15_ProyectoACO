"""PROCESO ENGINE: logica del juego + entrada/salida fisica.

Hilos dentro de este proceso:
  1. hilo principal : atiende ordenes de la web (cmd_q)
  2. hilo JUEZ      : reloj, cuenta atras, notas falladas, fin de partida
  3. hilos GPIO     : callbacks de gpiozero -> register_press()   (uno o varios) 
  4. hilo LED       : enciende/apaga LEDs segun el juicio          (led_q)
  5. hilo DB        : guarda resultados en SQLite                  (db_q)

Variables compartidas entre estos hilos: el propio objeto Engine
(next_note, scores locales...) protegido con self.lock (threading.Lock).
Hacia otros procesos se publica en SharedState (memoria compartida).
"""
import queue
import threading
import time

import config
from core import shared as sh
from core.chart import Chart
from hw.io import ButtonInput, LedOutput
from storage import db


class Engine:
    def __init__(self, shared, audio_q):
        self.shared = shared
        self.audio_q = audio_q
        self.lock = threading.Lock()          # protege el estado interno del engine
        self.led_q = queue.Queue()            # hilo juez/GPIO -> hilo LED
        self.db_q = queue.Queue()             # hilo juez -> hilo DB
        self.chart: Chart | None = None
        self.next_note = {}                   # jugador -> indice de la siguiente nota
        self.stop = threading.Event()

    # ------------ ordenes (hilo principal) ------------
    def start_game(self, chart_name: str, players: list[int]):
        self.end_game()
        chart = Chart.load(chart_name)
        t0 = time.monotonic() + config.COUNTDOWN_S
        with self.lock:
            self.chart = chart
            self.next_note = {p: 0 for p in players}
            self.chart_name = chart_name
        self.shared.reset(players, chart.title, t0)
        self.audio_q.put({"cmd": "play", "file": chart.audio_file,
                          "at": t0 - config.AUDIO_LATENCY_S})

    def end_game(self):
        self.audio_q.put({"cmd": "stop"})
        with self.lock:
            self.next_note = {}
        with self.shared.lock:
            self.shared.state.value = sh.IDLE

    # ------------ hilo JUEZ ------------
    def judge_loop(self):
        s = self.shared
        while not self.stop.is_set():
            t = s.song_time()
            with self.lock:
                st = s.state.value
                if st == sh.COUNTDOWN and t >= 0:
                    with s.lock:
                        s.state.value = sh.PLAYING
                elif st == sh.PLAYING and self.chart:
                    self._expire_missed(t)
                    if t > self.chart.notes[-1] + 2.0:
                        with s.lock:
                            s.state.value = sh.FINISHED
                        self._queue_results()
            time.sleep(config.TICK_S)

    def _expire_missed(self, t):
        limit = config.JUDGEMENT_WINDOWS[-1][1]
        for p, i in list(self.next_note.items()):
            while i < len(self.chart.notes) and t - self.chart.notes[i] > limit:
                self._apply(p, "miss", 0)
                i += 1
            self.next_note[p] = i

    # ------------ hilos GPIO (y pulsaciones simuladas) ------------
    def register_press(self, player: int, ts: float):
        with self.lock:
            if self.shared.state.value != sh.PLAYING or player not in self.next_note:
                return
            i = self.next_note[player]
            if i >= len(self.chart.notes):
                return
            delta = abs((ts - self.shared.t0.value) - self.chart.notes[i])
            for name, tol, pts in config.JUDGEMENT_WINDOWS:
                if delta <= tol:
                    self._apply(player, name, pts)
                    self.next_note[player] = i + 1
                    return
            # demasiado pronto: se ignora

    def _apply(self, player, judgement, points):
        """Actualiza memoria compartida (la llama quien tenga self.lock)."""
        s, k = self.shared, player - 1
        with s.lock:
            getattr(s, judgement)[k] += 1
            s.combo[k] = 0 if judgement == "miss" else s.combo[k] + 1
            s.score[k] += points
            s.last[k] = config.JUDGE_CODES[judgement]
        if judgement != "miss":
            self.led_q.put(player)

    # ------------ hilo LED ------------
    def led_loop(self, leds: LedOutput):
        while not self.stop.is_set():
            try:
                pid = self.led_q.get(timeout=0.1)
            except queue.Empty:
                continue
            leds.set(pid, True)
            time.sleep(config.LED_FLASH_S)
            leds.set(pid, False)

    # ------------ hilo DB ------------
    def _queue_results(self):
        s = self.shared
        with s.lock:
            for p in self.next_note:
                k = p - 1
                self.db_q.put((self.chart_name, p, config.PLAYERS[p]["name"],
                               s.score[k], s.perfect[k], s.good[k], s.miss[k]))

    def db_loop(self):
        con = db.connect()          # la conexion SQLite se crea y usa en este hilo
        while not self.stop.is_set():
            try:
                row = self.db_q.get(timeout=0.2)
            except queue.Empty:
                continue
            db.save_result(con, *row)
        con.close()

def run_engine(shared, cmd_q, audio_q):
    eng = Engine(shared, audio_q)
    buttons = ButtonInput(eng.register_press)     # crea hilos GPIO
    leds = LedOutput()

    threads = [
        threading.Thread(target=eng.judge_loop, name="juez", daemon=True),
        threading.Thread(target=eng.led_loop, args=(leds,), name="led", daemon=True),
        threading.Thread(target=eng.db_loop, name="db", daemon=True),
    ]
    for t in threads:
        t.start()

    while not shared.stop_event.is_set():       # hilo principal: ordenes de la web
        try:
            msg = cmd_q.get(timeout=0.1)
        except queue.Empty:
            continue
        try:
            if msg["cmd"] == "start":
                eng.start_game(msg["chart"], msg["players"])
            elif msg["cmd"] == "stop":
                eng.end_game()
            elif msg["cmd"] == "press":           # pulsacion simulada
                eng.register_press(msg["player"], msg["ts"])
        except Exception as e:
            print(f"[engine] error procesando {msg}: {e}")

    eng.stop.set()
    for t in threads:
        t.join(timeout=1)
