import os
import sqlite3
import threading
import time
from datetime import datetime

import psutil
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DB_PATH = "/data/metrics.db"
INTERVALO = int(os.getenv("INTERVALO_SEGUNDOS", "60"))

app = FastAPI(
    title="Pi Metrics API & Homelab Dashboard",
    description="API de monitoreo y persistencia en SQLite para laboratorio de virtualización.",
    version="1.2.0"
)

# Montar la carpeta de recursos estáticos para el frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


def leer_temperatura():
    """Obtiene la temperatura del SoC en °C directamente desde el kernel de Linux (DietPi / Raspberry Pi OS)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except Exception:
        return None


def medir():
    """Recolecta métricas instantáneas del procesador, memoria RAM, swap, disco y uptime."""
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
    """Inicializa la tabla de métricas en SQLite si no existe."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS metricas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, cpu REAL, ram REAL, ram_mb REAL,
            swap_mb REAL, temp REAL, disco REAL, uptime INTEGER)""")


def guardar(m):
    """Inserta una lectura de métricas en la base de datos."""
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO metricas(fecha,cpu,ram,ram_mb,swap_mb,temp,disco,uptime)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (m["fecha"], m["cpu_porcentaje"], m["ram_porcentaje"],
             m["ram_mb_usados"], m["swap_mb_usados"], m["temperatura_c"],
             m["disco_porcentaje"], m["uptime_segundos"]))


def recolector():
    """Hilo secundario en segundo plano para muestreo periódico."""
    while True:
        guardar(medir())
        time.sleep(INTERVALO)


@app.on_event("startup")
def arranque():
    init_db()
    threading.Thread(target=recolector, daemon=True).start()


@app.get("/")
def serve_dashboard():
    """Sirve la interfaz gráfica en HTML/JS."""
    return FileResponse("static/index.html")


@app.get("/metrics")
def metrics():
    """Endpoint para obtener las métricas actuales en formato JSON."""
    return medir()


@app.get("/historial")
def historial(n: int = 20):
    """Devuelve los últimos N registros almacenados en la base de datos SQLite."""
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
    """Liveness check para docker u orquestadores."""
    return {"estado": "ok"}


@app.post("/action/log")
def register_homelab_event(event_name: str):
    """Endpoint POST para registrar eventos operativos."""
    timestamp = datetime.now().isoformat()
    return {
        "status": "success",
        "message": f"Evento '{event_name}' procesado correctamente a las {timestamp}."
    }