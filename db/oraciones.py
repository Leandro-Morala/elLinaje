from db.base import db

class OracionesModel(db):
    
    def table_name(self):
        return 'oraciones'

    def table_list_columns(self):
        return [
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('tiempo_inicio','','TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('tiempo_final','','TIMESTAMP'),
            ('tiempo_acumulado','user','DEFAULT \'user\'')
            ]
                

    def insertar(self,tiempo_inicio, tiempo_final, tiempo_acumulado ):
        '''
            modulo para insertar libros dentro de la base de datos generica
        '''
        return self.__insertar__(tiempo_inicio=tiempo_inicio,tiempo_final=tiempo_final,tiempo_acumulado=tiempo_acumulado)

    
