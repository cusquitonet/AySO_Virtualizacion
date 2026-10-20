# AySO Virtualization
Repositorio para la configuración y documentación del TPI

Observación: Si bien todo este trabajo esta realizado sobre una raspberry pi 3b+ con un pen drive USB de 64 GB para los datos, la guía puede ser utilizada para una instalación en una PC antigua o mini PC disponible.

Hardware: Raspberry pi 3b+ (Conectada al router por Ethernet)
          Pen drive USB Kingston 3.0 de 64 GB

SO: Diet-pi (Basado en Debian)
Paquetes instalados: Docker

Aclaración: Este taller es realizado como proyecto para un TPI, por lo tanto el hardware utilizado es el que teníamos en casa. Obviamente siempre es mas conveniente tener una maquina mas potente para armar un home-lab, mas si vas a meterle gran cantidad de servicios o algunos mas pesados. Varias de las elecciones para esta configuración fueron hechas teniendo en cuenta las limitaciones de esta configuración. Diet-pi utiliza solo 50 Mb de RAM recién instalado y sobre el solo esta Docker con las instancias de sus imágenes corriendo lo que consume menos de 400 Mb, dejando 600 de RAM por si en un futuro queremos agregar algún otro servicio.

Lo que tenemos corriendo:
- Pi-Hole: Servidor DNS que redirige la publicidad de internet lejos de los dispositivos de nuestra LAN.
- Uptime-kuma: Es una herramienta de monitorización auto hospedada. Actualmente solo hace un ping a nuestra API cada 30 min y así ya poder tener un registro por si en algún momento tuvo una caída. Pero tiene muchas mas funciones.
- Portainer: Es un gestor de contenedores docker visual que trabaja desde el navegador web. Muy amigable.
- Home-lan API: Es una pequeña API hecha por nosotros, con python y FASTAPI que muestra unas métricas del sistema y ademas las guarda en un archivo de SQLite. 

Directorio laboratorio:

- El archivo Guia_instalacion.MD tiene una guía paso a paso para poder hacer una instalación limpia de todo el sistema y su configuración. (Dejamos fuera la instalación y configuración inicial de Diet-Pi porque ya se encuentra documentada en su pagina de forma clara). La misma configuración corre perfectamente en Debian Stable.
  
- Backup.sh es un script que realiza una copia de seguridad. En la RPI esta cargado a cron para que se ejecute una vez por semana y haga la copia de todo el USB dentro del propio USB (Si, se que no es el lugar ideal pero si vos tenes otro pen drive y querés utilizarlo para la copia solo tenes que cambiar la ruta de destino para que apunte a este ultimo), finalmente guarda las ultimas 5 copias del sistema y va eliminando las mas viejas así no se llena el espacio con archivos viejos.
  
- Env.example es el archivo de configuración de Pi-Hole, podríamos haber puesto esa configuración dentro del mismo dockerfile pero si alguien logra ingresar al servidor no debería ver contraseñas y demás, así que va separado.
  
- Docker-compose.yml es donde esta toda la configuración completa del proyecto. cuando ejecutes el build llamando a este archivo construirá todo el servidor y lo levantara.
  
- Dockerfile es un archivo de configuración para python y nuestra API. Necesario para poder levantar el backend. Cuidado de ponerlo en la carpeta api/ para que levante bien.
  
- Main.py es el corazón de nuestra API, si querés agregar funciones o ampliar este es tu archivo. Con un poco de lectura de FastAPI o algún video de internet hasta podes agregarle un pequeño CRUD.
  
- Requirements.txt va junto a los dos archivos anteriores dentro de api/ y es para que instale los módulos dentro del contenedor que te permitan levantar un servidor uvicorn y la API.
  
- Nginx.conf es un archivo muy simple, lo único que hace es configurar el contenedor Nginx para que actúe como un proxy inverso. Hacia afuera solo estará disponible el puerto 80 y apuntara al puerto 8000 del contenedor de la API donde escucha uvicorn. Así los servicios internos están protegidos y hay un solo puerto escuchando.

Nota final: Si te gusta lo que armamos acá y querés utilizarlo sos libre de hacerlo, si querés colaborar o darnos algunas ideas para ampliar este pequeño proyecto también estamos abiertos a escucharte. No es necesario que aportes código o configuraciones. Pueden ser ideas ya que aunque no lo creas a veces generan mas avances que lo técnico.

Este proyecto por ahora es de dos personas, pero nunca se sabe hasta donde puede llegar.
A la fecha de armar este repositorio sigo haciendo pruebas y preparando la documentación. 
