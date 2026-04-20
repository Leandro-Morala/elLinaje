from kivy.uix.screenmanager import Screen
from kivy.app import App 
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.utils import platform

from datetime import datetime
import sqlite3
import shutil
import os
from libs.backups.main import BackupEngine

class BaseScreen(Screen):
    """
    Clase base para todas las pantallas de la aplicación.
    Asegura que cada pantalla reciba la instancia del DataManager (DM)
    y lo almacene como self.DM. ( self.player ) para mayor practicidad.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self.ConfigFile = App.get_running_app().getModel('ConfigFile')
        self.user = App.get_running_app().getModel('UsuariosModel')
        Logger.info("carga de BaseScreen terminada...")
        
    def get_data(self,params):
        Logger.info(f'{self.name=}-->{params}')
        try:
            Logger.debug(f"obteniendo parametro{params=}"+"*"*30)
            texto = self.user.get_player_data(params)
            return texto
        except AttributeError as e :
            Logger.info(f"exeption error..{e}")
            return "--"

    def get_player_data_foto_perfil(self):
        self.get_data('foto_perfil')
        return 'images/default_profile.png'
        
    def get_player_data_nombre(self):
        # username del usuario
        usr=self.user.get_one(1)
        if usr:
            Logger.info(f"{usr['username']=}")
            usrnm=usr['username']
            return usrnm 
        return 'Null'
    
    def get_player_nivel(self):
        level = self.get_data('nivel')
        return level
        
    def uptdate_text(self,widget_id,texto):
        """
        Actualiza la propiedad 'text' de un widget Kivy identificado por su ID,
        solo si el ID está disponible en el diccionario self.ids.
        """
        if hasattr(self,ids,widget_id):
            #solo actualiza si el id del widget existe en el diccionario:
            try:
                self.ids[widget_id].text =str(texto)
            except Attribute:
                Logger.error(f"ERROR: El widget {widget_id} existe, pero no tiene la propiedad '.text'.")
        else:
            # esto como advertencia:
            Logger.error(f"ADVERTENCIA {ids=} NO ENCONTRADO O NO CARGADO TODAVIA.")

    ###############      MODAL POPAPS                             #######################
    def confirm_exit(self,texto, callback):
        # Lógica de confirmación ya existente corregida para cerrar sesión si se desea
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=texto))
        
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_si = Button(text="Sí, Salir", background_color=(0.8, 0.2, 0.2, 1))
        btn_no = Button(text="Cancelar")
        
        btns.add_widget(btn_si)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        
        popup = Popup(title="Confirmar", content=content, size_hint=(0.7, 0.3))
        btn_si.bind(on_release=lambda x: App.get_running_app().stop())
        btn_no.bind(on_release=popup.dismiss)
        popup.open()
        
    def echo(self, mensaje):
        texto=f"{mensaje}"
        # Lógica de confirmación ya existente corregida para cerrar sesión si se desea
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=texto))
        
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_no = Button(text="Cerrar")
        
        btns.add_widget(btn_no)
        content.add_widget(btns)
        
        popup = Popup(title="INFORMACION:", content=content, size_hint=(0.7, 0.3))
        # cerrar popap caso negativo
        btn_no.bind(on_release=popup.dismiss)
        # abrir popap
        popup.open()


    ########## seccion gestion de bases de datos ############################
    @mainthread
    def abrir_explorador(self, modo='export'):
        """Abre un modal para seleccionar dónde guardar o qué archivo cargar."""
        
        # --- SOLUCIÓN PARA PERMISOS ANDROID ---
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            def callback(permissions, results):
                if all(results):
                    self._crear_popup_explorador(modo)
                else:
                    self.echo("Permisos denegados para acceder a archivos")
            
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE
            ], callback)
        else:
            self._crear_popup_explorador(modo)
    
    @mainthread
    def _crear_popup_explorador(self, modo):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        file_chooser = FileChooserListView(
            path=os.path.expanduser("~"), 
            filters=['*.bin'] if modo == 'import' else []
        )
        
        content.add_widget(file_chooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_cancelar = Button(text="Cancelar")
        btn_accion = Button(
            text="Seleccionar" if modo == 'import' else "Guardar Aquí",
            background_color=(0.1, 0.5, 0.8, 1)
        )
        
        btn_layout.add_widget(btn_cancelar)
        btn_layout.add_widget(btn_accion)
        content.add_widget(btn_layout)

        self._popup = Popup(
            title="Seleccionar Archivo de Respaldo" if modo == 'import' else "Guardar Respaldo",
            content=content,
            size_hint=(0.9, 0.9)
        )

        btn_cancelar.bind(on_release=self._popup.dismiss)
        
        if modo == 'export':
            btn_accion.bind(on_release=lambda x: self.confirmar_exportacion(file_chooser.path))
        else:
            btn_accion.bind(on_release=lambda x: self.confirmar_importacion(file_chooser.selection))

        self._popup.open()

    def confirmar_exportacion(self, ruta_carpeta):
        """Paso intermedio para definir el nombre y contraseña antes de exportar."""
        self._popup.dismiss()
        # Aquí podrías abrir otro Popup pequeño pidiendo contraseña.
        # Por simplicidad, usaremos el password del usuario actual o uno fijo por ahora.
        nombre_archivo = os.path.join(ruta_carpeta, "respaldo_mercado.bin")
        password = self.ids.txt_file_pass.text.strip()
        
        if not password or len(password) < 8  : # contraseña corta
            self.echo("Error: Se requiere una contraseña  o una contraseña mayor a 8 caracteres")
            return

        exito, msg = self.engine.exportar(nombre_archivo, password)
        self.echo(msg)

    def confirmar_importacion(self, seleccion):
        """Procesa el archivo seleccionado para restaurar."""
        if not seleccion:
            self.echo("No se seleccionó ningún archivo.")
            return
            
        self._popup.dismiss()
        ruta_archivo = seleccion[0]
        password = self.ids.txt_user_pass.text.strip()

        if not password:
            self.echo("Ingrese la contraseña del backup en el campo de texto.")
            return

        exito, msg = self.engine.importar(ruta_archivo, password)
        if exito:
            self.echo("Restauración completa. Reinicie la aplicación.")
        else:
            self.echo(f"Error: {msg}")

    # --- Los métodos de tu archivo original que conectan con los botones del KV ---

    def ejecutar_exportar_seguro(self):
        # Este método se llamaría desde el botón 'EXPORTAR' del .kv
        self.abrir_explorador(modo='export')

    def ejecutar_importar_seguro(self):
        # Este método se llamaría desde el botón 'IMPORTAR' del .kv
        self.abrir_explorador(modo='import')


    def exportar_db(self):
        try:
            ruta = self.ids.txt_export_path.text.strip()
            if not ruta:
                self.echo("Indique ruta de exportación")
                return
            if not os.path.exists(os.path.dirname(ruta)) and os.path.dirname(ruta) != "":
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
            
            shutil.copy(self.db_path, ruta)
            self.echo(f"Base de datos exportada a: {ruta}")
        except Exception as e:
            self.echo(f"Error al exportar: {e}")

    def importar_db(self):
        try:
            ruta = self.ids.txt_import_path.text.strip()
            if not os.path.exists(ruta):
                self.echo("El archivo de origen no existe")
                return
            
            # Backup de la actual por seguridad antes de sobrescribir
            shutil.copy(self.db_path, self.db_path + ".bak")
            shutil.copy(ruta, self.db_path)
            self.echo("Base de datos importada correctamente")
        except Exception as e:
            self.echo(f"Error al importar: {e}")



