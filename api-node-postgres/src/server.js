import express from "express";
import { initDb, pool, waitForDb } from "./db.js";
import { router as productosRouter } from "./productos.routes.js";

const app = express();
const PORT = Number(process.env.PORT ?? 3000);

app.use(express.json());

app.get("/", (_req, res) =>
  res.json({ api: "productos", stack: "Node.js (Express) + PostgreSQL", docs: "/api/productos" })
);

// Healthcheck: confirma que la API está viva Y que alcanza la BD.
app.get("/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", db: "up" });
  } catch {
    res.status(503).json({ status: "degraded", db: "down" });
  }
});

app.use("/api/productos", productosRouter);

app.use((_req, res) => res.status(404).json({ error: "Ruta no encontrada" }));

// Express 5 propaga automáticamente los errores de handlers async hasta aquí.
app.use((err, _req, res, _next) => {
  if (err.type === "entity.parse.failed") return res.status(400).json({ error: "JSON mal formado" });
  console.error(err);
  res.status(500).json({ error: "Error interno del servidor" });
});

await waitForDb();
await initDb();

const server = app.listen(PORT, "0.0.0.0", () =>
  console.log(`[api] escuchando en http://0.0.0.0:${PORT}`)
);

// Cierre ordenado: `docker stop` envía SIGTERM.
for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, () => {
    console.log(`[api] ${signal} recibido, cerrando...`);
    server.close(() => pool.end().then(() => process.exit(0)));
  });
}
