#from kivy.uix.screenmanager import Screen
# from kivy.lang import Builder
from kivy.app import App
from datetime import datetime
from screens.basescreen import BaseScreen
from kivy.properties import ListProperty

# esta incluido en self.player
# DM = DataManager() 

# se carga de forma automatica al inicio
#Builder.load_file('kv_files/work.kv')
'''
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('tiempo_inicio','','TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('tiempo_final','','TIMESTAMP'),
            ('tiempo_acumulado','','TIMESTAMP'),
            ('objservaciones','','TEXT'),
            ('tags','','TEXT'),
            
'''
class WorkScreen(BaseScreen):
    """Pantalla de trabajo en la iglesia: Histórico manual."""
    history_data = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trabajo=App.get_running_app().getModel('TrabajosModel')
        
    def on_enter(self):
        load_history()
        
    def load_history(self):
        """
            actualizar lista historicos
        """
        # Asegúrate de que el DataManager tenga una clave 'trabajo_historico'
        Logger.info(f"load_history.")
        # Formatear los datos para el RecycleView:
        # El RecycleView espera una lista de diccionarios, donde cada diccionario
        # contiene las claves usadas en la plantilla (<WorkHistoryItem>).
        trabajos = self.trabajo.obtener_todos()
        formatted_data = []
        for index, registro in enumerate(trabajos):
            formatted_data.append({
                'item_index': index, # Clave requerida para identificar la fila
                'start_time': registro['tiempo_inicio'],
                'end_time': registro['tiempo_final'],
                'observation': registro['objservaciones'],
                # Las propiedades que no definimos en la plantilla (ej. 'text') se ignoran.
            })
            Logger.info(f"datos={formatted_data=}")
        
        Logger.info(f"DEBUG: Registros formateados ({len(formatted_data)}): {formatted_data[:2]}")
        # Esto notifica a Kivy que la lista ha cambiado y debe redibujar
        self.history_data = formatted_data
        
    def add_manual_registro(self, start_str, end_str, observation):
        '''
            llama a la logca para guardar historiales de trabajo
        '''
        # Llama a la lógica anterior para guardar
        # self.player.add_manual_registro(start_str, end_str, observation) # Llama a la versión de BaseScreen si existe
        
        
        # Lógica de guardado (usando la versión de work.py anterior)
        try:
            # Validación de fechas (asumimos que la validación sigue en esta función)
            inicio = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
            fin = datetime.strptime(end_str, '%Y-%m-%d %H:%M')
            acumulado = fin - inicio
            
            if fin <= inicio:
                Logger.info("Error: La fecha de fin debe ser posterior a la de inicio. formato: año - mes - dia espcio hora : minuto")
                return 
            # insertar(tiempo_inicio, tiempo_final, tiempo_acumulado , observaciones, tags)
            self.trabajo.insert( tiempo_inicio=start_str, tiempo_final=end_str,  tiempo_acumulado = acumulado.seconds ,  observaciones = observation,  tags ='{}'  )
                
            
        except ValueError:
            print("Error en el formato de fecha/hora. Usa YYYY-MM-DD HH:MM.")


    # --- MÉTODOS PARA EDITAR Y ELIMINAR (NUEVOS) ---
    def remove_item(self, index_to_remove):
        """Elimina un registro basado en su índice en la lista de datos formateados."""
        # Importante: El índice aquí es el índice en formatted_data,
        # que debería coincidir con el índice en self.player.data['trabajo_historico']
        
        if 0 <= index_to_remove < len(self.player.data['trabajo_historico']):
            # 1. Eliminar del DataManager
            #del self.player.data['trabajo_historico'][index_to_remove]
            #self.player.save_data()
            Logger.info(f"Prueba de indice para remover {index_to_remove} ")
            
            # 2. Refrescar la vista
            self.load_history()
        else:
            Logger.info(f"Error: Índice {index_to_remove} fuera de rango.")

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
