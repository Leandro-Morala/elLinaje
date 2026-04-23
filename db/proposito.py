import time
from db.base import db
from kivy.logger import Logger


class PropositoModel(db):

    def table_name(self):
        return 'propositos'

    def table_list_columns(self):
        return [
            ('id',             0,   'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_usuario',     1,   'INTEGER DEFAULT 1'),
            ('fecha_creacion', '',  'TEXT'),          # YYYY-MM-DD
            ('proposito',      '',  'TEXT NOT NULL'), # titulo de la meta
            ('objetivo',       '',  'TEXT'),          # que quiero alcanzar
            ('fecha_objetivo', '',  'TEXT'),          # fecha limite YYYY-MM-DD
            ('completado',     0,   'INTEGER DEFAULT 0'),
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._migrar()

    def _migrar(self):
        """Agrega columnas nuevas en DBs existentes (seguro si ya existen)."""
        for col, ddl in [('fecha_objetivo', 'TEXT'), ('completado', 'INTEGER DEFAULT 0'),
                         ('id_usuario', 'INTEGER DEFAULT 1')]:
            try:
                self.__run_executa_sql__(
                    f"ALTER TABLE {self.table_name()} ADD COLUMN {col} {ddl};",
                    (), 'ALTER')
            except Exception:
                pass  # columna ya existe

    def insertar(self, proposito, objetivo='', fecha_objetivo='', id_usuario=1):
        from datetime import datetime
        return self.__insertar__(
            id_usuario=id_usuario,
            fecha_creacion=datetime.now().strftime('%Y-%m-%d'),
            proposito=proposito,
            objetivo=objetivo,
            fecha_objetivo=fecha_objetivo,
            completado=0,
        )

    def get_by_usuario(self, id_usuario=1, solo_activas=False):
        cond = "id_usuario = ?"
        vals = [id_usuario]
        if solo_activas:
            cond += " AND completado = 0"
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE {cond} ORDER BY completado ASC, fecha_creacion DESC;")
        cursor = self.__run_executa_sql__(query, tuple(vals), 'SELECT')
        return cursor.fetchall() if cursor else []

    def marcar_completada(self, reg_id, completado=1):
        return self.actualizar(reg_id, completado=completado)
