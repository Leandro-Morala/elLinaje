import time
from datetime import datetime
from db.base import db
from kivy.logger import Logger


class OfrendasModel(db):
    """Registro de ofrendas monetarias del usuario."""

    def table_name(self):
        return 'ofrendas'

    def table_list_columns(self):
        return [
            ('id',          0,    'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_usuario',  1,    'INTEGER NOT NULL'),
            ('fecha',       0,    'INTEGER DEFAULT 0'),   # unix timestamp
            ('monto',       0.0,  'REAL DEFAULT 0'),
            ('descripcion', '',   'TEXT'),
        ]

    def insertar(self, id_usuario, monto, descripcion=''):
        return self.__insertar__(
            id_usuario=id_usuario,
            fecha=int(time.time()),
            monto=float(monto),
            descripcion=descripcion,
        )

    def get_by_usuario(self, id_usuario, limit=500):
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_usuario = ? ORDER BY fecha DESC LIMIT {limit};")
        cursor = self.__run_executa_sql__(query, (id_usuario,), 'SELECT')
        if cursor:
            return cursor.fetchall()
        return []

    def get_anios(self, id_usuario):
        """Devuelve lista de años con registros, ordenados desc."""
        query = (f"SELECT DISTINCT strftime('%Y', datetime(fecha, 'unixepoch')) as anio "
                 f"FROM {self.table_name()} WHERE id_usuario = ? ORDER BY anio DESC;")
        cursor = self.__run_executa_sql__(query, (id_usuario,), 'SELECT')
        if cursor:
            rows = cursor.fetchall()
            return [r[0] for r in rows if r[0]]
        return []

    def get_filtrado(self, id_usuario, anio=None, mes=None, limit=500):
        """Devuelve registros filtrados por año y/o mes."""
        conditions = ["id_usuario = ?"]
        values = [id_usuario]
        if anio and str(anio) != 'Todos':
            conditions.append("strftime('%Y', datetime(fecha, 'unixepoch')) = ?")
            values.append(str(anio))
        if mes and str(mes) not in ('Todos', '0', ''):
            conditions.append("strftime('%m', datetime(fecha, 'unixepoch')) = ?")
            values.append(str(mes).zfill(2))
        where = ' AND '.join(conditions)
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE {where} ORDER BY fecha DESC LIMIT {limit};")
        cursor = self.__run_executa_sql__(query, tuple(values), 'SELECT')
        if cursor:
            return cursor.fetchall()
        return []
