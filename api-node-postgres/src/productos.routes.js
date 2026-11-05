import { Router } from "express";
import { pool } from "./db.js";

export const router = Router();

const COLUMNAS = "id, nombre, descripcion, precio::float AS precio, stock, creado_en";

// Valida el body completo (POST y PUT usan el mismo esquema: PUT reemplaza el recurso).
function validar(body) {
  const errores = [];
  const { nombre, descripcion = "", precio, stock = 0 } = body ?? {};

  if (typeof nombre !== "string" || nombre.trim().length === 0 || nombre.length > 120)
    errores.push("nombre: obligatorio, texto de 1 a 120 caracteres");
  if (typeof descripcion !== "string")
    errores.push("descripcion: debe ser texto");
  if (typeof precio !== "number" || !Number.isFinite(precio) || precio < 0)
    errores.push("precio: obligatorio, número >= 0");
  if (!Number.isInteger(stock) || stock < 0)
    errores.push("stock: entero >= 0");

  return { errores, datos: { nombre: nombre?.trim(), descripcion, precio, stock } };
}

function parseId(raw) {
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}

// READ (todos)
router.get("/", async (_req, res) => {
  const { rows } = await pool.query(`SELECT ${COLUMNAS} FROM productos ORDER BY id`);
  res.json(rows);
});

// READ (uno)
router.get("/:id", async (req, res) => {
  const id = parseId(req.params.id);
  if (!id) return res.status(400).json({ error: "id inválido" });

  const { rows } = await pool.query(`SELECT ${COLUMNAS} FROM productos WHERE id = $1`, [id]);
  if (rows.length === 0) return res.status(404).json({ error: "Producto no encontrado" });
  res.json(rows[0]);
});

// CREATE
router.post("/", async (req, res) => {
  const { errores, datos } = validar(req.body);
  if (errores.length) return res.status(400).json({ errores });

  // Consultas parametrizadas ($1, $2...) → evitan SQL injection.
  const { rows } = await pool.query(
    `INSERT INTO productos (nombre, descripcion, precio, stock)
     VALUES ($1, $2, $3, $4) RETURNING ${COLUMNAS}`,
    [datos.nombre, datos.descripcion, datos.precio, datos.stock]
  );
  res.status(201).location(`/api/productos/${rows[0].id}`).json(rows[0]);
});

// UPDATE (reemplazo completo)
router.put("/:id", async (req, res) => {
  const id = parseId(req.params.id);
  if (!id) return res.status(400).json({ error: "id inválido" });

  const { errores, datos } = validar(req.body);
  if (errores.length) return res.status(400).json({ errores });

  const { rows } = await pool.query(
    `UPDATE productos SET nombre = $1, descripcion = $2, precio = $3, stock = $4
     WHERE id = $5 RETURNING ${COLUMNAS}`,
    [datos.nombre, datos.descripcion, datos.precio, datos.stock, id]
  );
  if (rows.length === 0) return res.status(404).json({ error: "Producto no encontrado" });
  res.json(rows[0]);
});

// DELETE
router.delete("/:id", async (req, res) => {
  const id = parseId(req.params.id);
  if (!id) return res.status(400).json({ error: "id inválido" });

  const { rowCount } = await pool.query("DELETE FROM productos WHERE id = $1", [id]);
  if (rowCount === 0) return res.status(404).json({ error: "Producto no encontrado" });
  res.status(204).end();
});
