"""Estado compartido ENTRE PROCESOS (multiprocessing, memoria compartida).

Quien escribe cada campo:
  state, t0, scores...  -> proceso ENGINE (unico escritor)
  audio_pos             -> proceso AUDIO  (unico escritor)
  stop_event            -> proceso MAIN   (apaga todo)
Lectores: proceso WEB (snapshot para SSE) y ENGINE (audio_pos).

Todos los campos multi-valor se actualizan/leen bajo self.lock para que la web
nunca vea un estado a medias (p.ej. score nuevo con combo antiguo).
"""
import time

IDLE, COUNTDOWN, PLAYING, FINISHED = 0, 1, 2, 3
STATE_NAMES = {IDLE: "idle", COUNTDOWN: "countdown", PLAYING: "playing", FINISHED: "finished"}
JUDGE_NAMES = {0: None, 1: "perfect", 2: "good", 3: "miss"}


class SharedState:
    def __init__(self, ctx, n_players: int):
        self.n = n_players
        self.lock = ctx.Lock()
        self.state = ctx.Value("i", IDLE, lock=False)
        self.t0 = ctx.Value("d", 0.0, lock=False)          # instante monotonic de song_time=0
        self.audio_pos = ctx.Value("d", 0.0, lock=False)   # segundos reproducidos (AUDIO -> ENGINE)
        self.active = ctx.Array("i", n_players, lock=False)  # 1 si el jugador participa
        self.score = ctx.Array("i", n_players, lock=False)
        self.combo = ctx.Array("i", n_players, lock=False)
        self.perfect = ctx.Array("i", n_players, lock=False)
        self.good = ctx.Array("i", n_players, lock=False)
        self.miss = ctx.Array("i", n_players, lock=False)
        self.last = ctx.Array("i", n_players, lock=False)  # ultimo juicio (codigo)
        self.title = ctx.Array("c", 64, lock=False)
        self.stop_event = ctx.Event()

    # monotonic es un reloj del sistema: es comparable entre procesos
    def song_time(self) -> float:
        return time.monotonic() - self.t0.value

    def reset(self, players, title: str, t0: float):
        with self.lock:
            for i in range(self.n):
                self.active[i] = 1 if (i + 1) in players else 0
                self.score[i] = self.combo[i] = self.last[i] = 0
                self.perfect[i] = self.good[i] = self.miss[i] = 0
            self.title.value = title.encode("utf-8")[:63]
            self.t0.value = t0
            self.state.value = COUNTDOWN

    def snapshot(self) -> dict:
        with self.lock:
            players = {
                i + 1: {
                    "score": self.score[i], "combo": self.combo[i],
                    "perfect": self.perfect[i], "good": self.good[i], "miss": self.miss[i],
                    "last": JUDGE_NAMES[self.last[i]],
                }
                for i in range(self.n) if self.active[i]
            }
            return {
                "state": STATE_NAMES[self.state.value],
                "song_time": self.song_time(),
                "audio_pos": self.audio_pos.value,
                "title": self.title.value.decode("utf-8", "ignore"),
                "players": players,
            }
