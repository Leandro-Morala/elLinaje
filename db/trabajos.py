from .base import db
from kivy.logger import Logger


class TrabajosModel(db):

    def table_name(self):
        return 'trabajos'

    def table_list_columns(self):
        return [
            ('id',               0,    'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('tiempo_inicio',    '',   'TEXT'),   # fecha YYYY-MM-DD
            ('tiempo_final',     '',   'TEXT'),
            ('tiempo_acumulado', '',   'TEXT'),   # horas como string float
            ('objservaciones',   '',   'TEXT'),
            ('tags',             '{}', 'TEXT'),
        ]

    def insertar(self, fecha, duracion_horas, descripcion='', tags='{}'):
        return self.__insertar__(
            tiempo_inicio=str(fecha),
            tiempo_final='',
            tiempo_acumulado=str(duracion_horas),
            objservaciones=str(descripcion),
            tags=tags,
        )

    def get_anios(self):
        """Devuelve lista de años con registros, ordenados desc."""
        query = (f"SELECT DISTINCT substr(tiempo_inicio, 1, 4) as anio "
                 f"FROM {self.table_name()} "
                 f"WHERE tiempo_inicio IS NOT NULL AND tiempo_inicio != '' "
                 f"ORDER BY anio DESC;")
        cursor = self.__run_executa_sql__(query, (), 'SELECT')
        if cursor:
            rows = cursor.fetchall()
            return [r[0] for r in rows if r[0] and len(r[0]) == 4]
        return []

    def get_filtrado(self, anio=None, mes=None, limit=500):
        """Devuelve registros filtrados por año y/o mes (YYYY-MM-DD en tiempo_inicio)."""
        conditions = []
        values = []
        if anio and str(anio) != 'Todos':
            conditions.append("substr(tiempo_inicio, 1, 4) = ?")
            values.append(str(anio))
        if mes and str(mes) not in ('Todos', '0', ''):
            conditions.append("substr(tiempo_inicio, 6, 2) = ?")
            values.append(str(mes).zfill(2))
        where = ' AND '.join(conditions) if conditions else '1=1'
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE {where} ORDER BY tiempo_inicio DESC LIMIT {limit};")
        cursor = self.__run_executa_sql__(query, tuple(values), 'SELECT')
        if cursor:
            return cursor.fetchall()
        return []
