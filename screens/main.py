from kivy.properties import StringProperty, NumericProperty
from screens.basescreen import BaseScreen
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock

from datetime import datetime
import time

class ClickableImage(ButtonBehavior, Image):
    # La clase hereda las propiedades de Image (dibujar la imagen)
    # y las propiedades de ButtonBehavior (responder a on_press/on_release)
    def __init__(self, **kw):
        super().__init__(**kw)
        self.user = App.get_running_app().getModel('UsuariosModel')
        self._id_ = -1 # ID del usuario
        

    def clickerimg(self):
        #al hacer click en la imagen
        Logger.info("click de imagen")
        # app.root.current = 'player_data'
        try:
            app = App.get_running_app()
            screen_manager = app.root 
            # 2. Cambiar de pantalla (ejemplo: ir a 'player_data')
            screen_manager.current = 'player_data'
        except AttributeError as e:
            Logger.error(f"Error: {e}")
            

#
class MainScreen(BaseScreen):
    """Pantalla principal con el estado del jugador y navegación."""
    
    # Propiedades para enlazar con la UI
    player_name = StringProperty("Jugador,\nCristiano")
    nivel_label = StringProperty("Nivel: 0")
    power_value = NumericProperty(0)
    power_max = NumericProperty(24 * 3600)
    power_text = StringProperty("0h 00m 00s")
    imagen_perfil   = StringProperty("")
    
    def __init__(self, **kwargs):
        # esto esta en BaseScreen!!
        super().__init__(**kwargs)
        self.is_downtime=False
        self.power_max = 84600  # 24hs en segundos
        self._save_data_=60
        # self.bind(on_pre_enter=self.start_timer)
        
    def on_enter(self, *args):
        # solo una vez. al entrar se actualiza desde la base de datos
        potencia = self.actualizar_cobertura_restante()
        Logger.info(f"{potencia=}")
        self.power_value = potencia
        # solo cuando se ingresa se actualiza el estado..
        self.update_ui()
        
    def update_timer(self, dt):
        consumo_por_segundo = 0.0011574
        poder = self.power_value
        if self.power_value > 0:
            poder -= (consumo_por_segundo *dt )
        else:
            poder=0
            #deter ejecucion... no hay mas poder de oracion..
            self.event_clock.cancel()
        #print(f"down...{poder=}")
        self.power_value = poder
        self._save_data_ -= 1
        if self._save_data_ == 0 :
            # guardar datos cada x cantidad de tiempo
            self.set_actualizar_timer_db()
            # reiniciar el contador de segundos
            self._save_data_ = 60
            
    def start(self):
        #ejecutar update_time 1 vez por segundo
        self.event_clock = Clock.schedule_interval(self.update_timer, 1)
    
    def updateplayer(self):
        nombre = self.get_player_data_nombre()
        Logger.debug(f"{nombre}" )
        self.player_name = nombre
        self.nivel_label = "NIVEL:" + str( self.get_player_nivel() )
        
    def update_ui(self):
        self.updateplayer()
        self.start()
    
    def clickerimg(self):
        scree_manager=self.screen.get_running_app()
        scree_manager.current='playerdata'
        
    def format_time(self, seconds):
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}h {m:02d}m {s:02d}s"
    
    def actualizar_cobertura_restante(self, *args):
        """
        Calcula la diferencia entre el 'final_oracion_timestamp' guardado y el ahora.
        Esto resuelve el problema de cerrar y abrir la app.
        """
        tiempoFinOracion = self.get_data('fecha_fin_oracion')
        if not tiempoFinOracion :
            return 0

        try:
            # fecha_fin_oracion debe guardarse como un timestamp (float) para mayor facilidad
            fin_timestamp = float(tiempoFinOracion)
            ahora = time.time()
            
            restante = tiempoFinOracion - ahora
            
            if restante <= 0:
                return 0
            else:
                # Formatear seconds = restante
                Logger.info(f"valor devuelto ::: {restante=}" )       # -----------------------------------------
                return int(restante)
        except Exception as e:
            Logger.error(f"Prayer: Error calculando cobertura: {e}")
            return 0
    
    def set_actualizar_timer_db(self):
        """
            Guardar en la base de datos el nuevo tiemo consumido, esto se hace cada 5 minutos de forma automatica
        """
        tiempo = time.time() + int( self.power_value )
        Logger.info(f"actualizando valor en base de datos...{tiempo=}")
        self.user.set_tag(1,'fecha_fin_oracion',int(tiempo) )
        
        
    def check_propositos(self, propositos):
        hoy = datetime.now().date()
        for p in propositos:
            if not p['completado']:
                try:
                    fecha_limite = datetime.strptime(p['fecha_limite'], '%Y-%m-%d').date()
                    diferencia = (fecha_limite - hoy).days
                    if diferencia <= 7 and diferencia >= 0:
                        return f"¡Propósito '{p['descripcion'][:20]}...' vence en {diferencia} días!"
                except ValueError:
                    continue # Ignorar formatos de fecha inválidos
        return "No hay objetivos cercanos."
