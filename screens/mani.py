#from kivy.uix.screenmanager import Screen
# from kivy.lang import Builder
# from data_manager import DataManager
from datetime import datetime
from screens.basescreen import BaseScreen
from kivy.properties import ListProperty

# esta incluido en self.player
# DM = DataManager() 

# se carga de forma automatica al inicio
#Builder.load_file('kv_files/work.kv')

class ManiScreen(BaseScreen):
    """Pantalla de trabajo en la iglesia: Histórico manual."""
    history_mn_data = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        
    '''
    version anterior de esta funcion.
    def add_manual_registro(self, start_date_str, end_date_str, observation):
        try:
            inicio = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')
            fin = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')
            
            if fin <= inicio:
                print("Error: La fecha de fin debe ser posterior a la de inicio.")
                return 
                
            self.player.data['trabajo_historico'].append({
                'inicio': start_date_str,
                'fin': end_date_str,
                'observacion': observation
            })
            self.player.save_data()
            print("Registro de trabajo añadido con éxito.")
            
        except ValueError:
            print("Error en el formato de fecha/hora. Usa YYYY-MM-DD HH:MM.")
    '''
    def load_history(self):
        """Carga los datos del DataManager y actualiza la propiedad history_data."""
        # Asegúrate de que el DataManager tenga una clave 'trabajo_historico'
        
        historico_bruto = self.player.data_get('trabajo_historico', [])
        print(f"load_history....{historico_bruto=}")
        # Formatear los datos para el RecycleView:
        # El RecycleView espera una lista de diccionarios, donde cada diccionario
        # contiene las claves usadas en la plantilla (<WorkHistoryItem>).
        
        formatted_data = []
        for index, registro in enumerate(historico_bruto):
            formatted_data.append({
                'item_index': index, # Clave requerida para identificar la fila
                'start_time': registro['inicio'],
                'end_time': registro['fin'],
                'observation': registro['observacion'],
                # Las propiedades que no definimos en la plantilla (ej. 'text') se ignoran.
            })
            print(f"datos={formatted_data=}")
        
        print(f"DEBUG: Registros formateados ({len(formatted_data)}): {formatted_data[:2]}")
        # Esto notifica a Kivy que la lista ha cambiado y debe redibujar
        self.history_dataS = formatted_data
        
    def add_manual_registro(self, start_str, end_str, observation):
        # Llama a la lógica anterior para guardar
        self.player.add_manual_registro(start_str, end_str, observation) # Llama a la versión de BaseScreen si existe
        
        # Lógica de guardado (usando la versión de work.py anterior)
        try:
            # Validación de fechas (asumimos que la validación sigue en esta función)
            inicio = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
            fin = datetime.strptime(end_str, '%Y-%m-%d %H:%M')
            
            if fin <= inicio:
                print("Error: La fecha de fin debe ser posterior a la de inicio.")
                return 
                
            self.player.data['trabajo_historico'].append({
                'inicio': start_str,
                'fin': end_str,
                'observacion': observation
            })
            self.player.save_data()
            print("Registro de trabajo añadido con éxito.")
            
            # Vuelve a cargar la lista para actualizar la vista
            self.load_history()
            
        except ValueError:
            print("Error en el formato de fecha/hora. Usa YYYY-MM-DD HH:MM.")


    # --- MÉTODOS PARA EDITAR Y ELIMINAR (NUEVOS) ---

    def remove_item(self, index_to_remove):
        """Elimina un registro basado en su índice en la lista de datos formateados."""
        
        # Importante: El índice aquí es el índice en formatted_data,
        # que debería coincidir con el índice en self.player.data['trabajo_historico']
        
        if 0 <= index_to_remove < len(self.player.data['trabajo_historico']):
            
            # 1. Eliminar del DataManager
            del self.player.data['trabajo_historico'][index_to_remove]
            self.player.save_data()
            print(f"Registro en el índice {index_to_remove} eliminado.")
            
            # 2. Refrescar la vista
            self.load_history()
        else:
            print(f"Error: Índice {index_to_remove} fuera de rango.")

    def edit_item(self, index_to_edit):
        """
        Lógica para editar. Esto generalmente implica cargar los datos 
        de ese índice en los TextInput superiores y quizás cambiar el botón 
        de "Agregar" a "Guardar Cambios".
        """
        print(f"LÓGICA DE EDICIÓN: Preparando para editar el índice {index_to_edit}")
        
        registro = self.player.data['trabajo_historico'][index_to_edit]
        
        # Cargar los datos antiguos en los campos de entrada para edición
        self.ids.start_time_input.text = registro['inicio']
        self.ids.end_time_input.text = registro['fin']
        self.ids.obs_input.text = registro['observacion']
        
        # **PENDIENTE:** Debes implementar lógica para cambiar el botón
        # de 'Agregar' a 'Guardar Cambios' y pasarle el índice a editar.
