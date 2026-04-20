import sqlite3
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from kivy.logger import Logger

class BackupEngine:
    """
    Motor independiente para la gestión de copias de seguridad cifradas.
    """
    def __init__(self, db_path='data/mercado.db'):
        self.db_path = db_path
        # Salt estático para la derivación de la llave. 
        # En una app de producción, podrías hacerlo dinámico y guardarlo en el archivo.
        self.salt = b'\x19\xed\xad\x15\x1e\xdf\xfe\x01'

    def _derivar_llave(self, password):
        """Genera una llave Fernet a partir de un string usando PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def exportar(self, destino_bin, password):
        """
        Genera un volcado SQL, lo cifra y lo guarda en la ruta destino.
        """
        try:
            if not os.path.exists(self.db_path):
                return False, "La base de datos original no existe."

            # 1. Obtener volcado SQL
            conn = sqlite3.connect(self.db_path)
            # iterdump genera el script SQL completo para reconstruir la DB
            script_sql = "".join(line for line in conn.iterdump())
            conn.close()

            # 2. Cifrar contenido
            f = Fernet(self._derivar_llave(password))
            contenido_cifrado = f.encrypt(script_sql.encode('utf-8'))

            # 3. Escribir archivo binario
            with open(destino_bin, 'wb') as f_out:
                f_out.write(contenido_cifrado)

            Logger.info(f"Backup: Exportación exitosa en {destino_bin}")
            return True, "Copia de seguridad creada con éxito."
        except Exception as e:
            Logger.error(f"Backup Error: {e}")
            return False, str(e)

    def importar(self, origen_bin, password):
        """
        Lee un archivo binario, lo descifra y reconstruye la base de datos.
        """
        try:
            if not os.path.exists(origen_bin):
                return False, "El archivo de respaldo no existe."

            # 1. Leer y descifrar
            f = Fernet(self._derivar_llave(password))
            with open(origen_bin, 'rb') as f_in:
                datos_cifrados = f_in.read()
            
            try:
                script_sql = f.decrypt(datos_cifrados).decode('utf-8')
            except Exception:
                return False, "Contraseña incorrecta o archivo corrupto."

            # 2. Reconstrucción de base de datos
            # Hacemos una copia de seguridad temporal de la actual antes de borrar
            if os.path.exists(self.db_path):
                os.replace(self.db_path, self.db_path + ".bak")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Ejecutamos el script de reconstrucción
            cursor.executescript(script_sql)
            conn.commit()
            conn.close()

            Logger.info("Backup: Restauración completada exitosamente.")
            return True, "Base de datos restaurada correctamente."
        except Exception as e:
            Logger.error(f"Backup Error: {e}")
            return False, str(e)
