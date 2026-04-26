from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.ai_service import corregir_texto

class TextoEntrada(BaseModel):
    texto: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/corregir")
def corregir(datos: TextoEntrada):
    errores, texto_corregido = corregir_texto(datos.texto)
    return {"errores": errores, "texto_corregido": texto_corregido}