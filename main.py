
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
import pdfplumber
import pandas as pd

# Cargar las variables del archivo .env
load_dotenv()

# Crear cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class Pregunta(BaseModel):
    pregunta: str

@app.post("/preguntar")
def preguntar(data: Pregunta):
    try:
        pregunta_usuario = data.pregunta.lower()

        # Leer el PDF
        texto_pdf = ""
        try:
            with pdfplumber.open("documentos/mujeres_latinoamerica.pdf") as pdf:
                for pagina in pdf.pages:
                    texto_pdf += pagina.extract_text() + "\n"
        except Exception as e:
            return {"error": f"Error leyendo el PDF: {e}"}

        # Leer el Excel
        texto_excel = ""
        try:
            df = pd.read_excel("documentos/mujeres_latinoamerica.xlsx")
            texto_excel = df.to_string(index=False)
        except Exception as e:
            return {"error": f"Error leyendo el Excel: {e}"}

        # Combinar textos como contexto
        contexto = f"""
        --- Información del PDF ---
        {texto_pdf}

        --- Tabla del Excel ---
        {texto_excel}
        """

        # Prompt para GPT
        prompt = f"""
Eres NOVA, un asistente profesional. Usa únicamente el siguiente contexto para responder:

{contexto}

Pregunta:
{pregunta_usuario}
"""

        # Llamada a GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente profesional que solo responde con base en el contexto dado."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"respuesta": response.choices[0].message.content}

    except Exception as general_error:
        return {"error": f"Error general: {general_error}"}
