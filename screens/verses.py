#from kivy.uix.screenmanager import Screen
#from kivy.lang import Builder

from datetime import datetime
import random
from kivy.properties import StringProperty, ListProperty
from screens.basescreen import BaseScreen

# esta incluido en self.player
#DM = DataManager() 

# se carga de forma automatica al inicio.
# Carga el archivo .kv específico
#Builder.load_file('kv_files/verses.kv')

class VersesScreen(BaseScreen):
    """Pantalla de versículos: Agregar, Listar y Partida de Refuerzo."""
    
    # Propiedades para la partida
    verse_count = StringProperty("Versículos almacenados: 0")
    game_status = StringProperty("Listo para iniciar la partida.")
    

    def on_enter(self, *args):
        """Actualiza el contador al entrar a la pantalla."""
        self.update_verse_count()

    def update_verse_count(self):
        """Actualiza la propiedad con la cantidad actual de versículos."""
        count = len(self.player.data_get('versiculos', {}))
        self.verse_count = f"Versículos almacenados: {count}"
    
    def add_verse(self,libro, capitulo,verse_num_input , text_input ):
        ok=self.player.add_verse(libro,capitulo,verse_num_input,text_input )
        if ok[0]:
            self.ids.status_add.text = f"✅ versiculo agregado."
            self.ids.book_input.text = ''
            self.ids.chapter_input.text = ''
            self.ids.verse_num_input.text = ''
            self.ids.text_input.text = ''
        else:
            error=ok[1]
            self.ids.status_add.text = f"❌ Error:{error}"
        self.update_verse_count()
            
            
    def iniciar_partida(self):
        """Selecciona un versículo y configura las opciones de juego."""
        versiculos = self.player.data_get('versiculos', {})
        #if len(versiculos) < 5:
        #    self.game_status = "Necesitas al menos 5 versículos para iniciar la partida."
        #    return
        
        # 1. Seleccionar el versiculo mas antiguo para la partida.
        self.current_verse_key = random.choice(list(versiculos.keys()))
        self.current_verse = versiculos[self.current_verse_key]
        
        # 2. Configurar las preguntas
        self.partida_etapa = 1 # 1: Libro, 2: Capítulo, 3: Versículo
        self.ids.game_text.text = f"¿De qué libro es este versículo?\n\n'{self.current_verse['texto']}'"
        
        # 3. Generar 3 opciones incorrectas para el libro
        opciones_incorrectas = random.sample([
            l for l in self.libros_biblia if l != self.current_verse['libro']
        ], 3)
        
        # Opciones totales para la pregunta 1 (Libro)
        opciones_libro = opciones_incorrectas + [self.current_verse['libro']]
        random.shuffle(opciones_libro)
        
        # Mostrar opciones de juego
        self.ids.game_layout.clear_widgets()
        for i, opcion in enumerate(opciones_libro):
            btn = self.create_game_button(opcion, i)
            self.ids.game_layout.add_widget(btn)

        self.game_status = "Etapa 1: Elige el Libro."

    def create_game_button(self, text, index):
        """Crea un botón para las opciones del juego."""
        from kivy.uix.button import Button
        return Button(
            text=text, 
            on_release=lambda btn: self.responder_partida(btn.text)
        )

    def responder_partida(self, respuesta):
        """Maneja la respuesta del jugador en cada etapa."""
        
        if not hasattr(self, 'current_verse'):
            return # Juego no iniciado
            
        correcta = False
        
        if self.partida_etapa == 1: # Pregunta: Libro
            if respuesta == self.current_verse['libro']:
                correcta = True
                self.partida_etapa = 2
                self.game_status = "¡Correcto! Etapa 2: ¿Cuál es el Capítulo?"
                self.preparar_etapa_capitulo()
            else:
                self.finalizar_partida(False, f"Fallaste el Libro. Era {self.current_verse['libro']}.")
                
        elif self.partida_etapa == 2: # Pregunta: Capítulo
            # Simplificado: asume que la respuesta es un número
            try:
                if int(respuesta) == self.current_verse['capitulo']:
                    correcta = True
                    self.partida_etapa = 3
                    self.game_status = "¡Correcto! Etapa 3: ¿Cuál es el Versículo?"
                    self.preparar_etapa_versiculo()
                else:
                    self.finalizar_partida(False, f"Fallaste el Capítulo. Era {self.current_verse['capitulo']}.")
            except ValueError:
                 self.finalizar_partida(False, "Respuesta inválida para Capítulo.")

        elif self.partida_etapa == 3: # Pregunta: Versículo
            # Simplificado: asume que la respuesta es un número
            try:
                if int(respuesta) == self.current_verse['versiculo']:
                    correcta = True
                    self.finalizar_partida(True, "¡Victoria! Has reforzado este versículo.")
                else:
                    self.finalizar_partida(False, f"Fallaste el Versículo. Era {self.current_verse['versiculo']}.")
            except ValueError:
                 self.finalizar_partida(False, "Respuesta inválida para Versículo.")

    def preparar_etapa_capitulo(self):
        """Prepara las opciones para la pregunta del capítulo (input de texto)."""
        self.ids.game_layout.clear_widgets()
        
        from kivy.uix.textinput import TextInput
        self.ids.game_layout.add_widget(TextInput(
            id='chapter_game_input',
            hint_text='Ingresa el número del Capítulo',
            multiline=False,
            size_hint_y=0.7
        ))
        
        from kivy.uix.button import Button
        self.ids.game_layout.add_widget(Button(
            text='Responder Capítulo',
            size_hint_y=0.3,
            on_release=lambda btn: self.responder_partida(self.ids.game_layout.children[1].text)
        ))
        
    def preparar_etapa_versiculo(self):
        """Prepara las opciones para la pregunta del versículo (input de texto)."""
        self.ids.game_layout.clear_widgets()
        
        from kivy.uix.textinput import TextInput
        self.ids.game_layout.add_widget(TextInput(
            id='verse_game_input',
            hint_text='Ingresa el número del Versículo',
            multiline=False,
            size_hint_y=0.7
        ))
        
        from kivy.uix.button import Button
        self.ids.game_layout.add_widget(Button(
            text='Responder Versículo',
            size_hint_y=0.3,
            on_release=lambda btn: self.responder_partida(self.ids.game_layout.children[1].text)
        ))

    def finalizar_partida(self, exito, mensaje):
        """Actualiza el estado del versículo basado en el resultado."""
        
        versiculo = DM.data['versiculos'][self.current_verse_key]
        
        if exito:
            versiculo['veces_acertado'] += 1
            versiculo['nivel_refuerzo'] = min(5, versiculo['nivel_refuerzo'] + 1)
        else:
            versiculo['veces_fallado'] += 1
            versiculo['nivel_refuerzo'] = max(0, versiculo['nivel_refuerzo'] - 1)
            
            # Lógica de eliminación: si falla y el nivel es 0 (o bajo)
            if versiculo['nivel_refuerzo'] == 0:
                del DM.data['versiculos'][self.current_verse_key]
                DM.update_player_data('nivel_versiculos', DM.get_player_data()['nivel_versiculos'] - 1)
                mensaje += " ¡El versículo ha sido olvidado y eliminado!"
                
        DM.save_data()
        self.update_verse_count()
        self.game_status = mensaje
        self.ids.game_text.text = "Partida finalizada. ¡Juega de nuevo!"
        self.ids.game_layout.clear_widgets()
        # Vuelve a mostrar el botón de iniciar partida
        from kivy.uix.button import Button
        self.ids.game_layout.add_widget(Button(text="Iniciar Nueva Partida", on_release=lambda btn: self.iniciar_partida()))
