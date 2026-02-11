from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.models import User
from app.utils import image_to_embedding, upload_image_to_cloudinary, url_to_embedding
import face_recognition
from contextlib import contextmanager

# Base.metadata.create_all(bind=engine) # Comentado para producción
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

@app.post("/register-face")
def register_face(nombre: str = Form(...), image: str = Form(...)):
    # 1. Verificar si hay un rostro antes de subir
    new_embedding = image_to_embedding(image)
    if new_embedding is None:
        raise HTTPException(status_code=400, detail="No se detectó rostro en la imagen proporcionada.")
    
    with get_db() as db:
        # 2. Verificar si el username ya existe
        if db.query(User).filter(User.nombre == nombre).first():
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
        
        # 3. VERIFICACIÓN DE DUPLICADOS: Comparar con rostros existentes
        users = db.query(User).all()
        for user in users:
            if not user.fotoPerfil:
                continue
            
            db_embedding = url_to_embedding(user.fotoPerfil)
            if db_embedding is not None:
                matches = face_recognition.compare_faces([db_embedding], new_embedding)
                if matches[0]:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Error: Este rostro ya está registrado bajo el usuario '{user.nombre}'."
                    )

        # 4. Si no es duplicado, subir imagen a Cloudinary
        image_url = upload_image_to_cloudinary(image)
        if not image_url:
            raise HTTPException(status_code=500, detail="Error al subir la imagen a Cloudinary.")
            
        print(f"URL de imagen obtenida: {image_url}")
        
        # 5. Guardar solo nombre e fotoPerfil
        user = User(nombre=nombre, fotoPerfil=image_url)
        db.add(user)
        db.commit()
        print("Usuario registrado exitosamente (rostro único).")
    
    return {"msg": "Usuario registrado exitosamente", "image_url": image_url}

@app.post("/verify-face")
def verify_face(image: str = Form(...)):
    # 1. Obtener embedding de la imagen actual (la de la cámara)
    current_embedding = image_to_embedding(image)
    if current_embedding is None:
        raise HTTPException(status_code=400, detail="No se detectó rostro.")
    
    with get_db() as db:
        users = db.query(User).all()
        for user in users:
            if not user.fotoPerfil:
                continue
                
            # 2. Obtener embedding de la imagen en Cloudinary
            db_embedding = url_to_embedding(user.fotoPerfil)
            if db_embedding is None:
                print(f"No se pudo obtener embedding para el usuario {user.nombre} desde la URL.")
                continue
                
            # 3. Comparar
            matches = face_recognition.compare_faces([db_embedding], current_embedding)
            if matches[0]:
                return {"user_id": user.idUsuarios, "username": user.nombre}
    
    raise HTTPException(status_code=401, detail="Usuario no reconocido")
