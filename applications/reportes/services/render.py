from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_html_resumen(data: dict) -> str:
    year = data.get('year')
    month = data.get('month')
    fecha = data.get('fecha_generacion')

    rows = data.get('metricas_por_asignatura') or []
    top_reprob = data.get('asignaturas_con_mayor_reprobacion') or []
    top_doc = data.get('docentes_con_mejor_promedio') or []

    def _fmt2(value):
      try:
        return f"{float(value or 0):.2f}"
      except Exception:
        return "0.00"

    def _fmtpct(value):
      return f"{_fmt2(value)}%"

    def _tr(items):
        return ''.join(f"<td style='padding:6px;border:1px solid #ddd'>{i}</td>" for i in items)

    tabla_asig = ''.join(
      f"<tr>{_tr([r.get('periodo',''), r.get('asignatura_codigo',''), r.get('asignatura_nombre',''), r.get('total_estudiantes',0), _fmt2(r.get('promedio_general')), _fmtpct(r.get('tasa_aprobacion')), r.get('tareas_pendientes',0)])}</tr>"
      for r in rows
    )

    tabla_reprob = ''.join(
      f"<tr>{_tr([r.get('asignatura_codigo',''), r.get('asignatura_nombre',''), _fmtpct(r.get('reprobacion_pct'))])}</tr>"
      for r in top_reprob
    )

    tabla_doc = ''.join(
      f"<tr>{_tr([r.get('docente_nombre',''), _fmt2(r.get('promedio'))])}</tr>"
      for r in top_doc
    )

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <div style="max-width: 900px; margin: 0 auto; padding: 16px;">
          <h2>Consolidado Mensual del Desempeño Académico</h2>
          <p><strong>Mes:</strong> {year}-{int(month):02d} <br/>
             <strong>Fecha de generación:</strong> {fecha}</p>

          <h3>Métricas por asignatura</h3>
          <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
              <tr style="background:#f3f3f3">
                {_tr(['Periodo','Código','Asignatura','Total estudiantes','Promedio general','Tasa aprobación','Tareas pendientes'])}
              </tr>
            </thead>
            <tbody>{tabla_asig}</tbody>
          </table>

          <h3>Asignaturas con mayor reprobación</h3>
          <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
              <tr style="background:#f3f3f3">
                {_tr(['Código','Asignatura','Reprobación %'])}
              </tr>
            </thead>
            <tbody>{tabla_reprob}</tbody>
          </table>

          <h3>Docentes con mejor promedio</h3>
          <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
              <tr style="background:#f3f3f3">
                {_tr(['Docente','Promedio'])}
              </tr>
            </thead>
            <tbody>{tabla_doc}</tbody>
          </table>

          <p style="color:#666;font-size:12px;margin-top:20px">Correo automático. No responder.</p>
        </div>
      </body>
    </html>
    """.strip()


def render_excel_bytes(data: dict) -> bytes:
    output = BytesIO()

    df_asig = pd.DataFrame(data.get('metricas_por_asignatura') or [])
    df_reprob = pd.DataFrame(data.get('asignaturas_con_mayor_reprobacion') or [])
    df_doc = pd.DataFrame(data.get('docentes_con_mejor_promedio') or [])

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_asig.to_excel(writer, index=False, sheet_name='PorAsignatura')
        df_reprob.to_excel(writer, index=False, sheet_name='MayorReprobacion')
        df_doc.to_excel(writer, index=False, sheet_name='MejoresDocentes')

    return output.getvalue()


def render_pdf_bytes(data: dict) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = []
    title = f"Consolidado mensual {data.get('year')}-{int(data.get('month')):02d}"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))

    rows = data.get('metricas_por_asignatura') or []
    table_data = [[
        'Periodo', 'Código', 'Asignatura', 'Total', 'Promedio', 'Aprobación %', 'Pendientes'
    ]]

    for r in rows:
        table_data.append([
            r.get('periodo', ''),
            r.get('asignatura_codigo', ''),
            r.get('asignatura_nombre', ''),
            str(r.get('total_estudiantes', 0)),
            f"{r.get('promedio_general', 0):.2f}",
            f"{r.get('tasa_aprobacion', 0):.2f}",
            str(r.get('tareas_pendientes', 0)),
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(table)
    doc.build(elements)

    return output.getvalue()
