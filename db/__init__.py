import sys
import os
# Configuración de rutas para librerías externas

CONFIG={
    "APPNAME":"elLinaje",
    "DATEFORMAT":"%Y-%m-%d",
    "TIMEFORMAT":"%H:%M:%S",
    "VERSION":'0.1.105',
    "BASE_DIR" : os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
}

CONFIG.update({"LIBS_DIR" : os.path.join(CONFIG['BASE_DIR'], 'libs')})

if CONFIG['LIBS_DIR'] not in sys.path:
    sys.path.insert(0, CONFIG['LIBS_DIR'])
    
#from libs.share.db.base import base 
from libs.share.db import base
sys.modules['db.base'] = base


from libs.share.db import init_db
sys.modules['db.init_db'] = init_db

'''
class DatabaseManager( base.DatabaseManager ) :
    pass
' ''
    
class ConfigFile( base.ConfigFile) :
    pass
    
class base (base):
    pass

modelo de biblias ejemplo:

modelo_biblia = BibliaModel() # Tu clase que hereda de Modelo
# Cambiamos dinámicamente a la versión Reina Valera
modelo_biblia.set_custom_db('libs/bibles/RV1960.sqlite') 
versiculos = modelo_biblia.get_all() # Esto leerá de RV1960.sqlite

'''
