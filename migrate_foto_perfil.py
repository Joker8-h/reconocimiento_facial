import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL no encontrada en el archivo .env")
    exit(1)

engine = create_engine(DATABASE_URL)

def add_column():
    column_name = "fotoPerfil"
    table_name = "usuarios"
    
    # SQL para agregar la columna si no existe
    # Nota: MySQL no tiene 'IF NOT EXISTS' para columnas en ALTER TABLE directamente, 
    # así que manejamos la excepción o verificamos primero.
    
    query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(255) NULL;")
    
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
            print(f"Éxito: Columna '{column_name}' agregada a la tabla '{table_name}'.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print(f"Información: La columna '{column_name}' ya existe en la tabla '{table_name}'.")
        else:
            print(f"Error al ejecutar la migración: {e}")

if __name__ == "__main__":
    add_column()
