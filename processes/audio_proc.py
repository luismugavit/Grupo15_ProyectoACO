"""PROCESO AUDIO: reproduce la musica y publica su posicion.

Por que un proceso aparte: la decodificacion/salida de audio no debe competir
por el GIL con el motor ni con la web, y su posicion es el reloj maestro para
la sincronizacion musica <-> graficos.

Entrada : audio_q (ordenes {"cmd": "play"|"stop", ...}) desde ENGINE.
Salida  : shared.audio_pos (segundos reproducidos).
"""
import os
import queue
import time

import config

try:
    import pygame
except ImportError:
    pygame = None


def run_audio(shared, audio_q):
    ready = False
    if pygame:
        try:
            pygame.mixer.init()
            ready = True
        except Exception as e:
            print(f"[audio] sin dispositivo de audio: {e}")
    else:
        print("[audio] pygame no instalado: audio simulado")

    playing = False
    play_at = None            # instante monotonic en el que debe sonar

    while not shared.stop_event.is_set():
        try:
            msg = audio_q.get(timeout=0.01)
        except queue.Empty:
            msg = None

        if msg:
            if msg["cmd"] == "play":
                play_at, playing = msg["at"], False
                path = os.path.join(config.AUDIO_DIR, msg["file"])
                if ready and os.path.exists(path):
                    pygame.mixer.music.load(path)
                else:
                    print(f"[audio] (simulado) {msg['file']}")
            elif msg["cmd"] == "stop":
                play_at, playing = None, False
                if ready:
                    pygame.mixer.music.stop()
                shared.audio_pos.value = 0.0

        # arranque preciso: espera activa en los ultimos ms
        if play_at is not None and not playing and time.monotonic() >= play_at:
            if ready and pygame.mixer.music.get_busy() is False:
                try:
                    pygame.mixer.music.play()
                except Exception:
                    pass
            playing = True

        if playing:
            # TODO(sync): comparar audio_pos con shared.song_time() y corregir deriva
            if ready:
                pos = pygame.mixer.music.get_pos()
                if pos >= 0:
                    shared.audio_pos.value = pos / 1000.0
            else:
                shared.audio_pos.value = time.monotonic() - play_at

    if ready:
        pygame.mixer.quit()
