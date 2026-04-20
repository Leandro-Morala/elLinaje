from db.base import db

class PropositoModel(db):

    def table_name(self):
        return 'propositos'

    def table_list_columns(self):
        return [
            ('id',            0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('fecha_creacion','', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('proposito',     '', 'TEXT NOT NULL'),
            ('objetivo',      '', 'TEXT'),
        ]

    def insertar(self, proposito, objetivo='', fecha_creacion=None):
        kwargs = dict(proposito=proposito, objetivo=objetivo)
        if fecha_creacion:
            kwargs['fecha_creacion'] = fecha_creacion
        return self.__insertar__(**kwargs)
