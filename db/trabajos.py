from .base import db
from datetime import datetime
from db import CONFIG

class TrabajosModel(db):
    # FORMATO DE FECHAHORA NORMALIZADO %Y-%m-%d %H:%M:%S
    DATE_FORMAT=CONFIG['DATEFORMAT'] +' '+ CONFIG['TIMEFORMAT']
    
    def table_name(self):
        return 'trabajos'

    def table_list_columns(self):
        return [
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('tiempo_inicio','','TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('tiempo_final','','TIMESTAMP'),
            ('tiempo_acumulado','','TIMESTAMP'),
            ('objservaciones','','TEXT'),
            ('tags','','TEXT'),
            ]
                

    def insertar(self, tiempo_inicio, tiempo_final, tiempo_acumulado , observaciones, tags):
        '''
            modulo para insertar libros dentro de la base de datos generica
            inicio = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        '''
        tiempo = datetime.strptime( tiempo_inicio , TrabajosModel.DATE_FORMAT )
        return self.__insertar__(
            tiempo_inicio=tiempo_inicio,
            tiempo_final=tiempo_final,
            tiempo_acumulado=tiempo_acumulado,
            objservaciones=objservaciones,tags=tags)
