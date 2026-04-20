from kivy.app import App
from kivy.uix.screenmanager import ScreenManager ,FadeTransition, WipeTransition, SwapTransition
from kivy.properties import DictProperty
from kivy.logger import Logger ,LOG_LEVELS
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
import os
import random
# importar librerias de bases de datos
from db import init_db, base
from db.base import DatabaseManager
from db.libros import LibrosBiblicosModel 
from db.oraciones import OracionesModel 
from db.trabajos import TrabajosModel
from db.proposito import PropositoModel
from db.pasos import PasosModel
from db.usuario import UsuariosModel
from db.capitulos import CapitulosModel
#importacion de libreria especial:
# from db.bibliasestaticas import bookModel,metadataModel,verseModel,BibliasDisponibles
from db.bibliasestaticas import Biblia,BibliasDisponibles


# boton estilizado listo para ser utilizado
from screens.plantilla import BotonEstilizado
from screens.mani import ManiScreen

# from screens.config import ConfigScreen

def load_all_kv_files(path):
    """Escanea un directorio recursivamente y carga todos los archivos .kv."""
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.kv'):
                Builder.load_file(os.path.join(root, file))
                Logger.info(f"KV cargado: {file}")

load_all_kv_files("kv_files")

from screens.help_data import HelpSheet
from screens.playerdata import PlayerDataScreen
from screens.faithdata import FaithDataScreen

from screens.welcome import WelcomeScreen
from screens.main import MainScreen
from screens.prayer import PrayerScreen
from screens.work import WorkScreen
from screens.verses import VersesScreen
from screens.purposes import PurposesScreen
from screens.config import ConfigScreen

from defaultconfig import defaultConfig

'''

config (Gestión de .ini)
root (Referencia al widget base)
user_data_dir (Ruta de datos de usuario)
directory (Ruta de la app)

'''

class GameApp(App):
    # configuracion general de la aplicacion
    app_config = DictProperty( defaultConfig )
    """Clase principal de la aplicación Kivy."""
    
    
    def build(self):
        # configuracion necesaria para la base de datos
        Logger.debug("Inicializando Aplicacion....")
        
        #DatabaseManager.configurar( ('data','ElLinaje.db') )
        Logger.info(f"ruta de base de datos:{self.app_config['DB_PATH']}")
        
        DatabaseManager.configurar( 
            db_path = (self.app_config['DB_PATH'],) ,
            img_path= (self.app_config['IMG_PATH'],) ,
            static_bibles_path= (self.app_config['SATIC_BIBLES_PATH'],) ,
            formato_fecha= self.app_config['FORMATO_FECHA']  ,
            formato_hora = self.app_config['FORMATO_HORA']  
            )
        
        self.dbmodel = {}   # utilidad para administrar las bases de datos
        Logger.debug("Db model cargando...")
        
        # crear base de datos y archivos relacionados
        self.librosbiblicosmodel = LibrosBiblicosModel()
        self.dbmodel.update({"LibrosBiblicosModel":self.librosbiblicosmodel})
        
        self.capitulsmodel = CapitulosModel()
        self.dbmodel.update({"CapitulosModel":self.capitulsmodel})
        
        self.oracionesmodel = OracionesModel()
        self.dbmodel.update({"OracionesModel":self.oracionesmodel})
        
        self.trabajos = TrabajosModel()
        self.dbmodel.update({"TrabajosModel":self.trabajos})
        
        self.proposito = PropositoModel()
        self.dbmodel.update({"PropositoModel":self.proposito})
        
        self.pasos = PasosModel()
        self.dbmodel.update({"PasosModel":self.pasos})
                
        # los datos de la persona se almacenaran aqui
        self.usuariomodel = UsuariosModel()
        self.dbmodel.update({"UsuariosModel":self.usuariomodel})


        init_db.init_db(self)
        Logger.debug("init_db cargado....")
        # lo agrego despues de que pasa la prueba de "creacion de archivos de bases de datos. ya que 
        # estos archivos tiene que estar en la isntalacion del paquete original... se presupone
        self.bibliasestaticas = { 'librerias': BibliasDisponibles() ,'contenido':[] }
        self.dbmodel.update({"Biblioteca":self.bibliasestaticas })        
        
        listadobiblias = self.bibliasestaticas['librerias'].listar_biblias_disponibles()
        # Logger.debug(f"listado:{listadobiblias=}")
        # ['ASV.sqlite', 'Reina-Valera 1960 (RVR1960).sqlite', 'World_English_Bible.sqlite', 'alternative_book_names.sqlite', 'Las_Sagradas_Escrituras.sqlite', 'New Life Version (NLV).sqlite', 'Dios Habla Hoy (DHH).sqlite']
        for biblia in listadobiblias :
            # construir una blibilia stdt/bibles/
            path_biblia=os.path.join('stdt','bibles', biblia )
            
            biblia=Biblia()
            #meta = metadataModel()
            #verso = verseModel()
            
            biblia.set_custom_db(path_biblia)
            #meta.set_custom_db(path_biblia)
            #verso.set_custom_db(path_biblia)
            Logger.debug(f"agregando biblia {path_biblia} ..")
            self.bibliasestaticas['contenido'].append( biblia )
            
             
        # Cargar los archivos .kv. Kivy busca automáticamente .kv que coincidan 
        # con el nombre de la clase App (GameApp -> game.kv), pero al usar módulos 
        # separados, cargaremos los archivos .kv de nuestra carpeta 'kv_files' 
        # manualmente en cada módulo, o Kivy los buscará por nombre de clase.
        # Crear el Screen Manager para la navegación
        sm = ScreenManager(transition=WipeTransition())
                
        # 1. Agregar las nuevas pantallas de inicio (todas reciben Jugador)
        sm.add_widget(WelcomeScreen(name='welcome'))        # plantilla de bienvenida
        sm.add_widget(PlayerDataScreen(name='player_data')) # plantilla de ingreso de datos personales
        sm.add_widget(FaithDataScreen(name='faith_data'))   # plantilla de datos para aceptar a Cristo y Bautizarse
        
        # Añadir todas las pantallas
        # Cada clase de pantalla cargará su propio archivo .kv
        sm.add_widget(MainScreen(name='main'))          # principal
        sm.add_widget(PrayerScreen(name='prayer' ))      # rezos
        sm.add_widget(WorkScreen(name='work' ))          # trabajos de iglesia
        sm.add_widget(VersesScreen(name='verses' ))      # juego de versiculos
        sm.add_widget(ManiScreen(name='mani' ))          # trabajo de la inglesia
        sm.add_widget(PurposesScreen(name='purposes' ))  # propositos propios
        sm.add_widget(ConfigScreen(name='config' ))      # configuracion y salidas
        
        
        # sm.current = 'main'
        sm.current = 'welcome'                                          # pagina de bienvenida
        #self.rellenar_campos()
        return sm

    def getModel(self,model):
        if model in self.dbmodel:
            return self.dbmodel[model]
        else:
            return None
            
                
    def salir_del_juego(self):
        Logger.debug("Guardando progreso de El Linaje...")
        #self.stop() # Cierra la aplicación# Aquí puedes guardar datos antes de irte
        Logger.debug("Guardando progreso de El Linaje...")
        #self.stop() # Cierra la aplicación
        # self.confirm_exit()
        self.stop()
    
    def confirm_exit(self):
        content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        content.add_widget(Label(text='¿Seguro que quieres salir de\nEl Linaje?'))
        
        buttons = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
        
        btn_yes = Button(text='Sí, salir', background_color=(0.8, 0.2, 0.2, 1))
        btn_no = Button(text='No, me quedo')

        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)

        popup = Popup(title='Confirmar salida', content=content, size_hint=(0.7, 0.4))
        
        # Lógica de los botones
        rtn = btn_yes.bind(on_release=App.get_running_app().stop)
        btn_no.bind(on_release=popup.dismiss)
        popup.open()
        return rtn
    
    def get_promesa(self,Fail=False):
        '''
            obtener una promesa
        '''
        promesas=[
            ('Filipenses',4,19,50),    ('Jeremías',29,11,24),     ('2 Pedro',1,4,61),
            ('Isaías',41,10,23),       ('2 Corintios',1,20,47),   ('Juan',3,16,43),
            ('1 Juan',1,9,62),         ('Isaías',43,2,23),        ('Juan',14,27,43),
            ('Josué',23,146),         ('Isaías',40,31,23),       ('Romanos',8,28,45),
            ('2 Corintios',7,1,47),     ('Mateo',11,'28-29',40),   ('Santiago',1,15,59),
            ('Isaías',40,'26-31',23),  ('2 Pedro',3,9,61),        ('Deuteronomio',31,8,5),
            ('1 Corintios',10,13,46),  ('Jeremías',30,17,24),     ('Isaías',54,17,23),
            ('Romanos',6,23,45),       ('Romanos',10,9,45),       ('Éxodo',15,26,2),
            ('Apocalipsis',21,4,66),   ('Josué',1,9,6),          ('Apocalipsis',3,5,66),
            ('Isaías',26,3,23),        ('Romanos',8,32,45),       ('1 Reyes',8,56,11),
            ]
        # elegir uno
        r=random.Random()
        
        maximo = len(promesas)
        quien = int( r.random()*maximo )
        # quien = 15 # prueba de ISAIAS 40:26-31
        # quien = 0
        ver_promesa = promesas[quien]
        
        biblioteca = self.bibliasestaticas
        # la primer biblia del listado
        biblia = biblioteca['contenido']
        # book :     'id' 'book_reference_id testament_reference_id  name 
        rvr1960=None
        for n in biblia:
            #REINA VALERA 1960
            if 'RVR1960' in n.path :
                # es el reina valera
                rvr1960 = n
                break
        Logger.info(f"la promesa:{ver_promesa}")
        # Ej: Juan 3:16
        # contenido = rnv1960.buscarVersiculo('JUAN',3,16)
        try:
            contenido = rvr1960.buscarVersiculo( *ver_promesa )
            if Fail : return contenido
        except Exception as e:
            # intentar de nuevo
            Logger.error(f"ERROR:{e}")
            contenido = self.get_promesa(Fail=True)
        
        # TODO: mejorar el jugador ira subiendo de nivel, a medida que memorice pasajes biblicos,
        # comprobar que las promesas no esten en sus memorias, asi ir quitandolas de esta seleccion.
        # hasta que solo quede 1 forzada Juan 3:16. que no apareca en el de bienvenida.
        return contenido


if __name__ == '__main__':
    Logger.setLevel(LOG_LEVELS["debug"])
    os.environ['KIVY_LOG_LEVEL'] = 'debug'
    GameApp().run()
