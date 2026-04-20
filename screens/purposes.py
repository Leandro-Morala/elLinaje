from screens.basescreen import BaseScreen
from kivy.logger import Logger

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
    def on_enter(self):
        # Limpiar y recargar la tabla desde el DataManager
        self.ids.purposes_container.clear_widgets()
        data = self.player.get_all_propositos() # Asumiendo que tienes este método
        
        contador=0
        for item in data.values():
            # print(f"{item=}")
            row = PurposeRow(
                objetivo=str(contador) ,
                actualizacion=str(item['fecha_limite']),
                logros=str(item['completado']),
                ayuda_dios=str(item['ayudaDeDios']),
                id_registro=str(item['id']),
            )
            contador+=1
            # print(f"{item['descripcion']}") #,
            self.ids.purposes_container.add_widget(row)
