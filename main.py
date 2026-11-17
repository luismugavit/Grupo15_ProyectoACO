"""Punto de entrada. Lanza los 3 procesos del juego:

  MAIN/WEB  (este proceso)  -> Flask + SSE
  ENGINE    (multiprocessing) -> logica, pulsadores, LEDs, DB (varios hilos)
  AUDIO     (multiprocessing) -> musica y reloj de audio

Uso:  python main.py
"""
import multiprocessing as mp

import config
from core.shared import SharedState
from processes.audio_proc import run_audio
from processes.engine_proc import run_engine
from web.app import create_app


def main():
    ctx = mp.get_context("spawn")        # 'spawn': seguro con GPIO/pygame
    shared = SharedState(ctx, config.MAX_PLAYERS)
    cmd_q = ctx.Queue()                  # WEB    -> ENGINE (ordenes)
    audio_q = ctx.Queue()                # ENGINE -> AUDIO  (play/stop)

    procs = [
        ctx.Process(target=run_engine, args=(shared, cmd_q, audio_q), name="engine"),
        ctx.Process(target=run_audio, args=(shared, audio_q), name="audio"),
    ]
    for p in procs:
        p.start()

    app = create_app(shared, cmd_q)
    try:
        app.run(host=config.HOST, port=config.PORT, threaded=True, use_reloader=False)
    finally:
        shared.stop_event.set()
        for p in procs:
            p.join(timeout=3)
            if p.is_alive():
                p.terminate()


if __name__ == "__main__":
    main()
