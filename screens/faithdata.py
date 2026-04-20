# screens/faithdata.py

#from kivy.lang import Builder
from screens.basescreen import BaseScreen

# se carga de forma automatica al inicio.
# Builder.load_file('kv_files/faithdata.kv')
#

class FaithDataScreen(BaseScreen):
    
    def complete_registration(self):
        # 1. Recuperar el estado de los CheckBoxes si es necesario para el juego
        # Nota: Aquí no guardaremos esta información, como pediste.
        
        # Si quisieras usarlo temporalmente:
        # accepted = self.ids.accepted_christ.active
        # baptized = self.ids.baptized.active
        
        # 2. Navegar a la pantalla principal del juego
        self.manager.current = 'main'
        
        # Opcional: Forzar la primera actualización de la pantalla 'main'
        # main_screen = self.manager.get_screen('main')
        # main_screen.update_ui()
