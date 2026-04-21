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
    nivel_estrellas = StringProperty("")
    nivel_valor = NumericProperty(0)
    power_value = NumericProperty(0)
    power_max = NumericProperty(24 * 3600)
    power_text = StringProperty("0h 00m 00s")
    imagen_perfil = StringProperty("")
    fecha_hora_text = StringProperty("")
    
    def __init__(self, **kwargs):
        # esto esta en BaseScreen!!
        super().__init__(**kwargs)
        self.is_downtime=False
        self.power_max = 84600  # 24hs en segundos
        self._save_data_=60
        # self.bind(on_pre_enter=self.start_timer)
        
    def on_enter(self, *args):
        potencia = self.actualizar_cobertura_restante()
        Logger.info(f"{potencia=}")
        self.power_value = potencia
        self.update_ui()

    def on_leave(self, *args):
        if hasattr(self, 'event_clock') and self.event_clock:
            self.event_clock.cancel()
            self.event_clock = None
        Clock.unschedule(self.update_fecha_hora)
        
    def update_fecha_hora(self, dt):
        self.fecha_hora_text = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")

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
        h = int(poder) // 3600
        m = (int(poder) % 3600) // 60
        self.power_text = f"{h}h {m:02d}m"
        self._save_data_ -= 1
        if self._save_data_ == 0 :
            # guardar datos cada x cantidad de tiempo
            self.set_actualizar_timer_db()
            # reiniciar el contador de segundos
            self._save_data_ = 60
            
    def start(self):
        if hasattr(self, 'event_clock') and self.event_clock:
            self.event_clock.cancel()
        self.event_clock = Clock.schedule_interval(self.update_timer, 1)
        self.update_fecha_hora(0)
        Clock.unschedule(self.update_fecha_hora)
        Clock.schedule_interval(self.update_fecha_hora, 1)
    
    def updateplayer(self):
        nombre = self.get_player_data_nombre()
        Logger.debug(f"{nombre}")
        self.player_name = nombre.replace('\n', ' ') if nombre else "Jugador"
        nivel = self.get_player_nivel() or 0
        self.nivel_label = f"Nivel  {nivel}"
        self.nivel_valor = min(int(nivel), 50)
        
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
        """
        fin_raw = self.user.get_tag(1, 'fecha_fin_oracion')
        Logger.info(f"[Main] actualizar_cobertura fin_raw={fin_raw!r}")
        if not fin_raw:
            return 0

        try:
            fin_timestamp = float(fin_raw)
            ahora = time.time()
            restante = fin_timestamp - ahora
            if restante <= 0:
                return 0
            Logger.info(f"[Main] restante={restante:.0f}s")
            return int(restante)
        except Exception as e:
            Logger.error(f"[Main] Error calculando cobertura: {e}")
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
