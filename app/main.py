from fastapi import FastAPI, HTTPException, Form, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.models import User
from app.utils import image_to_embedding, upload_image_to_cloudinary, url_to_embedding
from pydantic import BaseModel
from typing import Optional
import face_recognition
from contextlib import contextmanager
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterModel(BaseModel):
    nombre: str
    image: Optional[str] = None
    imageUrl: Optional[str] = None

class VerifyModel(BaseModel):
    image: Optional[str] = None
    imageUrl: Optional[str] = None

@app.post("/register-face")
async def register_face(
    request: Request,
    nombre: Optional[str] = Form(None),
    image: Optional[str] = Form(None),
    imageUrl: Optional[str] = Form(None)
):
    # Detectar si es JSON o Form
    if request.headers.get("content-type") == "application/json":
        try:
            data = await request.json()
            nombre = data.get("nombre")
            image = data.get("image")
            imageUrl = data.get("imageUrl")
        except Exception:
            pass

    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio.")

    # 1. Obtener embedding (desde imagen o URL)
    if imageUrl:
        new_embedding = url_to_embedding(imageUrl)
    elif image:
        new_embedding = image_to_embedding(image)
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar 'image' o 'imageUrl'.")

    if new_embedding is None:
        if imageUrl:
            raise HTTPException(status_code=400, detail="No se detectó un rostro claro en la URL proporcionada. Asegúrate de que la cara sea visible.")
        else:
            raise HTTPException(status_code=400, detail="No se detectó un rostro claro en la imagen enviada. Asegúrate de que la cara sea visible.")
    
    with get_db() as db:
        # Buscar si el usuario ya fue creado por Node
        existing_user = db.query(User).filter(User.nombre == nombre).first()
        
        # 3. VERIFICACIÓN DE DUPLICADOS (Comparar con OTROS usuarios)
        users = db.query(User).all()
        for user in users:
            # Si es el mismo usuario que estamos registrando/actualizando, saltar comparación
            if existing_user and user.idUsuarios == existing_user.idUsuarios:
                continue
                
            if not user.fotoPerfil:
                continue
            
            db_embedding = url_to_embedding(user.fotoPerfil)
            if db_embedding is not None:
                matches = face_recognition.compare_faces([db_embedding], new_embedding)
                if matches[0]:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Error: Este rostro ya está registrado bajo otro usuario ('{user.nombre}')."
                    )

        # 4. Determinar la URL final
        final_url = imageUrl
        if not final_url and image:
            final_url = upload_image_to_cloudinary(image)
            if not final_url:
                raise HTTPException(status_code=500, detail="Error al subir la imagen a Cloudinary.")
            
        # 5. Guardar o Actualizar en la DB compartida
        if existing_user:
            # Si Node ya lo creó, solo aseguramos que tenga la foto actualizada
            existing_user.fotoPerfil = final_url
            db.commit()
            msg = "Rostro actualizado exitosamente para el usuario existente"
        else:
            # Si por alguna razón no existe, intentamos crearlo (aunque puede fallar por falta de campos como email)
            user = User(nombre=nombre, fotoPerfil=final_url)
            db.add(user)
            db.commit()
            msg = "Usuario y rostro registrados exitosamente"
    
    return {"msg": msg, "image_url": final_url}

@app.post("/verify-face")
async def verify_face(
    request: Request,
    image: Optional[str] = Form(None),
    imageUrl: Optional[str] = Form(None)
):
    # Detectar si es JSON o Form
    if request.headers.get("content-type") == "application/json":
        try:
            data = await request.json()
            image = data.get("image")
            imageUrl = data.get("imageUrl")
        except Exception:
            pass

    # 1. Obtener embedding actual
    if imageUrl:
        current_embedding = url_to_embedding(imageUrl)
    elif image:
        current_embedding = image_to_embedding(image)
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar 'image' o 'imageUrl'.")

    if current_embedding is None:
        if imageUrl:
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la URL para verificar.")
        else:
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen para verificar.")
    
    with get_db() as db:
        users = db.query(User).all()
        for user in users:
            if not user.fotoPerfil:
                continue
                
            db_embedding = url_to_embedding(user.fotoPerfil)
            if db_embedding is None:
                continue
                
            matches = face_recognition.compare_faces([db_embedding], current_embedding)
            if matches[0]:
                return {"user_id": user.idUsuarios, "username": user.nombre}
    
    raise HTTPException(status_code=401, detail="Usuario no reconocido")
