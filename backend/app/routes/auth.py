from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
import bcrypt

from app.db.database import get_db
from app.db.models import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "ortograf-ia-secret-key-2024"
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30



class RegisterData(BaseModel):
    nombre: str
    email: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

class ResetData(BaseModel):
    email: str
    nueva_password: str



def hashear(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verificar(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())

def crear_token(usuario_id: int) -> str:
    expira = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(usuario_id), "exp": expira},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def respuesta_sesion(usuario: Usuario) -> dict:
    return {
        "token": crear_token(usuario.id),
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email
        }
    }


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/register")
def register(datos: RegisterData, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese correo.")

    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hashear(datos.password)
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return respuesta_sesion(usuario)


@router.post("/login")
def login(datos: LoginData, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verificar(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    return respuesta_sesion(usuario)


@router.post("/reset-password")
def reset_password(datos: ResetData, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo.")

    usuario.password_hash = hashear(datos.nueva_password)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente."}