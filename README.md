# CRUD Dojo AWS — API REST en contenedores, local y en EC2

Misma API REST de **productos** (CRUD completo) implementada dos veces, con lenguaje y base de datos distintos, desplegada con Docker **localmente** y en **AWS EC2**.

| Carpeta | Lenguaje / Framework | Base de datos | Puerto |
|---|---|---|---|
| [`api-node-postgres/`](api-node-postgres) | JavaScript — Node.js 22 + Express 5 | PostgreSQL 17 (relacional, SQL) | `3000` |
| [`api-python-mongo/`](api-python-mongo) | Python 3.13 — FastAPI | MongoDB 8 (documental, NoSQL) | `8000` |

Ambas exponen **exactamente el mismo contrato JSON**, así que el mismo script de pruebas (`scripts/probar-crud.sh`) sirve para las dos.

```
crud-dojo-aws/
├── api-node-postgres/      # Implementación 1
│   ├── src/                # server.js, db.js, productos.routes.js
│   ├── Dockerfile          # multi-stage, usuario no-root, HEALTHCHECK
│   └── docker-compose.yml  # api + postgres (volumen persistente)
├── api-python-mongo/       # Implementación 2
│   ├── app/                # main.py, models.py, db.py
│   ├── tests/              # pytest + mongomock
│   ├── Dockerfile
│   └── docker-compose.yml  # api + mongo (volumen persistente)
├── scripts/
│   ├── probar-crud.sh      # prueba el CRUD completo contra cualquier URL
│   └── ec2-setup.sh        # instala Docker + Compose + swap en la EC2
└── docs/GUION_VIDEO.md     # guion del video y puntos para la reflexión
```

---

## 🎥 Video

**Enlace del video (YouTube):** _pendiente — se publicará aquí._

El video documenta el despliegue local y en AWS EC2 de ambas implementaciones, y cierra con una reflexión sobre facilidades, dificultades y aprendizajes del proceso.

---

## Contrato de la API

Recurso: `producto` → `{ id, nombre, descripcion, precio, stock, creado_en }`

| Método | Ruta | Acción | Respuesta OK |
|---|---|---|---|
| `GET` | `/health` | Estado de la API y de la BD | `200` |
| `GET` | `/api/productos` | Listar todos | `200` |
| `GET` | `/api/productos/{id}` | Obtener uno | `200` / `404` |
| `POST` | `/api/productos` | Crear | `201` + header `Location` |
| `PUT` | `/api/productos/{id}` | Reemplazar | `200` / `404` |
| `DELETE` | `/api/productos/{id}` | Eliminar | `204` / `404` |

Body de `POST`/`PUT`:

```json
{ "nombre": "Teclado mecánico", "descripcion": "Switches red", "precio": 189900, "stock": 12 }
```

Errores: validación → `400 {"errores": [...]}`; id mal formado → `400`; no existe → `404 {"error": "..."}`.

La API de Python además genera documentación interactiva (Swagger UI) en **`/docs`**.

---

## Parte 1 — Despliegue local con contenedores

Requisito: Docker Engine con el plugin Compose (`docker compose version`).

### Implementación 1: Node.js + PostgreSQL

```bash
cd api-node-postgres
cp .env.example .env              # opcional: cambia credenciales
docker compose up -d --build      # construye la imagen y levanta api + db
docker compose ps                 # ambos servicios deben quedar "healthy"
docker compose logs -f api        # ver logs (Ctrl+C para salir)
../scripts/probar-crud.sh http://localhost:3000
```

### Implementación 2: Python + MongoDB

```bash
cd api-python-mongo
cp .env.example .env
docker compose up -d --build
docker compose ps
../scripts/probar-crud.sh http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Comprobar que los datos están en la base de datos

```bash
# PostgreSQL
docker compose -f api-node-postgres/docker-compose.yml exec db \
  psql -U dojo -d productos_db -c "SELECT * FROM productos;"

# MongoDB
docker compose -f api-python-mongo/docker-compose.yml exec mongo \
  mongosh -u dojo -p dojo --authenticationDatabase admin productos_db --eval "db.productos.find()"
```

### Apagar

```bash
docker compose down        # detiene y borra contenedores; los datos quedan en el volumen
docker compose down -v     # además borra el volumen (datos)
```

> **Por qué la BD no tiene `ports`:** los contenedores de un mismo `docker-compose.yml` comparten una red interna donde cada servicio se resuelve por su nombre (`db`, `mongo`). La API se conecta por esa red, así que la base de datos no necesita estar expuesta al host ni a internet.

---

## Parte 2 — Despliegue en AWS EC2 con contenedores

### 1. Crear la instancia (Consola de AWS → EC2 → *Launch instance*)

| Campo | Valor |
|---|---|
| Name | `dojo-crud` |
| AMI | **Ubuntu Server 24.04 LTS** (x86_64) |
| Instance type | `t3.micro` (o `t2.micro`), elegible para la capa gratuita |
| Key pair | Crear uno nuevo → tipo RSA, formato `.pem` → se descarga `dojo-key.pem` |
| Storage | 15–20 GiB gp3 (las imágenes de Docker ocupan espacio) |

**Security group** (*Network settings → Edit*), reglas de entrada:

| Tipo | Puerto | Origen | Para qué |
|---|---|---|---|
| SSH | 22 | **My IP** | Administrar la instancia |
| Custom TCP | 3000 | `0.0.0.0/0` | API Node + PostgreSQL |
| Custom TCP | 8000 | `0.0.0.0/0` | API Python + MongoDB |

> Los puertos 5432 (Postgres) y 27017 (Mongo) **no** se abren: la BD solo vive en la red interna de Docker.

### 2. Conectarse por SSH

```bash
chmod 400 dojo-key.pem                       # SSH rechaza llaves con permisos abiertos
ssh -i dojo-key.pem ubuntu@<IP_PUBLICA>      # en Amazon Linux el usuario es ec2-user
```

### 3. Instalar Docker y clonar el repositorio

```bash
git clone https://github.com/Inmemorialake/crud-dojo-aws.git
cd crud-dojo-aws
sudo ./scripts/ec2-setup.sh       # Docker Engine + Compose + 2 GB de swap
exit                              # salir y volver a entrar para usar docker sin sudo
ssh -i dojo-key.pem ubuntu@<IP_PUBLICA>
cd crud-dojo-aws
```

### 4. Levantar las dos implementaciones

```bash
cd api-node-postgres && cp .env.example .env && nano .env   # pon una clave real
docker compose up -d --build && cd ..

cd api-python-mongo && cp .env.example .env && nano .env
docker compose up -d --build && cd ..

docker ps     # 4 contenedores: 2 APIs + 2 bases de datos
```

### 5. Probar desde tu PC (fuera de AWS)

```bash
./scripts/probar-crud.sh http://<IP_PUBLICA>:3000
./scripts/probar-crud.sh http://<IP_PUBLICA>:8000
```

En el navegador: `http://<IP_PUBLICA>:8000/docs` y `http://<IP_PUBLICA>:3000/api/productos`.

Gracias a `restart: unless-stopped`, si la instancia se reinicia los contenedores vuelven a arrancar solos.

### 6. Al terminar: evitar costos

EC2 → Instances → seleccionar → **Instance state → Terminate**. Revisa también que no queden volúmenes EBS ni Elastic IPs sueltas.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `curl` a la IP pública se queda colgado | Puerto no abierto en el Security Group | Agregar la regla de entrada 3000/8000 |
| `permission denied ... docker.sock` | El grupo `docker` aún no aplica | Cerrar y volver a abrir la sesión SSH |
| El build se congela o un contenedor muere (`Exited (137)`) | Sin memoria (1 GB de RAM) | Verificar swap con `free -h`; el script la crea |
| La IP pública cambió | Se detuvo y arrancó la instancia | Usar la nueva IP o asignar una Elastic IP |
| `api` reinicia en bucle | La BD aún no está lista o credenciales distintas | `docker compose logs api`; revisar `.env` |

---

## Diferencias entre las dos implementaciones

| Aspecto | Node.js + PostgreSQL | Python + MongoDB |
|---|---|---|
| Modelo de datos | Tabla con esquema fijo (`CREATE TABLE`) | Colección sin esquema; se crea al primer insert |
| Identificador | `SERIAL` (entero autoincremental) | `ObjectId` (24 caracteres hex) |
| Validación | Manual en `validar()` + `CHECK` en la BD | Declarativa con Pydantic (`Field(ge=0)`) |
| Consultas | SQL parametrizado (`$1, $2`) | Documentos/filtros (`{"_id": ...}`) |
| Documentación | — | Swagger UI automático en `/docs` |
| Imagen base | `node:22-alpine` (multi-stage) | `python:3.13-slim` |
| Healthcheck de la BD | `pg_isready` | `mongosh ... ping` |

## Tests sin Docker (Python)

```bash
cd api-python-mongo
pip install -r requirements.txt pytest httpx mongomock
pytest -q
```

---

## Integrantes

| Nombre | Código | GitHub |
|---|---|---|
| Andrés Gerardo González Rosero | 202416541 | [@Inmemorialake](https://github.com/Inmemorialake) |
| Freddy Alexander Melo Buitrago | 202125498 | [@FoxArtMotion](https://github.com/FoxArtMotion) |
| Sarahy Gisselle Caicedo Betancourth | 2610315 | — |

Ingeniería de Sistemas — Universidad del Valle
