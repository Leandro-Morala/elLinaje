from db.base import db

class PasosModel(db):

    def table_name(self):
        return 'pasos'

    def table_list_columns(self):
        return [
            ('id',             0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_proposito',   0,  'INTEGER NOT NULL REFERENCES propositos(id)'),
            ('paso',           '', 'TEXT NOT NULL'),
            ('fecha_creacion', '', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('fecha_objetivo', '', 'TIMESTAMP'),
            ('como_alcanzarlo','', 'TEXT'),
            ('observaciones',  '', 'TEXT'),
        ]

    def insertar(self, id_proposito, paso, fecha_objetivo=None, como_alcanzarlo='', observaciones='', fecha_creacion=None):
        kwargs = dict(
            id_proposito=id_proposito,
            paso=paso,
            como_alcanzarlo=como_alcanzarlo,
            observaciones=observaciones,
        )
        if fecha_objetivo:
            kwargs['fecha_objetivo'] = fecha_objetivo
        if fecha_creacion:
            kwargs['fecha_creacion'] = fecha_creacion
        return self.__insertar__(**kwargs)

    def get_by_proposito(self, id_proposito):
        return self._listar_con_filtro_key_(id_proposito, 'id_proposito')
