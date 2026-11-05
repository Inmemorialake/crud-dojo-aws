import pg from "pg";

// El Pool reutiliza conexiones TCP a PostgreSQL en vez de abrir una por request.
// Los valores vienen de variables de entorno (las define docker-compose.yml).
export const pool = new pg.Pool({
  host: process.env.DB_HOST ?? "localhost",
  port: Number(process.env.DB_PORT ?? 5432),
  user: process.env.DB_USER ?? "dojo",
  password: process.env.DB_PASSWORD ?? "dojo",
  database: process.env.DB_NAME ?? "productos_db",
  max: 10,
});

// Crea la tabla si no existe. Así la API no depende de un script SQL externo.
export async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS productos (
      id          SERIAL PRIMARY KEY,
      nombre      VARCHAR(120)   NOT NULL,
      descripcion TEXT           NOT NULL DEFAULT '',
      precio      NUMERIC(12, 2) NOT NULL CHECK (precio >= 0),
      stock       INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0),
      creado_en   TIMESTAMPTZ    NOT NULL DEFAULT NOW()
    )
  `);
}

// Reintenta la conexión: aunque compose espera el healthcheck de Postgres,
// esto hace la API robusta si la BD tarda o se reinicia.
export async function waitForDb(retries = 15, delayMs = 2000) {
  for (let i = 1; i <= retries; i++) {
    try {
      await pool.query("SELECT 1");
      return;
    } catch (err) {
      console.log(`[db] intento ${i}/${retries} fallido: ${err.message}`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("No fue posible conectar a PostgreSQL");
}
