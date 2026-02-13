import face_recognition
import numpy as np
import base64
import io
import os
from PIL import Image, ImageOps
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
        print(f"DEBUG: Descargando imagen desde URL: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"ERROR: No se pudo descargar imagen. Status: {response.status_code}")
            return None
        
        image_data = response.content
        print(f"DEBUG: Imagen descargada. Tamaño: {len(image_data)} bytes")
        
        image = Image.open(io.BytesIO(image_data))
        
        # Corregir orientación EXIF (muy común en móviles)
        image = ImageOps.exif_transpose(image)
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            print(f"DEBUG: Convirtiendo imagen de {image.mode} a RGB")
            image = image.convert('RGB')
            
        image_np = np.array(image)
        print(f"DEBUG: Procesando face_recognition en imagen de {image_np.shape}")

        # Intentar detección normal
        encodings = face_recognition.face_encodings(image_np)
        
        # Si no detecta, intentar con upsampling (más lento pero detecta caras pequeñas)
        if not encodings:
            print("DEBUG: No se detectó rostro en pase inicial. Reintentando con upsampling...")
            encodings = face_recognition.face_encodings(image_np, num_jitters=1)
        
        if not encodings:
            print("WARNING: No se encontró ningún rostro claro en la imagen de la URL.")
            return None
        
        print("DEBUG: Rostro detectado exitosamente.")
        return encodings[0]
    except Exception as e:
        print(f"CRITICAL ERROR: Error al procesar imagen desde URL: {str(e)}")
        return None

def image_to_embedding(base64_image: str):
    try:
        print("DEBUG: Procesando imagen base64...")
        # Si la imagen tiene el prefijo data:image/..., sepáralo
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        print(f"DEBUG: Imagen decodificada. Tamaño: {len(image_data)} bytes")
        
        image = Image.open(io.BytesIO(image_data))
        
        # Corregir orientación EXIF
        image = ImageOps.exif_transpose(image)
        
        if image.mode != 'RGB':
            print(f"DEBUG: Convirtiendo imagen de {image.mode} a RGB")
            image = image.convert('RGB')
            
        image_np = np.array(image)
        print(f"DEBUG: Procesando face_recognition en imagen de {image_np.shape}")

        # Intentar detección normal
        encodings = face_recognition.face_encodings(image_np)
        
        # Si no detecta, intentar con upsampling
        if not encodings:
            print("DEBUG: Reintentando base64 con upsampling...")
            encodings = face_recognition.face_encodings(image_np, num_jitters=1)

        if not encodings:
            print("WARNING: No se encontró ningún rostro claro en el base64.")
            return None
            
        print("DEBUG: Rostro detectado exitosamente.")
        return encodings[0]
    except Exception as e:
        print(f"CRITICAL ERROR: Error al procesar imagen base64: {str(e)}")
        return None
