# Homelab Virtualization & System Telemetry (Raspberry Pi 3+)

Este repositorio contiene la arquitectura completa, configuraciones e implementación de software para el proyecto final de laboratorio de virtualización.

## 🏗️ Arquitectura del Sistema

El proyecto despliega una solución contenerizada con **Docker** y **Docker Compose** sobre el sistema operativo **DietPi (64-bit)** en una **Raspberry Pi 3+**, utilizando almacenamiento USB externo para la persistencia de datos.

### Servicios Desplegados

* **API Telemetría & Dashboard (Puerto 80 / 8000)**: Servicio backend en FastAPI con hilos concurrentes en segundo plano para muestreo de hardware, almacenamiento en SQLite e interfaz web estática en Tailwind CSS.
* **Nginx (Puerto 80)**: Proxy inverso web para encaminamiento transparente de peticiones HTTP.
* **Uptime Kuma (Puerto 3001)**: Dashboard interactivo para la monitorización de servicios locales y tasa de disponibilidad (SLA).
* **Portainer CE (Puerto 9000)**: Interfaz de administración gráfica del motor Docker.
* **Pi-hole (Puerto 8080)**: Servidor de nombres DNS y filtro de contenido de red.

---

## 🛠️ Estructura del Repositorio

```text
.
├── docker-compose.yml
├── README.md
└── api/
    ├── Dockerfile
    ├── main.py
    ├── requirements.txt
    └── static/
        └── index.html
```

---

## 🚀 Despliegue en Entorno de Producción

1. Clonar el repositorio en la Raspberry Pi:
   ```bash
   git clone https://github.com/tu-usuario/homelab-raspberrypi.git
   cd homelab-raspberrypi
   ```

2. Construir e iniciar la pila de contenedores:
   ```bash
   docker compose up -d --build
   ```

3. Verificar estado de los servicios:
   ```bash
   docker compose ps
   ```
