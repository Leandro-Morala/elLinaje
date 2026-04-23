from db.base import db


class EstudioModel(db):
    """Estudios bíblicos del usuario: título + versículos de cualquier versión + notas."""

    def table_name(self):
        return 'estudio_versiculos'

    def table_list_columns(self):
        return [
            ('id',             0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_usuario',     1,  'INTEGER DEFAULT 1'),
            ('fecha_creacion', '', 'TEXT'),
            ('titulo',         '', 'TEXT'),
            # JSON: [{"b":idBook,"c":cap,"v":verse,"n":bookName,"lib":path,"txt":text}, ...]
            ('datos_json',     '', 'TEXT'),
            ('notas',          '', 'TEXT'),   # blob extenso de notas de estudio
            ('etiqueta',       '', 'TEXT'),
        ]

    def insertar(self, titulo, datos_json, notas='', etiqueta='', id_usuario=1):
        from datetime import datetime
        return self.__insertar__(
            id_usuario=id_usuario,
            fecha_creacion=datetime.now().strftime('%Y-%m-%d'),
            titulo=titulo,
            datos_json=datos_json,
            notas=notas,
            etiqueta=etiqueta,
        )

    def get_by_usuario(self, id_usuario=1, limit=200):
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_usuario = ? ORDER BY fecha_creacion DESC LIMIT ?;")
        cursor = self.__run_executa_sql__(query, (id_usuario, limit), 'SELECT')
        return cursor.fetchall() if cursor else []
