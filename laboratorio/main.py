"""API de metricas de la Raspberry Pi.
Guarda una medicion cada INTERVALO_SEGUNDOS en SQLite (/data/metrics.db),
persistido en el USB fuera del ciclo de vida del contenedor.
"""
import os
import sqlite3
import threading
import time
from datetime import datetime

import psutil
from fastapi import FastAPI

DB_PATH = "/data/metrics.db"
INTERVALO = int(os.getenv("INTERVALO_SEGUNDOS", "60"))

app = FastAPI(title="Pi Metrics API")


def leer_temperatura():
    """Temperatura del SoC en °C (DietPi / Raspberry Pi OS)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except Exception:
        return None


def medir():
    vm = psutil.virtual_memory()
    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "cpu_porcentaje": psutil.cpu_percent(interval=None),
        "ram_porcentaje": vm.percent,
        "ram_mb_usados": round(vm.used / 1024**2, 1),
        "swap_mb_usados": round(psutil.swap_memory().used / 1024**2, 1),
        "temperatura_c": leer_temperatura(),
        "disco_porcentaje": psutil.disk_usage("/").percent,
        "uptime_segundos": int(time.time() - psutil.boot_time()),
    }


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS metricas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, cpu REAL, ram REAL, ram_mb REAL,
            swap_mb REAL, temp REAL, disco REAL, uptime INTEGER)""")


def guardar(m):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO metricas(fecha,cpu,ram,ram_mb,swap_mb,temp,disco,uptime)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (m["fecha"], m["cpu_porcentaje"], m["ram_porcentaje"],
             m["ram_mb_usados"], m["swap_mb_usados"], m["temperatura_c"],
             m["disco_porcentaje"], m["uptime_segundos"]))


def recolector():
    while True:
        guardar(medir())
        time.sleep(INTERVALO)


@app.on_event("startup")
def arranque():
    init_db()
    threading.Thread(target=recolector, daemon=True).start()


@app.get("/metrics")
def metrics():
    return medir()


@app.get("/historial")
def historial(n: int = 20):
    with sqlite3.connect(DB_PATH) as con:
        filas = con.execute(
            "SELECT fecha,cpu,ram,ram_mb,swap_mb,temp,disco,uptime"
            " FROM metricas ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [
        {"fecha": f, "cpu": c, "ram": r, "ram_mb": rm, "swap_mb": s,
         "temp": t, "disco": d, "uptime": u}
        for f, c, r, rm, s, t, d, u in filas
    ]


@app.get("/salud")
def salud():
    return {"estado": "ok"}
