# AySO Virtualización: homelab con contenedores en una Raspberry Pi 3B+

Repositorio con la configuración, el código y la documentación del Trabajo Práctico Integrador de **Arquitectura y Sistemas Operativos** (Tecnicatura Universitaria en Programación a Distancia, UTN).

El proyecto monta un pequeño *home-lab* con varios servicios usando **virtualización por contenedores (Docker)** sobre hardware de bajos recursos.

> **Observación:** todo el trabajo se realizó sobre una Raspberry Pi 3B+ con un pen drive USB de 64 GB para los datos, pero la guía sirve igual para una PC antigua o una mini PC. Con una máquina más potente se pueden sumar más servicios, o servicios más pesados. Varias decisiones de esta configuración se tomaron justamente por las limitaciones del hardware disponible.

## Hardware y sistema base

| Componente | Detalle |
|---|---|
| Equipo | Raspberry Pi 3B+ (1 GB de RAM), conectada al router por Ethernet |
| Almacenamiento | Pen drive USB Kingston 3.0 de 64 GB, montado en `/mnt/usb-backup` |
| Sistema operativo | DietPi (basado en Debian). La misma configuración funciona en Debian Stable |
| Paquetes | Docker y Docker Compose |

DietPi usa unos 50 MB de RAM recién instalado y, con todos los contenedores en marcha, el conjunto consume menos de 400 MB. Quedan unos 600 MB libres por si en el futuro se agrega otro servicio.

> La Raspberry Pi 3B+ solo tiene puertos USB 2.0, así que el pen drive USB 3.0 funciona a la velocidad de USB 2.0.

La instalación inicial de DietPi no se documenta acá porque ya está explicada con claridad en su [documentación oficial](https://dietpi.com/docs/).

## Servicios

| Servicio | Puerto publicado | Descripción |
|---|---|---|
| **Nginx** | 80 | Proxy inverso. Es el único punto de entrada a la API: recibe las peticiones y las reenvía al puerto 8000 del contenedor de la API. |
| **Home-LAN API** | ninguno (8000, solo red interna) | API propia en Python/FastAPI. Mide métricas del sistema, las guarda en SQLite y sirve un dashboard web. Solo se accede a través de Nginx. |
| **Pi-hole** | 53 (TCP/UDP), 8080 (panel web) | Servidor DNS que bloquea publicidad y dominios no deseados para los dispositivos de la LAN. |
| **Uptime Kuma** | 3001 | Herramienta de monitorización autoalojada. Actualmente hace un ping a la API cada 30 minutos y deja registro de las caídas, pero tiene muchas más funciones. |
| **Portainer CE** | 9000 | Gestor visual de contenedores Docker desde el navegador. |

Decisiones de diseño:

- **Aislamiento:** la API vive en la red interna `app_net` y no publica puertos; solo Nginx queda expuesto hacia afuera. Portainer, Uptime Kuma y Pi-hole publican sus propios puertos de administración.
- **Persistencia:** los datos de Pi-hole, Portainer, Uptime Kuma y la base SQLite de la API se guardan en el USB (`/mnt/usb-backup/homelab-data`) mediante *bind mounts*.
- **Límites de recursos:** 128 MB para la API y 32 MB para Nginx (`mem_limit`).
- **Reinicio automático:** todos los contenedores usan `restart: unless-stopped`.
- **Secretos:** la contraseña de Pi-hole y la zona horaria van en un archivo `.env` separado (que no se sube al repositorio), no dentro del `docker-compose.yml`.

## Estructura del repositorio

```text
.
├── docker-compose.yml     # Configuración completa del stack (proyecto "homelab")
├── env.example            # Modelo del archivo .env (variables de Pi-hole)
├── README.md
├── .gitignore
├── api/
│   ├── Dockerfile         # Imagen de la API (python:3.12-slim + uvicorn)
│   ├── main.py            # Código de la API (FastAPI)
│   ├── requirements.txt   # Dependencias: fastapi, uvicorn, psutil
│   └── static/
│       └── index.html     # Dashboard web de métricas
├── nginx/
│   └── nginx.conf         # Proxy inverso hacia la API
└── scripts/
    └── backup.sh          # Copia de seguridad semanal
```

Descripción de los archivos:

- **`docker-compose.yml`**: define los cinco contenedores, la red interna y los volúmenes. Al ejecutar `docker compose up -d --build` construye la imagen de la API y levanta todo el servidor.
- **`env.example`**: modelo del archivo de variables de entorno de Pi-hole (`TZ` y `PIHOLE_PASSWORD`). Se copia como `.env` y se completa. Las variables van separadas y ocultas para que, si alguien ingresa al servidor, no encuentre contraseñas dentro de los archivos de configuración.
- **`api/Dockerfile`**: configuración de Python para la API. Debe estar dentro de `api/` para que el `build` funcione.
- **`api/main.py`**: el corazón de la API. Si querés ampliarla, este es tu archivo; con un poco de lectura de FastAPI hasta se le puede agregar un pequeño CRUD.
- **`api/requirements.txt`**: módulos que se instalan dentro del contenedor para levantar el servidor Uvicorn y la API.
- **`api/static/index.html`**: dashboard agregado a último momento para mostrar las métricas en el navegador. Consulta la API cada 5 segundos.
- **`nginx/nginx.conf`**: configuración mínima del proxy inverso. Hacia la API solo se llega por el puerto 80 de Nginx, que reenvía al puerto 8000 del contenedor donde escucha Uvicorn.
- **`scripts/backup.sh`**: script de copia de seguridad (ver más abajo).

## API

| Endpoint | Descripción |
|---|---|
| `GET /` | Dashboard web |
| `GET /metrics` | Métricas actuales en JSON (CPU, RAM, swap, temperatura del SoC, disco y uptime) |
| `GET /historial?n=N` | Últimos N registros guardados en SQLite (20 por defecto) |
| `GET /salud` | Verificación de estado: responde `{"estado": "ok"}` |
| `POST /action/log?event_name=...` | Registra un evento operativo y devuelve una confirmación |

Un hilo en segundo plano guarda una lectura en la base de datos cada 60 segundos (configurable con la variable `INTERVALO_SEGUNDOS`). El dashboard consulta la API cada 5 segundos.

## Despliegue

Requisitos: DietPi (o Debian) con Docker y el plugin Docker Compose instalados, y el pen drive USB montado en `/mnt/usb-backup`.

1. Crear las carpetas de datos en el USB:

   ```bash
   mkdir -p /mnt/usb-backup/homelab-data/{api,portainer,uptime-kuma}
   mkdir -p /mnt/usb-backup/homelab-data/pihole/{etc-pihole,etc-dnsmasq.d}
   ```

2. Clonar el repositorio en el USB:

   ```bash
   git clone https://github.com/cusquitonet/AySO_Virtualizacion.git /mnt/usb-backup/homelab-proyecto
   cd /mnt/usb-backup/homelab-proyecto
   ```

3. Crear el archivo de variables de entorno y completarlo (zona horaria y contraseña de Pi-hole):

   ```bash
   cp env.example .env
   chmod 600 .env
   nano .env
   ```

4. Construir e iniciar los contenedores:

   ```bash
   docker compose up -d --build
   ```

5. Verificar el estado:

   ```bash
   docker compose ps
   curl http://localhost/salud
   ```

Accesos desde la red local (reemplazar `IP` por la de la Raspberry Pi):

- Dashboard de la API: `http://IP`
- Portainer: `http://IP:9000`
- Uptime Kuma: `http://IP:3001`
- Pi-hole (panel): `http://IP:8080/admin`. Para que bloquee publicidad, configurar la IP de la Raspberry Pi como servidor DNS (en el router o en cada dispositivo).

> **Nota sobre Pi-hole:** la contraseña del panel se define con la variable `FTLCONF_webserver_api_password` (Pi-hole v6 o superior; la variable `WEBPASSWORD` de versiones anteriores ya no se usa). El `docker-compose.yml` la toma de `PIHOLE_PASSWORD` en el archivo `.env`.

## Copias de seguridad

`scripts/backup.sh` genera dos archivos comprimidos dentro de `/mnt/usb-backup/backups`:

- `homelab-data-FECHA.tar.gz`: datos de los contenedores (Pi-hole, Portainer, Uptime Kuma y SQLite de la API).
- `homelab-proyecto-FECHA.tar.gz`: configuración del proyecto (compose, código fuente y Nginx).

Después de cada copia se aplica una **rotación: se conservan solo los 4 backups más recientes de cada tipo** y se eliminan los más viejos, para que el espacio no se llene con archivos antiguos.

Como los datos de los contenedores pertenecen a root, el script se auto-eleva con `sudo` si se ejecuta sin privilegios. Para programar la ejecución semanal (domingos a las 03:00), agregar esta línea al crontab de root (`sudo crontab -e`):

```cron
0 3 * * 0 /bin/bash /mnt/usb-backup/homelab-proyecto/scripts/backup.sh >> /var/log/homelab_backup.log 2>&1
```

> **Limitación conocida:** las copias se guardan en el mismo USB que los datos, lo cual no es lo ideal (si el pen drive falla se pierde todo). Si tenés otro pen drive o un NAS, solo hay que cambiar la variable `DEST` del script para que apunte a ese destino.

## Limitaciones y mejoras posibles

- Portainer monta el socket de Docker (`/var/run/docker.sock`), lo que le da control total sobre Docker: conviene usar una contraseña robusta y no exponerlo fuera de la LAN.
- Varias imágenes usan la etiqueta `latest`; fijar versiones específicas daría más reproducibilidad.
- Posibles ampliaciones: copias de seguridad en otro dispositivo o NAS, más monitores en Uptime Kuma y un CRUD en la API.

## Notas finales

Si te gusta lo que armamos y querés usarlo, sos libre de hacerlo. Si querés colaborar o darnos ideas para ampliar este pequeño proyecto, también estamos abiertos a escucharte: no hace falta aportar código o configuraciones, a veces una idea genera más avances que lo técnico.

Este proyecto es, por ahora, de dos personas, pero nunca se sabe hasta dónde puede llegar.
