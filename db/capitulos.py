from db.base import db
from kivy.logger import Logger
import time


class CapitulosModel(db):
    """Versiculos biblicos memorizados por el usuario."""

    def table_name(self):
        return 'capitulos'

    def table_list_columns(self):
        return [
            ('id',             0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_usuario',     1,  'INTEGER NOT NULL'),
            ('book_id',        0,  'INTEGER NOT NULL'),
            ('book_name',      '', 'TEXT NOT NULL'),
            ('capitulo',       0,  'INTEGER NOT NULL'),
            ('versiculo',      0,  'INTEGER NOT NULL'),
            ('texto',          '', 'TEXT NOT NULL'),
            ('fecha_creacion', '', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('tiempo_final',   0,  'INTEGER DEFAULT 0'),  # unix timestamp de expiracion
            ('veces_acertado', 0,  'INTEGER DEFAULT 0'),
            ('veces_fallado',  0,  'INTEGER DEFAULT 0'),
            ('nivel_refuerzo', 0,  'INTEGER DEFAULT 0'),
        ]

    def insertar(self, id_usuario, book_id, book_name, capitulo, versiculo, texto):
        return self.__insertar__(
            id_usuario=id_usuario,
            book_id=book_id,
            book_name=book_name,
            capitulo=capitulo,
            versiculo=versiculo,
            texto=texto,
        )

    def get_by_usuario(self, id_usuario):
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_usuario = ? ORDER BY book_id, capitulo, versiculo;")
        cursor = self.__run_executa_sql__(query, (id_usuario,), 'SELECT')
        if cursor:
            return cursor.fetchall()
        return []

    def existe(self, id_usuario, book_id, capitulo, versiculo):
        query = (f"SELECT id FROM {self.table_name()} "
                 f"WHERE id_usuario = ? AND book_id = ? AND capitulo = ? AND versiculo = ? LIMIT 1;")
        cursor = self.__run_executa_sql__(query, (id_usuario, book_id, capitulo, versiculo), 'SELECT')
        if cursor:
            return cursor.fetchone() is not None
        return False

    # ------------------------------------------------------------------
    # Sistema de vida util
    # ------------------------------------------------------------------

    def calcular_vida_dias(self, total_versiculos):
        """1 dia por versiculo, minimo 7, maximo 365."""
        return min(365, max(7, total_versiculos))

    def renovar_vida(self, id_usuario):
        """Recalcula tiempo_final para todos los versiculos del usuario segun cantidad total."""
        registros = self.get_by_usuario(id_usuario)
        total = len(registros) if registros else 0
        vida_dias = self.calcular_vida_dias(total)
        nuevo_fin = int(time.time()) + (vida_dias * 86400)
        sql = f"UPDATE {self.table_name()} SET tiempo_final = ? WHERE id_usuario = ?;"
        self.__run_executa_sql__(sql, (nuevo_fin, id_usuario), 'UPDATE')
        Logger.info(f"[Capitulos] vida renovada: {total} versiculos -> {vida_dias} dias")
        return vida_dias

    def limpiar_expirados(self, id_usuario):
        """Elimina versiculos cuyo tiempo_final ya paso. Devuelve cantidad eliminada."""
        ahora = int(time.time())
        count_sql = (f"SELECT COUNT(*) FROM {self.table_name()} "
                     f"WHERE id_usuario = ? AND tiempo_final > 0 AND tiempo_final < ?;")
        cursor = self.__run_executa_sql__(count_sql, (id_usuario, ahora), 'SELECT')
        eliminados = 0
        if cursor:
            row = cursor.fetchone()
            eliminados = int(row[0]) if row else 0
        if eliminados > 0:
            sql = (f"DELETE FROM {self.table_name()} "
                   f"WHERE id_usuario = ? AND tiempo_final > 0 AND tiempo_final < ?;")
            self.__run_executa_sql__(sql, (id_usuario, ahora), 'DELETE')
            Logger.info(f"[Capitulos] {eliminados} versiculos expirados eliminados")
        return eliminados

    # ------------------------------------------------------------------
    # Estadisticas del juego
    # ------------------------------------------------------------------

    def actualizar_estadisticas(self, reg_id, acertado=True):
        registro = self.get_one(reg_id)
        if not registro:
            return False
        try:
            if acertado:
                return self.actualizar(reg_id,
                    veces_acertado=registro['veces_acertado'] + 1,
                    nivel_refuerzo=min(5, registro['nivel_refuerzo'] + 1),
                )
            else:
                return self.actualizar(reg_id,
                    veces_fallado=registro['veces_fallado'] + 1,
                    nivel_refuerzo=max(0, registro['nivel_refuerzo'] - 1),
                )
        except Exception as e:
            Logger.error(f"[CapitulosModel] actualizar_estadisticas: {e}")
            return False
