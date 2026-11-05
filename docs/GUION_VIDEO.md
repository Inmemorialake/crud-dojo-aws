# Guion del video (≈ 15–18 min)

Objetivo: mostrar el paso a paso **real** (sin cortes en los comandos importantes) y cerrar con una reflexión clara sobre facilidades, dificultades y aprendizajes.

**Antes de grabar**
- Instancia EC2 creada pero *sin* nada instalado (para mostrar la instalación en vivo), o graba la creación también.
- Terminal con fuente grande (≥ 16 pt) y tema de alto contraste; oculta tokens, claves y el `.pem`.
- Ten abiertas: el repo en el editor, la consola de AWS y dos terminales (local y SSH).
- Antes de grabar, ejecuta `docker compose down -v` en local para empezar desde cero.

---

## 0. Introducción (≈ 1 min)

- Quién eres, curso y objetivo de la actividad.
- Qué se va a construir: la misma API REST de productos en **dos stacks** (Node + PostgreSQL / Python + MongoDB), en contenedores, primero local y luego en EC2.
- Muestra el diagrama mental: *cliente → puerto expuesto → contenedor API → red interna de Docker → contenedor BD (volumen)*.

## 1. Recorrido por el código (≈ 3 min)

**Node + PostgreSQL** (`api-node-postgres/`)
- `db.js`: Pool de conexiones, variables de entorno, `CREATE TABLE IF NOT EXISTS`, reintentos de conexión.
- `productos.routes.js`: las 5 rutas del CRUD; consultas parametrizadas (`$1`) → evitan SQL injection; códigos HTTP (201, 204, 404, 400).

**Python + MongoDB** (`api-python-mongo/`)
- `models.py`: validación declarativa con Pydantic.
- `main.py`: mismas 5 rutas; `_id`/`ObjectId` → `id` string; manejadores de error para mantener el mismo contrato que la API de Node.

Remata con: *"Mismo contrato JSON, dos implementaciones distintas: por eso un solo script de pruebas sirve para ambas."*

## 2. Contenedores (≈ 2 min)

- **Dockerfile de Node**: multi-stage, copiar `package.json` antes que el código (caché de capas), `USER node`, `HEALTHCHECK`.
- **Dockerfile de Python**: `requirements.txt` primero, usuario sin privilegios.
- **docker-compose.yml**: servicio de BD con `healthcheck`, `depends_on: condition: service_healthy`, volumen nombrado, y por qué la BD **no** tiene `ports`.

## 3. Despliegue local (≈ 3 min)

```bash
cd api-node-postgres && docker compose up -d --build
docker compose ps                       # mostrar "healthy"
../scripts/probar-crud.sh http://localhost:3000
docker compose exec db psql -U dojo -d productos_db -c "SELECT * FROM productos;"
```

```bash
cd ../api-python-mongo && docker compose up -d --build
../scripts/probar-crud.sh http://localhost:8000
```
- Abre `http://localhost:8000/docs` y haz un POST desde Swagger UI.
- **Demostración de persistencia:** `docker compose down` → `up -d` → los datos siguen ahí. Luego explica qué hace `down -v`.
- Deja claro que **no** se está ejecutando desde el IDE: todo corre en contenedores (`docker ps`).

## 4. Despliegue en AWS EC2 (≈ 5 min)

1. Consola EC2 → *Launch instance*: AMI Ubuntu 24.04, `t3.micro`, key pair, almacenamiento.
2. **Security group**: 22 (solo tu IP), 3000 y 8000 abiertos; explica por qué 5432 y 27017 no.
3. SSH: `chmod 400 dojo-key.pem` y `ssh -i dojo-key.pem ubuntu@<IP>`.
4. `git clone ...` → `sudo ./scripts/ec2-setup.sh` → salir y volver a entrar.
5. `cp .env.example .env` (credenciales reales) → `docker compose up -d --build` en ambas carpetas → `docker ps`.
6. **Prueba desde tu PC** contra la IP pública: `./scripts/probar-crud.sh http://<IP>:3000` y `:8000`.
7. Navegador: `http://<IP>:8000/docs`.
8. Opcional (suma puntos): `sudo reboot`, esperar, y mostrar que los contenedores volvieron solos por `restart: unless-stopped`.

## 5. Reflexión (≈ 3 min) — en tus propias palabras

Estructura sugerida: **Facilidades → Dificultades → Aprendizajes → Conclusión**. Usa ejemplos concretos de lo que te pasó; abajo hay puntos de partida, quédate con los que de verdad viviste.

**Facilidades**
- Compose reduce el despliegue a un comando y lo hace *idéntico* en local y en EC2: lo que funcionó en el PC funcionó en la nube sin cambiar código.
- Las imágenes oficiales (`postgres`, `mongo`) evitan instalar y configurar motores de BD a mano.
- Variables de entorno: la misma imagen sirve para cualquier entorno cambiando solo el `.env`.
- FastAPI genera Swagger gratis; Express es mínimo y fácil de leer.

**Dificultades** (ejemplos típicos; cuenta los tuyos)
- Orden de arranque: la API intentaba conectarse antes de que la BD estuviera lista → `healthcheck` + `depends_on` + reintentos.
- Security Group: la API corría pero no respondía desde fuera hasta abrir el puerto.
- Recursos de la `t3.micro` (1 GB RAM): builds lentos o contenedores muertos sin swap.
- Permisos: llave `.pem`, grupo `docker`, usuario no-root en el contenedor.
- Diferencias entre motores: esquema fijo vs. sin esquema, `SERIAL` vs. `ObjectId`.

**Aprendizajes**
- Diferencia entre *imagen*, *contenedor*, *volumen* y *red*.
- Por qué no exponer la base de datos a internet (superficie de ataque mínima).
- SQL vs. NoSQL en la práctica: dónde vive la validación y cómo cambia el modelo de datos.
- Infraestructura reproducible: el repositorio + dos comandos reconstruyen todo el sistema desde cero.
- Costos: apagar/terminar recursos al finalizar.

**Conclusión (1 frase):** p. ej., *"Los contenedores desacoplan la aplicación de la máquina: el mismo artefacto corre igual en mi portátil y en AWS, y lo que cambia es solo la infraestructura alrededor."*

## 6. Cierre (≈ 30 s)

- Enlace al repositorio.
- Terminar la instancia EC2 en cámara (opcional) para mostrar la gestión de costos.

---

### Checklist antes de subir a YouTube
- [ ] Se ve el CRUD completo en **ambas** implementaciones, local y en EC2.
- [ ] Se nota que todo corre en contenedores (`docker ps`), no desde el IDE.
- [ ] No aparecen claves, el contenido del `.pem` ni el ID de cuenta de AWS.
- [ ] Audio claro; sin silencios largos durante los builds (acelera esos tramos al editar).
- [ ] Visibilidad **No listado** o **Público** (no "Privado"), para que el profesor pueda verlo.
- [ ] Enlace del repo en la descripción del video.
