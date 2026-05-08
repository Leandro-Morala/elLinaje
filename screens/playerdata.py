from kivy.properties import StringProperty
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import mainthread, Clock
from kivy.uix.camera import Camera
from screens.basescreen import BaseScreen
import json
import os
import shutil

FOTO_DIR = os.path.join('data', 'img')
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
    player_name = StringProperty('')
    player_lastname = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._foto_seleccionada = None

    def on_enter(self, *args):
        foto = self.get_player_data_foto_perfil()
        try:
            self.ids.player_image.source = foto
            self.ids.player_image.reload()
        except Exception:
            pass

    def save_and_continue(self):
        
        usr = self.user.get_one(1)
        nombre = self.player_name if self.player_name else 'Hijo'
        apellido = self.player_lastname if self.player_lastname else 'de Dios'
        usrname = f"{nombre},\n{apellido}"
        if not usr :
            # no existe usuario, agregando nuevo usuario
            foto = self._foto_seleccionada or 'default.png'
            idusr=self.user.insertar( usrname ,  json.dumps({'nivel':0,'no_load':True,'foto_perfil': foto})   ) # asumo id=1
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
            foto = self._foto_seleccionada or 'default.png'
            tag={'nivel':0,'no_load':True,'foto_perfil': foto}
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
    def abrir_modal_foto(self):
        """Modal de selección: cámara o galería."""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content.add_widget(Label(
            text="¿Cómo querés elegir tu foto de perfil?",
            halign='center', size_hint_y=None, height=dp(40)
        ))

        btn_camara = Button(
            text="📷  Tomar selfie",
            size_hint_y=None, height=dp(55),
            background_normal='', background_color=(0.1, 0.5, 0.8, 1)
        )
        btn_galeria = Button(
            text="🖼  Elegir de la galería",
            size_hint_y=None, height=dp(55),
            background_normal='', background_color=(0.2, 0.6, 0.3, 1)
        )
        btn_cancelar = Button(
            text="Cancelar",
            size_hint_y=None, height=dp(45),
            background_normal='', background_color=(0.5, 0.5, 0.5, 1)
        )

        content.add_widget(btn_camara)
        content.add_widget(btn_galeria)
        content.add_widget(btn_cancelar)

        self._popup_foto = Popup(
            title="Foto de perfil",
            content=content,
            size_hint=(0.85, 0.55),
            auto_dismiss=False
        )
        btn_camara.bind(on_release=lambda x: [self._popup_foto.dismiss(), self._abrir_camara()])
        btn_galeria.bind(on_release=lambda x: [self._popup_foto.dismiss(), self._abrir_galeria()])
        btn_cancelar.bind(on_release=self._popup_foto.dismiss)
        self._popup_foto.open()

    # ── OPCIÓN 1: Cámara ────────────────────────────────────────────
    def _abrir_camara(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, check_permission, Permission
                if check_permission(Permission.CAMERA):
                    self._mostrar_popup_camara()
                else:
                    def _cb(perms, results):
                        if results and results[0]:
                            self._mostrar_popup_camara()
                        else:
                            Clock.schedule_once(lambda dt: self.echo("Permiso de cámara denegado."), 0)
                    request_permissions([Permission.CAMERA], _cb)
            except Exception as e:
                Logger.error(f"Permiso cámara: {e}")
                Clock.schedule_once(lambda dt: self.echo("Error al solicitar permiso de cámara."), 0)
        else:
            self._mostrar_popup_camara()

    @mainthread
    def _mostrar_popup_camara(self):
        try:
            self._camara_index = 0
            self._camara = Camera(index=self._camara_index, play=True, resolution=(640, 480))
            content = BoxLayout(orientation='vertical', spacing=dp(5))
            content.add_widget(self._camara)

            btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            btn_girar = Button(text="🔄 Girar", background_normal='',
                               background_color=(0.4, 0.4, 0.4, 1))
            btn_capturar = Button(text="📸 Capturar", background_normal='',
                                  background_color=(0.1, 0.5, 0.8, 1))
            btn_cerrar = Button(text="Cancelar", background_normal='',
                                background_color=(0.5, 0.2, 0.2, 1))
            btns.add_widget(btn_girar)
            btns.add_widget(btn_capturar)
            btns.add_widget(btn_cerrar)
            content.add_widget(btns)

            self._popup_camara = Popup(title="Selfie", content=content,
                                       size_hint=(0.95, 0.9), auto_dismiss=False)
            self._popup_camara.bind(on_dismiss=lambda x: self._detener_camara())
            btn_girar.bind(on_release=lambda x: self._girar_camara())
            btn_capturar.bind(on_release=lambda x: self._capturar_foto())
            btn_cerrar.bind(on_release=self._popup_camara.dismiss)
            self._popup_camara.open()
        except Exception as e:
            Logger.error(f"Error al abrir cámara: {e}")
            self.echo("No se pudo abrir la cámara.")

    def _girar_camara(self):
        try:
            content = self._popup_camara.content
            self._camara.play = False
            content.remove_widget(self._camara)
            self._camara_index = 1 - self._camara_index
            self._camara = Camera(index=self._camara_index, play=True, resolution=(640, 480))
            content.add_widget(self._camara, index=len(content.children))
        except Exception as e:
            Logger.error(f"Error al girar cámara: {e}")

    def _capturar_foto(self):
        try:
            os.makedirs(FOTO_DIR, exist_ok=True)
            ruta = os.path.join(FOTO_DIR, 'perfil.png')
            self._camara.texture.save(ruta, flipped=False)
            self._popup_camara.dismiss()
            self._aplicar_foto(ruta)
        except Exception as e:
            Logger.error(f"Error al capturar foto: {e}")
            self.echo("No se pudo guardar la foto.")

    def _detener_camara(self):
        try:
            if hasattr(self, '_camara') and self._camara:
                self._camara.play = False
                self._camara = None
        except Exception as e:
            Logger.error(f"Error al detener cámara: {e}")

    # ── OPCIÓN 2: Galería ────────────────────────────────────────────
    def _abrir_galeria(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, check_permission, Permission
                from jnius import autoclass
                sdk_int = autoclass('android.os.Build$VERSION').SDK_INT
                permiso = Permission.READ_MEDIA_IMAGES if sdk_int >= 33 else Permission.READ_EXTERNAL_STORAGE

                if check_permission(permiso):
                    self._mostrar_popup_galeria()
                else:
                    def _cb(perms, results):
                        if results and results[0]:
                            self._mostrar_popup_galeria()
                        else:
                            Clock.schedule_once(lambda dt: self.echo("Permiso de almacenamiento denegado."), 0)
                    request_permissions([permiso], _cb)
            except Exception as e:
                Logger.error(f"Permiso galería: {e}")
                self._mostrar_popup_galeria()
        else:
            self._mostrar_popup_galeria()

    @mainthread
    def _mostrar_popup_galeria(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                env = autoclass('android.os.Environment')
                dcim = env.getExternalStoragePublicDirectory(env.DIRECTORY_DCIM)
                if dcim and os.path.exists(dcim.getAbsolutePath()):
                    ruta_inicial = dcim.getAbsolutePath()
                else:
                    raise Exception("DCIM no accesible")
            except Exception:
                for candidato in ('/sdcard/DCIM', '/sdcard/Pictures', '/sdcard/Download', '/sdcard'):
                    if os.path.exists(candidato):
                        ruta_inicial = candidato
                        break
                else:
                    ruta_inicial = '/sdcard'
        else:
            ruta_inicial = os.path.expanduser('~')

        content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))
        fc = FileChooserListView(
            path=ruta_inicial,
            filters=['*.png', '*.jpg', '*.jpeg']
        )
        content.add_widget(fc)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_sel = Button(text="Seleccionar", background_normal='',
                         background_color=(0.2, 0.6, 0.3, 1))
        btn_cancelar = Button(text="Cancelar")
        btns.add_widget(btn_cancelar)
        btns.add_widget(btn_sel)
        content.add_widget(btns)

        popup = Popup(title="Elegir imagen", content=content,
                      size_hint=(0.95, 0.9), auto_dismiss=False)
        btn_cancelar.bind(on_release=popup.dismiss)
        btn_sel.bind(on_release=lambda x: self._seleccionar_imagen(fc.selection, popup))
        popup.open()

    def _seleccionar_imagen(self, seleccion, popup):
        if not seleccion:
            self.echo("No seleccionaste ninguna imagen.")
            return
        popup.dismiss()
        origen = seleccion[0]
        try:
            os.makedirs(FOTO_DIR, exist_ok=True)
            destino = os.path.join(FOTO_DIR, 'perfil' + os.path.splitext(origen)[1])
            shutil.copy(origen, destino)
            self._aplicar_foto(destino)
        except Exception as e:
            Logger.error(f"Error al copiar imagen: {e}")
            self.echo("No se pudo copiar la imagen.")

    # ── Aplicar foto al widget y guardar en DB ───────────────────────
    def _aplicar_foto(self, ruta):
        try:
            self.ids.player_image.source = ruta
            self.ids.player_image.reload()
            self._foto_seleccionada = ruta
            Logger.info(f"Foto de perfil actualizada: {ruta}")
            # actualizar pantalla principal si está activa
            try:
                main = self.manager.get_screen('main')
                main.imagen_perfil = ruta
            except Exception:
                pass
        except Exception as e:
            Logger.error(f"Error al aplicar foto: {e}")

    def skip(self):
        # Si presiona omitir, simplemente navega a la siguiente pantalla
        self.manager.current = 'faith_data'
