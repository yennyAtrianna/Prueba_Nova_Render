from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
import pandas as pd
import os

# Cargar claves desde el archivo .env
load_dotenv()

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializar FastAPI
app = FastAPI()

# Modelo de entrada
class Pregunta(BaseModel):
    pregunta: str

@app.get("/")
def bienvenida():
    return {
        "mensaje": "👋 ¡Bienvenido a NOVA Bot! Accedé a la interfaz en /docs para probar la API."
    }

@app.post("/preguntar")
def preguntar(data: Pregunta):
    try:
        pregunta_usuario = data.pregunta.lower()

        # ---------- Lectura de archivos ----------
        contexto = ""

        # Leer archivos PDF con etiquetas
        pdf_archivos = {
            "Mujeres latinoamericanas": "documentos/mujeres_latinoamerica.pdf",
            "Consumo de snacks": "documentos/snacks_latinoamerica_resumen.pdf"
        }

        for titulo, archivo in pdf_archivos.items():
            try:
                with pdfplumber.open(archivo) as pdf:
                    texto = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
                    contexto += f"\n### PDF: {titulo}\n{texto}\n"
                    print(f"✅ PDF leído correctamente: {archivo}")
            except Exception as e:
                contexto += f"\n[Error leyendo {archivo}: {e}]\n"
                print(f"❌ Error leyendo PDF: {archivo} → {e}")

        # Leer archivos Excel con etiquetas
        excel_archivos = {
            "Tabla mujeres latinoamericanas": "documentos/mujeres_latinoamerica.xlsx",
            "Informe de consumo": "documentos/informe_latinoamerica.xlsx"
        }

        for titulo, archivo in excel_archivos.items():
            try:
                df = pd.read_excel(archivo)
                contexto += f"\n### EXCEL: {titulo}\n{df.to_string(index=False)}\n"
                print(f"✅ Excel leído correctamente: {archivo}")
            except Exception as e:
                contexto += f"\n[Error leyendo {archivo}: {e}]\n"
                print(f"❌ Error leyendo Excel: {archivo} → {e}")

        # 🔍 Mostrar una vista previa del contexto
        print("📝 CONTEXTO FINAL ENVIADO A GPT:")
        print(contexto[:1000])

        # ---------- Prompt para GPT ----------
        prompt = f"""
Eres NOVA, un asistente profesional. Usa solo el contexto para responder con claridad, amabilidad y precisión.
Primero detecta de qué trata la pregunta (persona, consumo, cifras, etc.) y luego responde usando el bloque más relevante.
Si no encuentras la información, di que no está en el contexto.

--- CONTEXTO ---
{contexto[:6000]}

--- PREGUNTA ---
{pregunta_usuario}
"""

        # Llamada a GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres NOVA, un asistente profesional que responde solo con el contexto proporcionado."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"respuesta": response.choices[0].message.content}

    except Exception as general_error:
        return {"error": f"Error general: {general_error}"}
