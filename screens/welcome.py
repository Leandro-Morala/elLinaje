# screens/welcome.py

from kivy.clock import Clock
# from kivy.lang import Builder
from screens.basescreen import BaseScreen # Importamos nuestra clase base
from screens.plantilla import RolloBiblico
from kivy.app import App
from kivy.logger import Logger
# se carga de forma automatica al inicio.
#Builder.load_file('kv_files/welcome.kv')
from kivy.factory import Factory
import random

# para usar el registro biblico
from db.bibliasestaticas import Reg

class WelcomeScreen(BaseScreen):
    
    def __init__(self, **kwargs):
        # Llama al constructor de BaseScreen para inicializar self.DM
        super().__init__(**kwargs)
        self.Biblioteca = App.get_running_app().getModel('Biblioteca')
        # Inicia el temporizador de 1.5 segundos cuando la pantalla es creada
        # Usamos on_pre_enter para iniciar justo antes de que se muestre, 
        # asegurando que se muestre por al menos un momento si la carga es rápida.
        self.bind(on_pre_enter=self.start_timer)

    def start_timer(self, *args):
        # Espera 1.5 segundos antes de llamar a go_next
        # Usamos Clock.schedule_once
        Clock.schedule_once(self.pergamino, 4.0)

    def go_next(self, dt):
        # La lógica para decidir a dónde ir después de la bienvenida.
        # Por ahora, vamos a la siguiente pantalla de configuración.
        usr = self.user.get_one(1) # obtener primer registro
        if not usr :
            self.manager.current = 'player_data'
        else:
            self.manager.current = 'main'
            
    
    def pergamino(self, dt):
        '''mostrar un pergamino y luego ir a main'''
        promesas=[
            ('Filipenses',4,19,50),    ('Jeremías',29,11,24),     ('2 Pedro',1,4,61),
            ('Isaías',41,10,23),       ('2 Corintios',1,20,47),   ('Juan',3,16,43),
            ('1 Juan',1,9,62),         ('Isaías',43,2,23),        ('Juan',14,27,43),
            ('Josué',23,146),          ('Isaías',40,31,23),       ('Romanos',8,28,45),
            ('2 Corintios',7,1,47),    ('Mateo',11,'28-29',40),   ('Santiago',1,15,59),
            ('Isaías',40,'26-31',23),  ('2 Pedro',3,9,61),        ('Deuteronomio',31,8,5),
            ('1 Corintios',10,13,46),  ('Jeremías',30,17,24),     ('Isaías',54,17,23),
            ('Romanos',6,23,45),       ('Romanos',10,9,45),       ('Éxodo',15,26,2),
            ('Apocalipsis',21,4,66),   ('Josué',1,9,6),           ('Apocalipsis',3,5,66),
            ('Isaías',26,3,23),        ('Romanos',8,32,45),       ('1 Reyes',8,56,11),
            ]
        r = random.Random()
        maximo = len(promesas)
        quien = int(r.random() * maximo)
        ver_promesa = promesas[quien]

        biblioteca = self.Biblioteca
        biblia = biblioteca['contenido']
        rvr1960 = None
        for n in biblia:
            if 'RVR1960' in n.path:
                rvr1960 = n
                break

        Logger.info(f"la promesa:{ver_promesa}")

        if rvr1960 is None:
            Logger.error("No se encontró la biblia RVR1960")
            self.go_next(1)
            return

        contenido = rvr1960.buscarVersiculo(*ver_promesa)
        Logger.info(f"{contenido=}" + "*"*30)

        if contenido and len(contenido) >= 1:
            popap = Factory.RolloBiblico()
            popap.cerrar = lambda: self.go_next(1)
            popap.mostrar_pasaje(0, contenido, lambda: self.go_next(1))
        else:
            Logger.error(f"error al buscar la promesa!!!  CONTENIDO NO ENCONTRADO!!!")
            self.go_next(1)
