"""Configuracion central del juego."""

# --- Jugadores: un pulsador y un LED por jugador (pines GPIO, numeracion BCM)
# Minimo exigido por el enunciado: 1 LED + 1 pulsador. Ajustar a los pines reales.
PLAYERS = {
    1: {"name": "Jugador 1", "button": 27,  "led": 12},
    2: {"name": "Jugador 2", "button": 17,  "led": 16},
    3: {"name": "Jugador 3", "button": 13, "led": 20},
    4: {"name": "Jugador 4", "button": 19, "led": 21},
}
MAX_PLAYERS = len(PLAYERS)

# --- Juicio de pulsaciones: (nombre, tolerancia en s, puntos)
JUDGEMENT_WINDOWS = [
    ("perfect", 0.050, 300),
    ("good",    0.120, 100),
    ("miss",    0.200,   0),
]
JUDGE_CODES = {"perfect": 1, "good": 2, "miss": 3}   # codigos en memoria compartida

# --- Tiempos
COUNTDOWN_S = 3.0
TICK_S = 0.005               # periodo del hilo juez
NOTE_LOOKAHEAD_S = 2.5
AUDIO_LATENCY_S = 0.0        # CALIBRAR: retardo de salida de audio de la Raspberry
LED_FLASH_S = 0.12

# --- Rutas
CHARTS_DIR = "charts"
AUDIO_DIR = "web/static/audio"
DB_PATH = "scores.db"

# --- Web
HOST, PORT = "0.0.0.0", 5000

# Fuerza pulsadores/LED simulados (desarrollo en PC). Sin gpiozero se activa solo.
USE_MOCK_HW = False
