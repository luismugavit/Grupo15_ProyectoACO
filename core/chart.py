"""Carga de charts (secuencias de notas) desde JSON."""
import json
import os
from dataclasses import dataclass, field

import config


@dataclass
class Chart:
    title: str
    audio_file: str
    bpm: float
    offset: float
    notes: list[float] = field(default_factory=list)   # instantes (s) de cada nota

    @staticmethod
    def load(name: str) -> "Chart":
        path = os.path.join(config.CHARTS_DIR, f"{os.path.basename(name)}.json")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        bpm, offset = d["bpm"], d.get("offset", 0.0)
        if "times" in d:
            notes = sorted(d["times"])
        else:
            notes = sorted(offset + b * 60.0 / bpm for b in d["beats"])
        return Chart(d["title"], d["audio_file"], bpm, offset, notes)
