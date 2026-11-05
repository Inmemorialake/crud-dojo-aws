"""Genera la hoja de entrega (PDF de una página) con datos, repositorio y video.

Uso:
    pip install reportlab
    python entrega/generar_hoja.py \
        --repo  https://github.com/<usuario>/crud-dojo-aws \
        --video https://youtu.be/<id> \
        --curso "Infraestructuras Paralelas y Distribuidas (750023C)" \
        --docente "Manuel Alejandro Pastrana, PhD"
"""
import argparse
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

p = argparse.ArgumentParser()
p.add_argument("--repo", default="(pendiente)")
p.add_argument("--video", default="(pendiente)")
p.add_argument("--curso", default="Infraestructuras Paralelas y Distribuidas (750023C)")
p.add_argument("--docente", default="Manuel Alejandro Pastrana, PhD")
p.add_argument("--nombre", default="Andrés Gerardo González Rosero")
p.add_argument("--codigo", default="202416541")
p.add_argument("--correo", default="andresgerardogonzales@gmail.com")
p.add_argument("--programa", default="Ingeniería de Sistemas")
p.add_argument("--salida", default="entrega/Entrega_Dojo_AWS_GonzalezRosero.pdf")
a = p.parse_args()

hoy = date.today()
fecha = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"

AZUL = colors.HexColor("#1F3A5F")
GRIS = colors.HexColor("#5A6472")
LINEA = colors.HexColor("#C9D1DC")

ss = getSampleStyleSheet()
st = {
    "inst": ParagraphStyle("inst", parent=ss["Normal"], fontName="Helvetica-Bold",
                           fontSize=11, textColor=GRIS, alignment=1, leading=14),
    "titulo": ParagraphStyle("titulo", parent=ss["Title"], fontName="Helvetica-Bold",
                             fontSize=20, textColor=AZUL, leading=24, spaceAfter=4),
    "sub": ParagraphStyle("sub", parent=ss["Normal"], fontSize=11.5, textColor=GRIS,
                          alignment=1, leading=15),
    "h": ParagraphStyle("h", parent=ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=12.5, textColor=AZUL, spaceBefore=6, spaceAfter=6),
    "k": ParagraphStyle("k", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=10.5,
                        textColor=GRIS, leading=14),
    "v": ParagraphStyle("v", parent=ss["Normal"], fontSize=10.5, leading=14),
    "body": ParagraphStyle("body", parent=ss["Normal"], fontSize=10.5, leading=15),
}


def link(url: str) -> str:
    if url.startswith("http"):
        return f'<link href="{url}" color="#1F5FBF"><u>{url}</u></link>'
    if url == "(pendiente)":
        return f'<font color="#B00020">{url}</font>'
    return url


def tabla(filas):
    t = Table([[Paragraph(k, st["k"]), Paragraph(v, st["v"])] for k, v in filas],
              colWidths=[4.2 * cm, 12.3 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


doc = SimpleDocTemplate(a.salida, pagesize=letter, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                        topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                        title="Entrega — Dojo AWS: API REST CRUD en contenedores",
                        author=a.nombre)

story = [
    Paragraph("UNIVERSIDAD DEL VALLE<br/>Escuela de Ingeniería de Sistemas y Computación", st["inst"]),
    Spacer(1, 0.7 * cm),
    Paragraph("Dojo AWS: API REST CRUD en contenedores", st["titulo"]),
    Paragraph("Despliegue local con Docker y en AWS EC2 — dos implementaciones", st["sub"]),
    Spacer(1, 0.8 * cm),

    Paragraph("Datos del estudiante", st["h"]),
    tabla([
        ("Nombre", a.nombre),
        ("Código", a.codigo),
        ("Programa", a.programa),
        ("Correo", a.correo),
        ("Curso", a.curso),
        ("Docente", a.docente),
        ("Fecha", fecha),
    ]),
    Spacer(1, 0.6 * cm),

    Paragraph("Enlaces de la entrega", st["h"]),
    tabla([
        ("Repositorio", link(a.repo)),
        ("Video (YouTube)", link(a.video)),
    ]),
    Spacer(1, 0.6 * cm),

    Paragraph("Resumen", st["h"]),
    Paragraph(
        "Se implementó la misma API REST de productos (CRUD completo) en dos stacks: "
        "<b>Node.js 22 + Express 5 con PostgreSQL 17</b> y <b>Python 3.13 + FastAPI con MongoDB 8</b>. "
        "Cada implementación se empaqueta con Dockerfile y se orquesta con Docker Compose "
        "(API + base de datos con volumen persistente y healthcheck). Ambas se desplegaron "
        "localmente en contenedores y en una instancia AWS EC2 (Ubuntu 24.04), exponiendo solo "
        "los puertos de las APIs (3000 y 8000) mediante el Security Group. El video documenta el "
        "paso a paso y una reflexión sobre facilidades, dificultades y aprendizajes del despliegue.",
        st["body"]),
]

doc.build(story)
print(f"PDF generado: {a.salida}")
