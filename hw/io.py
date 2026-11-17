
"""
Entradas/salidas físicas:
- Pulsador: GPIO 27 (sensor).
- LEDs: actuadores.

Se utiliza exclusivamente RPi.GPIO.
Los callbacks de los pulsadores se ejecutan mediante
el sistema de detección de eventos de RPi.GPIO.

Sin GPIO se utiliza el modo MOCK.
"""

import time
from typing import Callable

import config

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None


def hardware_available() -> bool:
    return GPIO is not None and not config.USE_MOCK_HW


class ButtonInput:
    def __init__(self, callback: Callable[[int, float], None]):
        self.mock = not hardware_available()
        self.callback = callback

        if self.mock:
            print("[hw] pulsador en MOCK (teclas / POST /api/debug/press/<n>)")
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Único pulsador conectado al GPIO 27
            GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Detección de pulsación
            GPIO.add_event_detect(
                27,
                GPIO.FALLING,
                callback=self._on_pressed,
                bouncetime=10
            )

            print("[hw] pulsador habilitado en GPIO 27")

        except Exception as e:
            print(f"[hw] GPIO no disponible ({e}); MOCK")
            self.mock = True

    def _on_pressed(self, channel):
        # Marca temporal lo antes posible
        timestamp = time.monotonic()

        # Se mantiene la firma original del callback
        self.callback(1, timestamp)


class LedOutput:
    def __init__(self):
        self.leds = {}
        self.mock = not hardware_available()

        if self.mock:
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Configuración de los LEDs definidos en config
            for pid, cfg in config.PLAYERS.items():
                led_pin = cfg["led"]
                GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.LOW)
                self.leds[pid] = led_pin

        except Exception as e:
            print(f"[hw] Error configurando LEDs: {e}")
            self.mock = True

    def set(self, pid: int, on: bool):
        if self.mock:
            return

        led_pin = self.leds.get(pid)

        if led_pin is not None:
            GPIO.output(
                led_pin,
                GPIO.HIGH if on else GPIO.LOW
            )


def cleanup():
    """Libera los recursos GPIO."""
    if GPIO is not None:
        GPIO.cleanup()
