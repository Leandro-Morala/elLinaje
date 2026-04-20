from kivy.properties import StringProperty
#from kivy.lang import Builder
from kivy.logger import Logger
from screens.basescreen import BaseScreen
import json
# se carga de forma automatica al inicio.
#Builder.load_file('kv_files/playerdata.kv')
'''
            username=username,
            password=password,        # no es necesario para la version alfa
            mail=mail, 
            tags=tags ,                 # tags o medallas que el usuario adquiera
            rol=rol 
'''
class PlayerDataScreen(BaseScreen):
    # Propiedades para manejar los campos de texto
    player_name = StringProperty('')
    player_lastname = StringProperty('')
    
    def save_and_continue(self):
        
        usr = self.user.get_one(1)
        nombre = self.player_name if self.player_name else 'Hijo'
        apellido = self.player_lastname if self.player_lastname else 'de Dios'
        usrname = f"{nombre},\n{apellido}"
        if not usr :
            # no existe usuario, agregando nuevo usuario
            # tags = {'nivel':0,'on_load':True,'foto_perfil':'default.png'}
            # username , tags='{}', password='', mail=''  , rol ='user' 
            idusr=self.user.insertar( usrname ,  json.dumps({'nivel':0,'no_load':True,'foto_perfil': 'default.png'})   ) # asumo id=1
            if idusr == 1 :
                Logger.info("usuario agregado con exito")
            else:
                Logger.error("falla al agregar usuario...")
            
            #self.user.set_tag( 1 , 'nivel', 0)
            #self.user.set_tag( 1 , 'on_load', 'True')
            #self.user.set_tag( 1 , 'foto_perfil', 'default.png' )
        else:
            # modificando actual:            
            self.user.actualizar( 1 , username = usrname )
            # recalcular en nivel actual, y volver a colocar los tag como corresponde:
            tag={'nivel':0,'no_load':True,'foto_perfil': 'default.png'}
            #extratags=self.user.get_player_data(params)
            self.user.actualizar(1, tags = json.dumps(tag) )
            
        self.manager.current = 'faith_data'
        '''
        # El ID del widget Image en tu .kv es 'player_image'.
        try:
            # Esto obtiene el string de la ruta del archivo (ej. 'img/nueva_foto.png')
            image_source_path = self.ids.player_image.source 
        except AttributeError:
            # Si no hay widget con ese ID, usa el valor por defecto.
            image_source_path = 'default.png'
        # Aquí puedes agregar validación si lo deseas (ej. si el nombre está vacío)
        data_to_save1 = {
            'nombre': self.player_name if self.player_name else 'Hijo',
            'apellido': self.player_lastname if self.player_lastname else 'de Dios',
            'on_load': True,
            'foto_perfil': image_source_path,  # Almacenar la ruta de la imagen
        }
        #update( nombre = self.player_name if self.player_name else 'Hijo',   
        #apellido=self.player_lastname if self.player_lastname else 'de Dios',
        #    # La lógica de la foto (selfie) se manejaría aquí, 
        #    # guardando la ruta del archivo o un indicador.
        #foto_perfil = self.Image.source ,
        #)
        
        for key, value in data_to_save1.items():
            self.player.update_player_data(key, value) # Llama a tu método (key, value)
        self.player.save_data()
        # 2. Navegar a la siguiente pantalla
        self.manager.current = 'faith_data'
        '''
    def skip(self):
        # Si presiona omitir, simplemente navega a la siguiente pantalla
        self.manager.current = 'faith_data'
