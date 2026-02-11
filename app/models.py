from sqlalchemy import Column, Integer, String, LargeBinary
from app.database import Base


class User(Base):
    __tablename__ = 'Usuarios'  

    idUsuarios = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    email = Column(String(150), unique=True)
    fotoPerfil = Column(String(255), nullable=True)
