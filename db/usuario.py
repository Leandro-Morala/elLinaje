from .base import db
import json
from kivy.logger import Logger

class UsuariosModel(db):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__login_ = None
        
    def table_name(self):
        return 'usuarios'

    def table_list_columns(self):
        return [
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('username','','TEXT UNIQUE NOT NULL'),
            ('password','','TEXT'),
            ('mail','','TEXT'),
            ('tags','{}','TEXT DEFAULT \'{}\''),    # tags : coleccion de medallas y logros del programa ( como el actual nivel del usuario )
            ('rol','user','DEFAULT \'user\'')
            ]
                

    def insertar(self, username , tags='{}', password='', mail=''  , rol ='user' ):
        '''
            inserta un registro nuevo. 
            tambien sirve como modelo para determinar cuales son opcionales y cuales necesarias
        '''
        return self.__insertar__(
            username=username,
            password=password,        # no es necesario para la version alfa
            mail=mail, 
            tags=tags ,                 # tags o medallas que el usuario adquiera
            rol=rol 
            )
                


    def set_tag(self, user_id, tag, valor):
        '''
         guarda cualquier informacion de medalla en los tags
         set_tag <usr_id>, <tag>, <valor>
         
        '''
        usuario = self.get_one(user_id)
        if usuario :
            idusr,usr,pas,mail,tagUsr,rol = usuario
            
            # registro obtenido usuario existe
            tag_actual = json.loads(usuario['tags'])

            # actualizar la tabla, si existe se actualiza, sino se crea
            tag_actual.update( {tag:valor} )
            # actualizar el usuario
            tagDump = json.dumps(tag_actual)  # indent=4 para que formatee mas bonito
            # obtenr datos actuales y ya modificados
            
            try:
                #actualizar en la base de datos la informacion
                self.actualizar(idusr,username=usr,password=pas,mail=mail,tags=tagDump,rol=rol)
            except Exception as e:
                Logger.error(f"{e}")
                return False
            return True
        else:
            return False
            
        
    def get_tag(self, user_id, tag):
        '''
            recupera cualquier informacion de medalla o tag pasar id, y tag
            si no se encuentra devuelve falso
            get_tag <usr_id>, <tag>
        '''
        usuario = self.get_one(user_id)
        if usuario :
            # registro obtenido usuario existe
            tag_actual = json.loads(usuario['tags'])
            if tag in tag_actual:
                # respondo con el valor del tag
                return  tag_actual[tag]
            else:
                # respondo con un false:
                return False
                
    def check(self,user_id,usr,passwd):
        usuario = self.get_one(user_id)
        ban_us=0
        ban_ps=0
        
        if usr == usuario['username'] : ban_us=1
        if passwd == usuario['password' ] : ban_ps=1
        
        return (ban_us + ban_ps ) == 2

    def get_player_data(self,params):
        # lo mismo que get tag pero para player = 1
        Logger.debug(f"player_data:{params}")
        usr= self.get_one(1)
        if usr :
            # existe el usuario
            return self.get_tag(1,params)
            
    def update_player_data(self,params,value):
        # lo mismo te set tag pero para el player = 1
        Logger.debug(f"set player data{params} : {value}")
        usr= self.get_one(1)
        if usr:
            return self.set_tag(1,params,value)
        else:
            # usuario no existente
            return False
