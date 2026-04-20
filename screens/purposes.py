from screens.basescreen import BaseScreen
from kivy.logger import Logger
from kivy.app import App

from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

# print("PurposesScreen pasa por aqui...")
class PurposeRow(ButtonBehavior, BoxLayout):
    # Definimos las propiedades que el KV usará
    objetivo = StringProperty('')
    actualizacion = StringProperty('')
    logros = StringProperty('')
    ayuda_dios = StringProperty('')
    id_registro = StringProperty('') # Para saber qué registro editar
    
    def set_funcion_goto_release(self,funcion):
        self.goto_funcion=funcion
        
    def on_release(self):
        # Al tocar la fila, viajamos a la pantalla de edición
        # pasándole el ID o los datos necesarios.
        app = App.get_running_app()
        edit_screen = app.root.get_screen('purpose_edit')
        edit_screen.load_purpose_data(self.id_registro) # Método que tendrías que crear
        app.root.current = 'purpose_edit'
        
class PurposesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proposito = App.get_running_app().getModel('PropositoModel')

    def on_enter(self):
        self.ids.purposes_container.clear_widgets()
        data = self.proposito.obtener_todos() or []

        for item in data:
            row = PurposeRow(
                objetivo=str(item['proposito']),
                actualizacion=str(item['fecha_creacion']),
                logros=str(item['objetivo']),
                ayuda_dios='',
                id_registro=str(item['id']),
            )
            self.ids.purposes_container.add_widget(row)
