"""Entradas/salidas fisicas: pulsadores (sensor) y LEDs (actuador).

gpiozero ejecuta los callbacks de los pulsadores en SUS PROPIOS HILOS
(hilos de entrada). Sin gpiozero/GPIO se usan versiones simuladas.
"""
import time
from typing import Callable

import config

try:
    from gpiozero import LED, Button
except Exception:
    LED = Button = None


def hardware_available() -> bool:
    return Button is not None and not config.USE_MOCK_HW


class ButtonInput:
    def __init__(self, callback: Callable[[int, float], None]):
        self.buttons = {}
        self.mock = not hardware_available()
        if self.mock:
            print("[hw] pulsadores en MOCK (teclas 1-4 / POST /api/debug/press/<n>)")
            return
        try:
            for pid, cfg in config.PLAYERS.items():
                b = Button(cfg["button"], pull_up=True, bounce_time=0.01)
                # marca de tiempo lo antes posible -> menor latencia
                b.when_pressed = lambda pid=pid: callback(pid, time.monotonic())
                self.buttons[pid] = b
        except Exception as e:
            print(f"[hw] GPIO no disponible ({e}); MOCK")
            self.mock = True


class LedOutput:
    def __init__(self):
        self.leds = {}
        self.mock = not hardware_available()
        if self.mock:
            return
        try:
            for pid, cfg in config.PLAYERS.items():
                self.leds[pid] = LED(cfg["led"])
        except Exception:
            self.mock = True

    def set(self, pid: int, on: bool):
        if self.mock:
            return
        led = self.leds.get(pid)
        if led:
            led.on() if on else led.off()
