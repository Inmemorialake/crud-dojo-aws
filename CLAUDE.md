# Contexto para Claude Code

Taller universitario: la misma API REST CRUD de productos en dos stacks, desplegada con Docker en local y en AWS EC2.

- `api-node-postgres/`: Node.js 22 + Express 5 + PostgreSQL 17, puerto 3000.
- `api-python-mongo/`: Python 3.13 + FastAPI + MongoDB 8, puerto 8000.
- Ambas comparten el mismo contrato JSON. `scripts/probar-crud.sh <URL_BASE>` prueba el CRUD completo contra cualquiera.
- La guía completa está en `README.md` y el guion del video en `docs/GUION_VIDEO.md`.

## Reglas

- Commits en español con Conventional Commits (`feat:`, `build:`, `docs:`, `fix:`...).
- Nunca imprimir, commitear ni copiar a la EC2 credenciales de AWS. Los archivos `.env` y `*.pem` no van al repo.
- Las bases de datos no se exponen: el Security Group solo abre 22 (IP del usuario), 3000 y 8000.
- Antes de crear o terminar recursos en AWS, mostrar el comando y pedir confirmación.

## Despliegue en EC2 con AWS CLI (región por defecto: us-east-1)

1. Key pair `dojo-key`; guardar el `.pem` fuera del repo con `chmod 400`.
2. Security group `dojo-crud-sg` con las reglas anteriores (IP del usuario: `curl -s https://checkip.amazonaws.com`).
3. Instancia `t3.micro`, Ubuntu 24.04 LTS (AMI vía el parámetro SSM `/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id`), 20 GiB gp3, tag `Name=dojo-crud`.
4. Por SSH (`ubuntu@<IP>`): clonar el repo, `sudo ./scripts/ec2-setup.sh`, reconectar, crear los `.env` con claves aleatorias y `docker compose up -d --build` en ambas carpetas.
5. Verificar desde local con `scripts/probar-crud.sh http://<IP>:3000` y `:8000`.
6. Al terminar el taller: terminar la instancia y borrar el security group y el key pair.
