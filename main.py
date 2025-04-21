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
        "mensaje": "👋 ¡Bienvenidoooooooooooo a NOVA Bot! Accedé a la interfaz en /docs para probar la API."
    }

@app.post("/preguntar")
def preguntar(data: Pregunta):
    try:
        pregunta_usuario = data.pregunta.lower()

        # Archivos PDF
        pdf_files = [
            "documentos/mujeres_latinoamerica.pdf",
            "documentos/consumosnacks.pdf"
        ]

        texto_pdf = ""
        for archivo in pdf_files:
            try:
                with pdfplumber.open(archivo) as pdf:
                    for pagina in pdf.pages:
                        texto_pdf += pagina.extract_text() + "\n"
            except Exception as e:
                texto_pdf += f"\n[Error leyendo {archivo}: {e}]\n"

        # Archivos Excel
        excel_files = [
            "documentos/mujeres_latinoamerica.xlsx",
            "documentos/informe_latinoamerica.xlsx"
        ]

        texto_excel = ""
        for archivo in excel_files:
            try:
                df = pd.read_excel(archivo)
                texto_excel += df.to_string(index=False) + "\n\n"
            except Exception as e:
                texto_excel += f"\n[Error leyendo {archivo}: {e}]\n"

        # Combinar todo en contexto
        contexto = f"""
--- CONTEXTO PDF ---
{texto_pdf}

--- CONTEXTO EXCEL ---
{texto_excel}
"""

        # Prompt completo para GPT
        prompt = f"""
Eres NOVA, un asistente profesional. Usa únicamente el siguiente contexto para responder de forma clara, profesional y amigable. Si no encuentras la información, responde con sinceridad.

{contexto}

Pregunta del usuario:
{pregunta_usuario}
"""

        # Llamada a la API de OpenAI
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
