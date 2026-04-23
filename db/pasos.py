from db.base import db
from kivy.logger import Logger


class PasosModel(db):
    """Log de progreso de cada meta (proposito).
    Campos reutilizados:
        paso          → logro (que se logro en este avance)
        observaciones → dios_ayudo (doy gracias a Dios por...)
        fecha_creacion → fecha del registro de progreso
    """

    def table_name(self):
        return 'pasos'

    def table_list_columns(self):
        return [
            ('id',             0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_proposito',   0,  'INTEGER NOT NULL'),
            ('fecha_creacion', '',  'TEXT'),   # YYYY-MM-DD
            ('paso',           '',  'TEXT'),   # logro
            ('observaciones',  '',  'TEXT'),   # dios_ayudo
        ]

    def insertar_progreso(self, id_proposito, logro, dios_ayudo='', fecha=''):
        from datetime import datetime
        return self.__insertar__(
            id_proposito=id_proposito,
            fecha_creacion=fecha or datetime.now().strftime('%Y-%m-%d'),
            paso=logro,
            observaciones=dios_ayudo,
        )

    def get_by_proposito(self, id_proposito):
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_proposito = ? ORDER BY fecha_creacion DESC;")
        cursor = self.__run_executa_sql__(query, (id_proposito,), 'SELECT')
        return cursor.fetchall() if cursor else []

    def count_by_proposito(self, id_proposito):
        query = (f"SELECT COUNT(*) FROM {self.table_name()} "
                 f"WHERE id_proposito = ?;")
        cursor = self.__run_executa_sql__(query, (id_proposito,), 'SELECT')
        if cursor:
            row = cursor.fetchone()
            return row[0] if row else 0
        return 0

    # alias por compatibilidad con código viejo
    def insertar(self, id_proposito, paso, fecha_objetivo=None,
                 como_alcanzarlo='', observaciones='', fecha_creacion=None):
        from datetime import datetime
        return self.__insertar__(
            id_proposito=id_proposito,
            fecha_creacion=fecha_creacion or datetime.now().strftime('%Y-%m-%d'),
            paso=paso,
            observaciones=observaciones,
        )
