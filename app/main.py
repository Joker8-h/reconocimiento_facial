from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.models import User
from app.utils import image_to_embedding, upload_image_to_cloudinary, url_to_embedding
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

@app.post("/register-face")
def register_face(nombre: str = Form(...), image: str = Form(None), imageUrl: str = Form(None)):
    # 1. Obtener embedding (desde imagen o URL)
    if imageUrl:
        new_embedding = url_to_embedding(imageUrl)
    elif image:
        new_embedding = image_to_embedding(image)
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar 'image' o 'imageUrl'.")

    if new_embedding is None:
        raise HTTPException(status_code=400, detail="No se detectó rostro en la imagen proporcionada.")
    
    with get_db() as db:
        # 2. Verificar si el username ya existe
        if db.query(User).filter(User.nombre == nombre).first():
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
        
        # 3. VERIFICACIÓN DE DUPLICADOS
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

        # 4. Determinar la URL final
        final_url = imageUrl
        if not final_url and image:
            final_url = upload_image_to_cloudinary(image)
            if not final_url:
                raise HTTPException(status_code=500, detail="Error al subir la imagen a Cloudinary.")
            
        # 5. Guardar en base de datos de Python
        user = User(nombre=nombre, fotoPerfil=final_url)
        db.add(user)
        db.commit()
    
    return {"msg": "Usuario registrado exitosamente", "image_url": final_url}

@app.post("/verify-face")
def verify_face(image: str = Form(None), imageUrl: str = Form(None)):
    # 1. Obtener embedding actual
    if imageUrl:
        current_embedding = url_to_embedding(imageUrl)
    elif image:
        current_embedding = image_to_embedding(image)
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar 'image' o 'imageUrl'.")

    if current_embedding is None:
        raise HTTPException(status_code=400, detail="No se detectó rostro.")
    
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
