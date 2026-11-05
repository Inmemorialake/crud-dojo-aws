# ---- Etapa 1: dependencias ----
# Se copian primero solo los manifiestos para aprovechar la caché de capas:
# si no cambian, `npm ci` no se vuelve a ejecutar en cada build.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# ---- Etapa 2: imagen final ----
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src

# No ejecutar como root dentro del contenedor (el usuario `node` ya viene en la imagen).
USER node

EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1

CMD ["node", "src/server.js"]
