from db.base import db

class CapitulosModel(db):
    def table_name(self):
        return 'capitulos'

    def table_list_columns(self):
        return [
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('cap_ver_vers','','TEXT UNIQUE NOT NULL'), # capitulo versiculo versionAsociada
            ('texto','','TEXT NOT NULL'),               # contenido del capitulo
            ('id_libro',0,'INTEGER NOT NULL'),          # id del libro asociado.
            ('tag','','TEXT'),                          # tags y datos auxiliares agregaod a posterior necesarios para capitulos que son o no de biblias originales.
            ('idlibro',None,'INTEGER NOT NULL REFERENCES librosbiblicos(id)')
        ]
    
    def insertar(cap_ver_vers, texto , id_libro , tag , idlibro ):
        '''
            modulo para insertar libros dentro de la base de datos generica
        '''
        return self.__insertar__( cap_ver_vers=cap_ver_vers,texto=texto,id_libro=id_libro,tag=tag,idlibro=idlibro)


