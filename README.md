# Juego de ritmo multijugador (Raspberry Pi) - Arquitectura de Computadores 2026-27

```bash
pip install -r requirements.txt
python main.py        # http://<ip-raspberry>:5000   (teclas 1-4 = pulsadores simulados)
```
Documento de arquitectura (entrega ALUD): `docs/ARQUITECTURA.md`.

## Cumplimiento del enunciado
| Requisito | Donde |
|---|---|
| >= 2 procesos | WEB (main), ENGINE, AUDIO (`main.py`) |
| >= 2 hilos | juez, GPIO, LED, DB, SSE (`processes/engine_proc.py`) |
| 1 LED + 1 pulsador | `hw/io.py` |
| Servidor web (Flask) | `web/app.py` |
| Extra: BD + tiempo real | SQLite (`storage/db.py`) + SSE |
| Extra: Git | repositorio del grupo |

## Hoja de ruta
1. [x] Esqueleto con procesos, hilos, memoria compartida
2. [ ] Pulsadores y LEDs reales (pines en `config.py`)
3. [ ] Graficos (carriles por jugador, efectos)
4. [ ] Sincronizacion con musica (usar `audio_pos`, calibrar `AUDIO_LATENCY_S`)
5. [ ] Pruebas de latencia, robustez, diagrama final y demo
