from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.pipeline import correct_text, review_text
from app.db.database import engine, Base
from app.routes.auth import router as auth_router

# Crear tablas al iniciar
Base.metadata.create_all(bind=engine)

class TextoEntrada(BaseModel):
    texto: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de autenticación
app.include_router(auth_router)

@app.post("/corregir")
def corregir(datos: TextoEntrada):
    return correct_text(datos.texto)

@app.post("/revisar")
def revisar(datos: TextoEntrada):
    return review_text(datos.texto)