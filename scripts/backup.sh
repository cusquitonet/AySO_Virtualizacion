#!/bin/bash
# Backup semanal del homelab: datos de contenedores + configuracion.
# Ubicacion: /mnt/usb-backup/homelab-proyecto/scripts/backup.sh
# Destino: /mnt/usb-backup/backups (mismo USB, carpeta separada).
# Retencion: se conservan los 4 backups mas recientes de cada tipo.
# Cron (domingos 03:00, crontab de root):
#   0 3 * * 0 /bin/bash /mnt/usb-backup/homelab-proyecto/scripts/backup.sh >> /var/log/homelab_backup.log 2>&1
set -e

# Los datos de los contenedores son propiedad de root (los procesos
# adentro del contenedor corren como root y escriben en los bind mounts).
# Si se ejecuta sin privilegios, se auto-eleva con sudo.
if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

DEST=/mnt/usb-backup/backups
FECHA=$(date +%Y%m%d-%H%M)
mkdir -p "$DEST"

# 1) Datos de los contenedores (Pi-hole, Portainer, Kuma, SQLite de la API)
tar -czf "$DEST/homelab-data-$FECHA.tar.gz" -C /mnt/usb-backup homelab-data

# 2) Configuracion del proyecto (compose, codigo fuente, nginx)
tar -czf "$DEST/homelab-proyecto-$FECHA.tar.gz" -C /mnt/usb-backup homelab-proyecto

# 3) Rotacion: conservar solo los 4 backups mas recientes de cada tipo
ls -1t "$DEST"/homelab-data-*.tar.gz  | tail -n +5 | xargs -r rm -f
ls -1t "$DEST"/homelab-proyecto-*.tar.gz | tail -n +5 | xargs -r rm -f

echo "[backup] OK -> $DEST (fecha $FECHA)"
