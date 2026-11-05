#!/usr/bin/env bash
# Prueba el CRUD completo contra cualquiera de las dos APIs (mismo contrato JSON).
#
# Uso:
#   ./scripts/probar-crud.sh http://localhost:3000        # Node + PostgreSQL
#   ./scripts/probar-crud.sh http://localhost:8000        # Python + MongoDB
#   ./scripts/probar-crud.sh http://<IP-PUBLICA-EC2>:3000 # en AWS
set -euo pipefail

BASE="${1:-http://localhost:3000}"
API="$BASE/api/productos"
ok()   { printf "\e[32m✔ %s\e[0m\n" "$1"; }
fail() { printf "\e[31m✘ %s\e[0m\n" "$1"; exit 1; }
paso() { printf "\n\e[1;34m== %s ==\e[0m\n" "$1"; }

# Extrae un campo de un JSON sin depender de jq (usa python3, presente en casi todo Linux).
campo() { python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }

paso "0. Health"
curl -fsS "$BASE/health"; echo

paso "1. CREATE  (POST $API)"
CREADO=$(curl -fsS -X POST "$API" -H "Content-Type: application/json" \
  -d '{"nombre":"Teclado mecánico","descripcion":"Switches red","precio":189900,"stock":12}')
echo "$CREADO"
ID=$(echo "$CREADO" | campo id)
ok "creado con id=$ID"

curl -fsS -X POST "$API" -H "Content-Type: application/json" \
  -d '{"nombre":"Mouse inalámbrico","precio":59900,"stock":30}' >/dev/null
ok "segundo producto creado"

paso "2. READ ALL  (GET $API)"
curl -fsS "$API"; echo

paso "3. READ ONE  (GET $API/$ID)"
curl -fsS "$API/$ID"; echo

paso "4. UPDATE  (PUT $API/$ID)"
ACTUALIZADO=$(curl -fsS -X PUT "$API/$ID" -H "Content-Type: application/json" \
  -d '{"nombre":"Teclado mecánico TKL","descripcion":"Switches brown","precio":175000,"stock":8}')
echo "$ACTUALIZADO"
[ "$(echo "$ACTUALIZADO" | campo stock)" = "8" ] && ok "stock actualizado a 8" || fail "el UPDATE no se aplicó"

paso "5. Validación (POST inválido → 400)"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API" -H "Content-Type: application/json" -d '{"precio":-5}')
[ "$CODE" = "400" ] && ok "respondió 400" || fail "se esperaba 400 y llegó $CODE"

paso "6. DELETE  (DELETE $API/$ID)"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API/$ID")
[ "$CODE" = "204" ] && ok "respondió 204" || fail "se esperaba 204 y llegó $CODE"

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API/$ID")
[ "$CODE" = "404" ] && ok "GET tras borrar → 404" || fail "se esperaba 404 y llegó $CODE"

printf "\n\e[1;32mCRUD completo OK contra %s\e[0m\n" "$BASE"
