import os
import zipfile
from kivy.lang import Builder
from kivy.utils import platform
from screens.basescreen import BaseScreen
from datetime import datetime

from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView # O FileChooserIconView para iconos
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.logger import Logger
from kivy.app import App
from screens.plantilla import RolloBiblico
from kivy.factory import Factory
import random

# para usar el registro biblico
from db.bibliasestaticas import Reg
# Builder.load_file('kv_files/config.kv')

class ConfigScreen(BaseScreen):
    
    def __init__(self, **kwargs):
        # Llama al constructor de BaseScreen para inicializar self.DM
        super().__init__(**kwargs)
        self.Biblioteca = App.get_running_app().getModel('Biblioteca')
        
    def go_to_profile_edit(self):
        """Navega a la pantalla de datos para editar perfil."""
        self.manager.current = 'player_data'

    def export_data(self):
        """Comprime la base de datos y recursos en un .zip."""
        try:
            # Nombre del archivo con fecha
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"backup_linaje_{timestamp}.zip"
            
            # Ruta de destino (usamos descargas o documentos)
            path_to_save = os.path.join(os.path.expanduser("~"), zip_name)

            with zipfile.ZipFile(path_to_save, 'w') as zipf:
                # 1. Comprimir la Base de Datos
                # Asumo que self.DM.db_path tiene la ruta al archivo .db
                db_file = "player_data.db" # Cambia al nombre real de tu archivo
                if os.path.exists(db_file):
                    zipf.write(db_file, arcname=db_file)
                
                # 2. Comprimir carpeta de imágenes si existe
                img_dir = 'images/'
                if os.path.exists(img_dir):
                    for root, dirs, files in os.walk(img_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file))

            print(f"Copia de seguridad creada en: {path_to_save}")
            # Aquí podrías mostrar un Popup de éxito
        except Exception as e:
            print(f"Error al exportar: {e}")
    
    def get_android_external_path(self):
        """
        Retorna la ruta segura para navegar en Android.
        En PC retorna el Home del usuario.
        """
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            # Pedimos permisos (esto debería hacerse al iniciar la app o la pantalla)
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            
            # Ruta común en Android para documentos/descargas
            from android.storage import primary_external_storage_path
            return primary_external_storage_path()
        else:
            # En Windows/Linux/Mac usamos la carpeta personal
            return os.path.expanduser("~")
    
    def import_data(self):
        """Abre un explorador para seleccionar un .zip y restaurar."""
        
        filechooser.open_file(
            title="Seleccionar Backup",
            filters=[("Archivos ZIP", "*.zip")],
            on_selection=self._handle_import
        )

    def _handle_import(self, selection):
        if not selection:
            return
            
        zip_path = selection[0]
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(".") # Extrae en la carpeta raíz
            
            # RECARGAR DATOS: Muy importante para que el juego vea los cambios
            self.DM.load_data() 
            print("Datos restaurados con éxito. Reinicia la app si es necesario.")
        except Exception as e:
            print(f"Error al importar: {e}")

    def go_next(self,to):
        pass
        
    def openbible(self):
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
        
        biblioteca = self.Biblioteca
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
        # Juan 3:16
        # contenido = rnv1960.buscarVersiculo('JUAN',3,16)
        contenido = rvr1960.buscarVersiculo( *ver_promesa )
        # para probar como funciona:
        Logger.info(f"{contenido=}"+"*"*30)
        if len(contenido) == 1:
            Logger.info("pasa por aqui")
            """
                existe la posiblidad de que tena 1 o mas registros...
                
                muestro el primero y dejo los otros a discrecion.
            """ 
            Reg = contenido[0]
            libro=Reg.nameBook
            capitulo = Reg.chapter
            versiculo = Reg.verse
            texto = Reg.text
            Logger.info(f"mostrare:{libro},{capitulo},{versiculo},{texto}")
        popap =  Factory.RolloBiblico()
        # popap.cerrar = lambda : self.go_next(1)        
        #popap.mostrar_pasaje( libro ,capitulo,versiculo, texto , total_versiculos=50)
        popap.mostrar_pasaje( 0, contenido , lambda : self.go_next(1) )
        
# ... dentro de tu clase ConfigScreen ...

    def open_file_manager(self, mode='export'):
        """Abre el explorador de archivos interno de Kivy."""
        content = BoxLayout(orientation='vertical')
        externalPath=self.get_android_external_path()
        # El widget de Kivy para explorar archivos
        file_chooser = FileChooserListView(
            path=externalPath , # iniciar en el path conveniente
            filters=['*.zip'] if mode == 'import' else [] # Filtra si es para importar
        )
        
        content.add_widget(file_chooser)

        # Botones inferiores del Popup
        buttons = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
        btn_cancel = Button(text='Cancelar', on_release=lambda x: self._popup.dismiss())
        
        # Botón de acción (Cargar o Guardar)
        action_text = 'Seleccionar' if mode == 'import' else 'Guardar aquí'
        btn_action = Button(text=action_text, background_color=(0.1, 0.6, 0.3, 1))
        
        # Definimos qué pasa al confirmar
        if mode == 'import':
            btn_action.bind(on_release=lambda x: self._process_import(file_chooser.selection))
        else:
            btn_action.bind(on_release=lambda x: self._process_export(file_chooser.path))

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_action)
        content.add_widget(buttons)

        # Crear y abrir el Popup
        self._popup = Popup(title="Explorador de Archivos", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def _process_import(self, selection):
        if selection:
            # selection es una lista con la ruta completa
            self._popup.dismiss()
            # Aquí llamas a tu lógica de descompresión
            print(f"Importando desde: {selection[0]}")
            # self.import_data_logic(selection[0])

    def _process_export(self, path):
        self._popup.dismiss()
        print(f"Exportando backup en la carpeta: {path}")
        # Aquí llamas a tu lógica de creación de ZIP
        # self.export_data_logic(path)
