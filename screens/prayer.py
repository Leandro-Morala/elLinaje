from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger
from screens.basescreen import BaseScreen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from datetime import datetime, timedelta
import time

'''
        oraciones :
        
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('tiempo_inicio','','TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('tiempo_final','','TIMESTAMP'),
            ('tiempo_acumulado','user','DEFAULT \'user\'')
'''
class OracionesRow(ButtonBehavior, BoxLayout):
    # Definimos las propiedades que el KV usará
    tiempo_inicio = StringProperty('')
    TiempoOrado = StringProperty('')
    observaciones = StringProperty('')
    
    id_registro = StringProperty('') # Para saber qué registro editar
    tiempo_final = StringProperty('') # de la base de datos
    tiempo_acumulado = StringProperty('') # de la base de datos

    def set_funcion_goto_release(self,funcion):
        self.goto_funcion=funcion 
    
    def on_release(self):
        '''
            ejecutar el poppup de la funcion elegida
        '''
        self.goto_funcion(self.id_registro)
        
        
class PrayerScreen(BaseScreen):
    """
    Controla el sistema de oración. 
    Transforma tiempo real (segundos) en tiempo de "Efecto de Oración" (hasta 24hs).
    """
    
    timer_text = StringProperty("00:00:00")         # Tiempo de la sesión actual
    timer_total_text = StringProperty("00:00:00")   # Tiempo de "cobertura" restante
    inicio_sesion_texto = StringProperty("---")     # Fecha/Hora de inicio
    button_text = StringProperty("Iniciar Oración")
    is_praying = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prayer_event = None
        self.sesion_actual_segundos = 0
        self.timestamp_inicio_real = None
        self.Oraciones = App.get_running_app().getModel('OracionesModel')
        self.is_praying = False # por defecto creo que no esta orando
        #    self.prayer_event = None
        # la tabla se actualizara luego de cada modificacion
        self.actualizar_registros()
        
    #def on_enter(self):
    #    self.actualizar_reloj_restante(0)
    #    Clock.schedule_interval(self.actualizar_reloj_restante, 1)
    
    def on_enter(self):
        """Al entrar, calculamos cuánto tiempo de oración queda comparando con la DB."""
        app = App.get_running_app()
        if hasattr(app, 'global_is_praying') and app.global_is_praying:
            self.is_praying = True
            self.button_text = "Detener Oración"
            if app.global_timestamp_inicio:
                self.timestamp_inicio_real = app.global_timestamp_inicio
                self.inicio_sesion_texto = self.timestamp_inicio_real.strftime("%Y-%m-%d %H:%M:%S")
                diff = int(time.time() - app.global_timestamp_inicio.timestamp())
                self.sesion_actual_segundos = diff
                self.timer_text = str(timedelta(seconds=self.sesion_actual_segundos))
            if not self.prayer_event:
                self.prayer_event = Clock.schedule_interval(self.update_current_session, 1)
        else:
            self.is_praying = False

        self.actualizar_cobertura_restante()
        Clock.unschedule(self.actualizar_cobertura_restante)
        Clock.schedule_interval(self.actualizar_cobertura_restante, 1)
    
    def actualizar_registros(self):
        self.ids.oraciones_container.clear_widgets()
        
        data = self.Oraciones.obtener_todos(limit='10', orderby='id DESC')
        contador=0
        for item in data :
            tiempoTotal = item['tiempo_acumulado']
            row = OracionesRow(
                tiempo_inicio=str(item['tiempo_inicio']) ,
                TiempoOrado=str(tiempoTotal),
                observaciones=str('test'),
                id_registro=str(item['id'])
            )
            contador+=1
            row.set_funcion_goto_release(self.popup)
            
            self.ids.oraciones_container.add_widget(row)
    
    
    def popup(self,idregistro):
        Logger.debug(f"registro editado{idregistro}")
        # de esta manera se actualizan los registro de forma mas simple
        self.actualizar_registros()
        
        
    def on_leave(self):
        """
            Al salir, NO detenemos la oración real, solo el evento visual 
            para liberar recursos, pero mantenemos el estado en la App.
        """
        Clock.unschedule(self.actualizar_cobertura_restante)
        if self.prayer_event:
            Clock.unschedule(self.prayer_event)
            self.prayer_event = None
             


    def get_multiplicador(self):
        """
        Calcula cuánto vale 1 segundo de oración real en segundos de juego.
        Nivel 0: 5 min -> 24hs (Mult: 288)
        Nivel 100 (ej): 4 hs -> 24hs (Mult: 6)
        """
        nivel = self.get_data('nivel')
        if not nivel :
            nivel = 0
        mult = max(6, 288 - (nivel * 2.82)) 
        return mult

    def actualizar_cobertura_restante(self, *args):
        """
        Calcula la diferencia entre el 'final_oracion_timestamp' guardado y el ahora.
        """
        fechaFinOracion = self.user.get_tag(1, 'fecha_fin_oracion')
        if not fechaFinOracion:
            self.timer_total_text = "00:00:00"
            return

        try:
            fin_timestamp = float(fechaFinOracion)
            ahora = time.time()
            restante = fin_timestamp - ahora
            if restante <= 0:
                self.timer_total_text = "00:00:00"
            else:
                self.timer_total_text = str(timedelta(seconds=int(restante)))
        except Exception as e:
            Logger.error(f"Prayer: Error calculando cobertura: {e}")
            
    def start_stop_timer(self):
        app = App.get_running_app()
        if not self.is_praying:
            # --- INICIO DE SESIÓN ---
            self.is_praying = True
            app.global_is_praying = True # Guardar estado en la instancia de App
            self.button_text = "Detener Oración"
            self.sesion_actual_segundos = 0
            
            # Capturamos el inicio para mostrarlo o procesarlo luego
            ahora_dt = datetime.now()
            self.timestamp_inicio_real = ahora_dt
            app.global_timestamp_inicio = ahora_dt # Guardar timestamp en App
            self.inicio_sesion_texto = ahora_dt.strftime("%H:%M:%S")
            if not self.prayer_event:
                self.prayer_event = Clock.schedule_interval(self.update_current_session, 1)
        
        else:
            # --- DETENER ---
            self.is_praying = False
            app.global_is_praying = False
            self.button_text = "Iniciar Oración"
            if self.prayer_event:
                self.prayer_event.cancel()
                self.prayer_event = None
            
            self.aplicar_tiempo_orado()
            self.sesion_actual_segundos = 0
            self.timer_text = "00:00:00"
    
    def update_current_session(self, dt):
        """Cronómetro de la sesión actual."""
        self.sesion_actual_segundos += 1
        self.timer_text = str(timedelta(seconds=self.sesion_actual_segundos))

    def aplicar_tiempo_orado(self):
        """Convierte el tiempo orado en 'cobertura' y lo suma a la fecha fin en la DB."""
        mult = self.get_multiplicador()
        segundos_ganados = self.sesion_actual_segundos * mult

        tiempo_inicial_str = self.timestamp_inicio_real.strftime("%Y-%m-%d %H:%M:%S")
        Logger.info(f"[Prayer] Sesión iniciada el {tiempo_inicial_str} ha terminado."+'*'*30)

        # Leer directamente con get_tag para evitar doble conexión SQLite en Android
        ultima_fin_raw = self.user.get_tag(1, "fecha_fin_oracion")
        Logger.info(f"[Prayer] ultima_fin_raw leída={ultima_fin_raw!r}")
        ahora_unix = time.time()

        try:
            ultima_fin = float(ultima_fin_raw) if ultima_fin_raw else ahora_unix
        except (ValueError, TypeError):
            ultima_fin = ahora_unix

        base_inicio = max(ahora_unix, ultima_fin)
        nueva_fin = base_inicio + segundos_ganados

        # Límite de 24 horas
        max_futuro = ahora_unix + 86400
        if nueva_fin > max_futuro:
            nueva_fin = max_futuro

        Logger.info(f"[Prayer] base={base_inicio:.0f} ganados={segundos_ganados:.0f}s nueva_fin={nueva_fin:.0f}")
        self.user.set_tag(1, "fecha_fin_oracion", int(nueva_fin))

        tiempo_acumulado = self.sesion_actual_segundos
        self.Oraciones.insertar(tiempo_inicial_str, nueva_fin, tiempo_acumulado)

        Logger.info(f"[Prayer] Ganados {segundos_ganados}s de cobertura (Mult: {mult})")
        self.actualizar_cobertura_restante()

'''    
    def actualizar_reloj_restante(self, dt):
        player_data = self.p
        
        # 1. Obtenemos la fecha de la última oración (debe estar guardada como string ISO o timestamp)
        # Ejemplo: "2023-10-27 10:00:00"
        # last_prayer_str = player_data.get('ultima_oracion_fecha', None)
        last_prayer_str = player_data.get('ultima_oracion', None)
        
        if not last_prayer_str:
            self.tiempo_restante_str = "00:00:00"
            return



                    
    def start_stop_timer(self):
        
        if not self.is_praying:
            self.is_praying = True
            self.button_text = "Detener Oración" 
            # Iniciar el contador, actualizando cada 1 segundo
            self.prayer_event = Clock.schedule_interval(self.update_timer, 0.1)
        else:
            self.is_praying = False
            self.button_text = "Iniciar Oración"
            self.prayer_event.cancel()
            # Guardar el tiempo orado y resetear
            self.player.add_oracion_time(self.cronometro_time) 
            self.cronometro_time = 0 
            self.timer_text = "00:00:00"

    def update_timer(self, dt):
        """Aumenta el tiempo del cronómetro y actualiza la UI."""
        self.cronometro_time += dt 
        seconds = int(self.cronometro_time)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.timer_text = f"{h:02d}:{m:02d}:{s:03d}"
        
'''
