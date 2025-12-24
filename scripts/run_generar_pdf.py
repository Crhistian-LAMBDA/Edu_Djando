import os
import sys

base = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, base)

from scripts.generar_pdf_guia import build_pdf

out = os.path.join(base, 'docs', 'Guia_Proyecto_EduPro360.pdf')
os.makedirs(os.path.dirname(out), exist_ok=True)
build_pdf(out)
print(f"PDF generado en: {out}")
