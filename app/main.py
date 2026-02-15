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

class CompareModel(BaseModel):
    imageUrl1: str
    imageUrl2: str

@app.post("/compare-faces")
async def compare_faces(data: CompareModel):
    """
    Compara dos imágenes faciales desde URLs de Cloudinary.
    Retorna si son la misma persona o no.
    """
    try:
        print(f"DEBUG: Comparando URLs:")
        print(f"  URL1: {data.imageUrl1}")
        print(f"  URL2: {data.imageUrl2}")
        
        # Obtener embeddings de ambas imágenes
        embedding1 = url_to_embedding(data.imageUrl1)
        embedding2 = url_to_embedding(data.imageUrl2)
        
        if embedding1 is None:
            raise HTTPException(
                status_code=400, 
                detail="No se detectó un rostro claro en la primera imagen (foto almacenada)."
            )
        
        if embedding2 is None:
            raise HTTPException(
                status_code=400, 
                detail="No se detectó un rostro claro en la segunda imagen (foto de login)."
            )
        
        # Comparar rostros
        print("DEBUG: Comparando embeddings...")
        matches = face_recognition.compare_faces([embedding1], embedding2, tolerance=0.5)
        distance = face_recognition.face_distance([embedding1], embedding2)[0]
        
        print(f"DEBUG: Match: {matches[0]}, Distance: {distance}")
        
        return {
            "match": bool(matches[0]),
            "distance": float(distance),
            "message": "Rostros coinciden" if matches[0] else "Rostros no coinciden"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR en compare_faces: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al comparar rostros: {str(e)}")

class FindMatchModel(BaseModel):
    targetUrl: str
    candidateUrls: list[str]

@app.post("/find-match")
async def find_match(data: FindMatchModel):
    """
    Busca si el targetUrl coincide con alguno de los candidateUrls.
    Detiene la búsqueda en el primer match encontrado (short-circuit).
    """
    try:
        print(f"DEBUG: Buscando duplicados para: {data.targetUrl}")
        print(f"DEBUG: Candidatos a revisar: {len(data.candidateUrls)}")

        target_embedding = url_to_embedding(data.targetUrl)
        if target_embedding is None:
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen proporcionada.")

        for url in data.candidateUrls:
            if not url: continue
            
            print(f"DEBUG: Revisando candidato: {url}")
            candidate_embedding = url_to_embedding(url)
            if candidate_embedding is None:
                print(f"DEBUG: No se pudo generar embedding para: {url}")
                continue
                
            match = face_recognition.compare_faces([candidate_embedding], target_embedding, tolerance=0.5)
            distance = face_recognition.face_distance([candidate_embedding], target_embedding)[0]
            
            print(f"DEBUG: Distancia: {distance} | Match: {match[0]}")
            
            if match[0]:
                print(f"DEBUG: ¡Duplicado encontrado! Coincide con: {url}")
                return {
                    "matchFound": True,
                    "matchDistance": float(distance),
                    "matchedUrl": url,
                    "message": "Este rostro ya está registrado."
                }

        return {
            "matchFound": False,
            "message": "No se encontraron duplicados."
        }

    except Exception as e:
        print(f"CRITICAL ERROR en find-match: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al buscar duplicados: {str(e)}")
