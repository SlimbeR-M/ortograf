from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.database import get_db
from app.db.models import Chat, Mensaje, Usuario

router = APIRouter(prefix="/chats", tags=["chats"])
bearer = HTTPBearer()

SECRET_KEY = "ortograf-ia-secret-key-2024"
ALGORITHM = "HS256"


# ─── Obtener usuario del token ────────────────────────────────────────────────

def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
) -> Usuario:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = int(payload["sub"])
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Token inválido.")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    return usuario


# ─── Schemas ─────────────────────────────────────────────────────────────────

class MensajeData(BaseModel):
    rol: str
    contenido: str

class GuardarChatData(BaseModel):
    titulo: str
    mensajes: list[MensajeData]


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/")
def listar_chats(usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.usuario_id == usuario.id).order_by(Chat.creado_en.desc()).all()
    return [{"id": c.id, "titulo": c.titulo, "creado_en": c.creado_en} for c in chats]


@router.post("/")
def crear_chat(datos: GuardarChatData, usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    chat = Chat(titulo=datos.titulo, usuario_id=usuario.id)
    db.add(chat)
    db.flush()

    for msg in datos.mensajes:
        db.add(Mensaje(rol=msg.rol, contenido=msg.contenido, chat_id=chat.id))

    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "titulo": chat.titulo}


@router.get("/{chat_id}")
def obtener_chat(chat_id: int, usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.usuario_id == usuario.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado.")

    return {
        "id": chat.id,
        "titulo": chat.titulo,
        "mensajes": [{"rol": m.rol, "contenido": m.contenido} for m in chat.mensajes]
    }


@router.delete("/{chat_id}")
def eliminar_chat(chat_id: int, usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.usuario_id == usuario.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado.")
    db.delete(chat)
    db.commit()
    return {"ok": True}