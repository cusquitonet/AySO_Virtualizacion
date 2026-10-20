# Instalacion limpia del homelab desde cero (Raspberry Pi 3B+ · DietPi)

Objetivo: un solo compose con todo (API + Nginx + Portainer + Kuma + Pi-hole),
datos persistentes en el USB, arranque automatico tras corte de luz,
y backup semanal. Un solo comando de despliegue.

================================================================
FASE 0 — VERIFICACION PREVIA (5 min)
================================================================

0.1 Instalar y confirmar que Docker funciona y anotar la version:

    sudo apt install docker
    docker --version
    docker compose version

0.2 Confirmar que el USB esta montado:

    findmnt /mnt/usb-backup
    df -h /mnt/usb-backup

0.3 Verificar que los puertos necesarios estan libres o en uso por lo esperado
    (53/udp DNS, 80 Nginx, 8080 Pi-hole web, 3001 Kuma, 9000 Portainer):

    ss -tlnp | grep -E ':(53|80|8080|3001|9000) '

0.4 Averiguar el UUID del USB (para el arranque automatico, Fase 3):

    sudo blkid /dev/sda1        # anotar el UUID=xxxx

================================================================
FASE 1 — BACKUP DE SEGURIDAD Y LIMPIEZA (10 min)
================================================================

1.1 Backup integral de lo actual (por las dudas):

    sudo tar -czf /mnt/usb-backup/backups/pre-migracion-$(date +%Y%m%d).tar.gz         -C /mnt/usb-backup homelab-data

1.2 Bajar TODO lo que corre hoy (desde la carpeta del compose viejo):

    cd ~/homelab-proyecto          # ajustar: donde este tu compose actual
    docker compose down
    docker compose down -v         # elimina los named volumes viejos
                                     # (los datos estan seguros en el USB)

1.3 Archivar el proyecto viejo (no borrar todavia, por precaucion):

    sudo mv ~/homelab-proyecto /mnt/usb-backup/homelab-proyecto-viejo

Nota: este paso no es necesario si se esta haciendo una instalacion desde cero

================================================================
FASE 2 — ESTRUCTURA NUEVA (10 min)
================================================================

2.1 Crear la carpeta nueva del proyecto DENTRO del USB:

    sudo mkdir -p /mnt/usb-backup/homelab-proyecto
    sudo mkdir -p /mnt/usb-backup/homelab-data/api

2.2 Copiar dentro de /mnt/usb-backup/homelab-proyecto estos archivos
    (manteniendo la estructura de carpetas):

    homelab-proyecto/
    ├── docker-compose.yml
    ├── .env.example   -> copiar a .env y completar la clave de Pi-hole
    ├── backup.sh
    ├── api/
    │   ├── Dockerfile
    │   ├── main.py
    │   └── requirements.txt
    └── nginx/
        └── nginx.conf

2.3 Crear el .env y protegerlo:

    cd /mnt/usb-backup/homelab-proyecto
    cp .env.example .env
    nano .env                      # poner una clave segura en PIHOLE_PASSWORD
    chmod 600 .env

================================================================
FASE 3 — ARRANQUE AUTOMATICO (corte de luz) (10 min)
================================================================

3.1 Montar el USB automaticamente al iniciar:

    sudo nano /etc/fstab

Agregar (con el UUID real de 0.4):

    UUID=TU-UUID  /mnt/usb-backup  ext4  nofail,noatime,x-systemd.device-timeout=5  0  2

Verificar SIN reiniciar:

    sudo systemctl daemon-reload
    sudo mount -a
    findmnt /mnt/usb-backup

3.2 Hacer que Docker ESPERE al USB (evita que arranque contra el data-root
    vacio si el USB tarda en montarse):

    sudo systemctl edit docker.service

Pegar:

    [Unit]
    Requires=mnt-usb-backup.mount
    After=mnt-usb-backup.mount

Guardar y luego:

    sudo systemctl daemon-reload

3.3 Habilitar Docker al inicio (DietPi):

    sudo dietpi-services enable docker

================================================================
FASE 4 — DESPLIEGUE: UN SOLO COMANDO (10-15 min)
================================================================

    cd /mnt/usb-backup/homelab-proyecto
    docker compose up -d --build

La primera construccion de la API en la Pi 3B+ tarda varios minutos: es normal.
Al terminar, verificar:

    docker compose ps              # los 5 servicios deben estar "running"
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

================================================================
FASE 5 — VERIFICACION (10 min)
================================================================

5.1 API via Nginx (todo el trafico entra por el puerto 80):

    curl http://localhost/metrics
    curl "http://localhost/historial?n=5"
    curl http://localhost/salud

5.2 Prueba estrella — PERSISTENCIA del volumen:

    docker compose rm -sf api
    docker compose up -d api
    curl "http://localhost/historial?n=5"     # los datos tienen que seguir ahi

    La DB vive en /mnt/usb-backup/homelab-data/api/metrics.db, fuera del
    contenedor: se puede destruir y recrear el contenedor sin perder nada.

5.3 Herramientas :

    http://<IP-DE-LA-PI>:9000    Portainer
    http://<IP-DE-LA-PI>:3001    Uptime Kuma
    http://<IP-DE-LA-PI>:8080    Pi-hole admin
    
Nota: La primera vez que ingresen van a tener que configurar la contrasena.

5.4 Aislamiento de red:

    docker network inspect homelab_app_net    # solo api y nginx estan ahi
    ss -tlnp | grep ':8000'                   # nada escucha en 8000 afuera:
                                              # la API solo es accesible via Nginx

5.5 Consumo real (datos para la tabla del informe):

    docker stats --no-stream
    free -h

5.6 Configurar Uptime Kuma: nuevo monitor HTTP a http://<IP-DE-LA-PI>/salud
    (demuestra en vivo que el servicio sigue respondiendo).

================================================================
FASE 6 — PRUEBA DE CORTE DE LUZ (10 min)
================================================================

    sudo reboot

Al volver, SIN tocar nada:

    findmnt /mnt/usb-backup     -> montado
    docker ps                   -> los 5 contenedores UP solos
    curl http://localhost/metrics

Tras un reinicio no hace falta intervencion humana, a diferencia de una
maquina virtual de VirtualBox que hay que levantar a mano.

================================================================
FASE 7 — BACKUP SEMANAL AUTOMATIZADO (5 min)
================================================================

7.1 Probar el script:

    chmod +x /mnt/usb-backup/homelab-proyecto/backup.sh
    /mnt/usb-backup/homelab-proyecto/backup.sh
    ls -lh /mnt/usb-backup/backups/

7.2 Programarlo (todos los lunes a las 4:00):

    (crontab -l 2>/dev/null; echo '0 4 * * 1 /mnt/usb-backup/homelab-proyecto/backup.sh >> /mnt/usb-backup/backups/backup.log 2>&1') | crontab -

7.3 Verificar que quedo agendado:

    crontab -l

================================================================
TROUBLESHOOTING
================================================================

- Puerto 80 ocupado:        ss -tlnp | grep ':80 '  (algun servidor web de DietPi?)
- Puerto 53 ocupado:        ss -ulnp | grep ':53 '  (dnsmasq del sistema?)
- Puerto 8000 expuesto:     no debe estarlo; la API entra solo via Nginx.
- temperatura_c = null:     cat /sys/class/thermal/thermal_zone0/temp
- USB no monta al inicio:   sudo journalctl -u mnt-usb-backup.mount -b
