import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Common database names found in the project
databases = ["bd_compartido", "proyectoacceso", "autentificacion", "moviflex"]

user = "root"
password = "rootpassword" 

password = "1118023359AAPV"
host = "localhost"
port = 3306

for db_name in databases:
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
        print(f"✅ Conexión exitosa a la base de datos: {db_name}")
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"   Tablas encontradas: {tables}")
        
        if "usuarios" in tables:
            cursor.execute("DESCRIBE usuarios")
            columns = [c[0] for c in cursor.fetchall()]
            print(f"   Columnas en 'usuarios': {columns}")
            if "fotoPerfil" in columns:
                print(f"   ⭐ ¡ESTA ES LA BASE DE DATOS CORRECTA!")
        
        conn.close()
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:
            print(f"❌ La base de datos '{db_name}' no existe.")
        else:
            print(f"⚠️ Error conectando a '{db_name}': {e}")
    except Exception as e:
        print(f"⚠️ Error inesperado con '{db_name}': {e}")
