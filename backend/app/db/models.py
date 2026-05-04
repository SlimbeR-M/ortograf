from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    chats = relationship("Chat", back_populates="usuario", cascade="all, delete")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, default="Nuevo chat")
    creado_en = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="chats")
    mensajes = relationship("Mensaje", back_populates="chat", cascade="all, delete")


class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    rol = Column(String, nullable=False)  # "usuario" o "ia"
    contenido = Column(Text, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    chat = relationship("Chat", back_populates="mensajes")