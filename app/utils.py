import face_recognition
import numpy as np
import base64
import io
import os
from PIL import Image
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image_to_cloudinary(base64_image: str):
    try:
        print("Iniciando subida a Cloudinary...")
        if ',' in base64_image:
            print("Separando prefijo base64...")
            base64_image = base64_image.split(',')[1]
        
        # Cloudinary uploader can handle base64 directly or file objects
        # We prefix with data:image/png;base64, if not present for the uploader
        upload_result = cloudinary.uploader.upload(
            f"data:image/png;base64,{base64_image}",
            folder="face_recognition"
        )
        url = upload_result.get("secure_url")
        print(f"Subida exitosa: {url}")
        return url
    except Exception as e:
        print(f"Error crítico al subir imagen a Cloudinary: {e}")
        return None

import requests

def url_to_embedding(url: str):
    try:
        print(f"Descargando imagen desde URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al descargar imagen: Status {response.status_code}")
            return None
        
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        
        # Convertir a RGB si es necesario (face_recognition prefiere RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        image_np = np.array(image)

        encodings = face_recognition.face_encodings(image_np)
        if not encodings:
            print("No se encontró rostro en la imagen de la URL.")
            return None
        return encodings[0]
    except Exception as e:
        print(f"Error al procesar imagen desde URL: {e}")
        return None

def image_to_embedding(base64_image: str):
    try:
        # Si la imagen tiene el prefijo data:image/..., sepáralo
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        image_np = np.array(image)

        encodings = face_recognition.face_encodings(image_np)
        if not encodings:
            return None
        return encodings[0]
    except Exception as e:
        print(f"Error al procesar imagen: {e}")
        return None
