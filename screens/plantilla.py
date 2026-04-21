from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ColorProperty
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.app import App

from db.bibliasestaticas import Reg,Biblia
# por defecto uso RNV196

class BotonEstilizado(ButtonBehavior, BoxLayout):
    """
    Clase que define la lógica del botón personalizado.
    La estructura visual se define exclusivamente en kv_files/plantilla.kv
    para evitar duplicados.
    """
    texto = StringProperty("Botón")
    icono = StringProperty("images/pray_icon.png")
    fuente = StringProperty("stdt/fonts/LacheyardScript_PERSONAL_USE_ONLY.otf")
    color_fondo = ColorProperty((1, 1, 1, 1))
    radio_borde = ListProperty([dp(15)])
    mostrar_icono = BooleanProperty(True)
    tamanio_texto = StringProperty('16sp')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class BuscadorBiblico(ModalView):
    """Popup especializado para la búsqueda secuencial y carrito."""
    
    def __init__(self, callback_finalizar, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.95, 0.9)
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.8)
        self.callback_finalizar = callback_finalizar
        
        # Datos
        self.libreriaPrincipal = App.get_running_app().getModel('Biblioteca')
        self.carrito = {}  # { 'idBook_cap_ver': objeto_registro }
        self.libro_actual = None
        self.capitulo_actual = None
        self.__BibliaActiva__ = None
        self.font_name = App.get_running_app().app_config.get('FONT_NAME', '')

        # --- LAYOUT PRINCIPAL ---
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Fondo estilo pergamino para el contenedor interno
        with self.layout.canvas.before:
            Factory.Color(0.96, 0.92, 0.84, 1)
            self.rect = Factory.RoundedRectangle(pos=self.layout.pos, size=self.layout.size, radius=[dp(15)])
        self.layout.bind(pos=self._update_rect, size=self._update_rect)

        # --- CABECERA: Selector de Biblia ---
        header_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        
        lbl_bib = Label(text="Biblia:", color=(0.3, 0.2, 0.1, 1), size_hint_x=None, width=dp(60), bold=True)
        
        # Obtenemos nombres de biblias para el Spinner
        biblias_disponibles = [n.path.split('/')[-1] for n in self.libreriaPrincipal['contenido']]
        self.spinner_biblia = Spinner(
            text=biblias_disponibles[0] if biblias_disponibles else "RVR1960",
            values=biblias_disponibles,
            size_hint=(1, 1),
            background_normal='',
            background_color=(0.8, 0.7, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        self.spinner_biblia.bind(text=self._on_biblia_change)
        
        header_box.add_widget(lbl_bib)
        header_box.add_widget(self.spinner_biblia)
        self.layout.add_widget(header_box)

        # --- TÍTULO DE PASO (Subrayado y resaltado) ---
        self.lbl_paso = Label(
            text="[u][b]Seleccionar Libro[/b][/u]",
            markup=True,
            color=(0.5, 0.1, 0.1, 1), # Rojo oscuro vibrante
            font_size='22sp',
            size_hint_y=None,
            height=dp(45),
            halign='center'
        )
        self.layout.add_widget(self.lbl_paso)

        # --- CONTENIDO (SCROLL) ---
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self.grid_opciones = GridLayout(cols=3, size_hint_y=None, spacing=dp(8), padding=dp(5))
        self.grid_opciones.bind(minimum_height=self.grid_opciones.setter('height'))
        self.scroll.add_widget(self.grid_opciones)
        self.layout.add_widget(self.scroll)

        # --- FOOTER (BOTONES ALINEADOS) ---
        self.footer = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8))
        
        self.btn_atras = Button(text="Atrás", background_color=(0.6, 0.5, 0.4, 1), size_hint_x=0.3)
        self.btn_clrnew = Button(text="Todos", background_color=(0.7, 0.6, 0.5, 1), size_hint_x=0.3, disabled=True)
        self.btn_ver = Button(text="Cargar (0)", background_color=(0.2, 0.5, 0.2, 1), size_hint_x=0.4, bold=True)

        self.btn_atras.bind(on_release=self._action_atras)
        self.btn_ver.bind(on_release=self.finalizar_seleccion)
        self.btn_clrnew.bind(on_release=self.elegirTodos)

        self.footer.add_widget(self.btn_atras)
        self.footer.add_widget(self.btn_clrnew)
        self.footer.add_widget(self.btn_ver)
        self.layout.add_widget(self.footer)

        self.add_widget(self.layout)
        self.mostrar_libros()

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _on_biblia_change(self, spinner, text):
        """Cambia la biblia activa y reinicia la vista."""
        for n in self.libreriaPrincipal['contenido']:
            if text in n.path:
                self.__BibliaActiva__ = n
                Logger.info(f"Buscador: Biblia cambiada a {text}")
                break
        self.mostrar_libros()

    def get_biblia(self):
        if not self.__BibliaActiva__:
            # Por defecto busca RVR1960
            for n in self.libreriaPrincipal['contenido']:
                if 'RVR1960' in n.path:
                    self.__BibliaActiva__ = n
                    break
            if not self.__BibliaActiva__: self.__BibliaActiva__ = self.libreriaPrincipal['contenido'][0]
        return self.__BibliaActiva__

    def limpiar_grid(self, cols=3):
        self.grid_opciones.clear_widgets()
        self.grid_opciones.cols = cols
        self.scroll.scroll_y = 1

    def mostrar_libros(self):
        self.lbl_paso.text = "[u][b]Seleccionar Libro[/b][/u]"
        self.limpiar_grid(cols=3)
        self.btn_atras.disabled = True
        self.btn_clrnew.text = "Limpiar"
        self.btn_clrnew.disabled = len(self.carrito) == 0
        self.btn_clrnew.unbind(on_release=self.elegirTodos)
        self.btn_clrnew.bind(on_release=self.limpiar_carrito)
        
        libros = self.get_biblia().getAllNameBook()
        bandera_nt = False
        
        for lib in libros:
            name, idBook, test_ref = lib
            
            if test_ref == 2 and not bandera_nt:
                bandera_nt = True
                # Separador NT
                sep = Label(text="[b]NUEVO TESTAMENTO[/b]", markup=True, size_hint_y=None, height=dp(50), color=(0.4, 0.2, 0, 1))
                self.grid_opciones.add_widget(Widget()) # Placeholder
                self.grid_opciones.add_widget(sep)
                self.grid_opciones.add_widget(Widget()) # Placeholder

            btn = Button(text=name, 
                        size_hint_y=None, 
                        height=dp(50), 
                        background_normal='', 
                        #background_color=(0.9, 0.85, 0.7, 1), 
                        background_color=(0.9, 0.85, 0.75, 1),
                        #color=(0.2, 0.1, 0, 1))
                        color=(0.2, 0.1, 0, 1),
                        font_size='14sp'
                        )
            btn.bind(on_release=lambda x, l=lib: self.mostrar_capitulos({'name': l[0], 'id': l[1]}))
            self.grid_opciones.add_widget(btn)

    def mostrar_capitulos(self, libro):
        self.libro_actual = libro
        self.lbl_paso.text = f"[u][b]{libro['name']}[/b][/u] - Capítulos"
        self.limpiar_grid(cols=5)
        self.btn_atras.disabled = False
        
        capitulos = self.get_biblia().countCapitulos(libro['id'])
        for i in range(1, capitulos + 1):
            btn = Button(text=str(i), size_hint=(None, None), size=(dp(55), dp(55)), 
                         background_color=(0.85, 0.8, 0.7, 1))
            btn.bind(on_release=lambda x, c=i: self.mostrar_versiculos(libro, c))
            self.grid_opciones.add_widget(btn)

    def mostrar_versiculos(self, libro, capitulo):
        self.libro_actual = libro
        self.capitulo_actual = capitulo
        self.lbl_paso.text = f"[u][b]{libro['name']} {capitulo}[/b][/u]"
        self.limpiar_grid(cols=5)
        
        # Configurar botón de acción para "Elegir Todos"
        self.btn_clrnew.text = "Todos"
        self.btn_clrnew.disabled = False
        self.btn_clrnew.unbind(on_release=self.limpiar_carrito)
        self.btn_clrnew.bind(on_release=self.elegirTodos)

        total_v = self.get_biblia().countVersiculos(libro['id'], capitulo)
        for i in range(1, total_v + 1):
            key = f"{libro['id']}_{capitulo}_{i}"
            esta_en_carrito = key in self.carrito
            
            btn = Button(text=str(i), size_hint=(None, None), size=(dp(50), dp(50)),
                         background_color=(0.2, 0.7, 0.2, 1) if esta_en_carrito else (0.4, 0.4, 0.4, 1))
            btn.bind(on_release=lambda x, v=i: self.toggle_carrito(libro, capitulo, v, x))
            self.grid_opciones.add_widget(btn)

    def toggle_carrito(self, libro, cap, ver, btn):
        id_libro = libro['id']
        key = f"{id_libro}_{cap}_{ver}"
        
        if key in self.carrito:
            # Si ya está, lo quitamos
            del self.carrito[key]
            btn.background_color = (0.4, 0.4, 0.4, 1)
        else:
            # Si no está, lo buscamos en la DB y lo agregamos
            respuesta = self.get_biblia().buscarVersiculo(libro['name'], cap, ver, id_libro)
            if respuesta:
                self.carrito[key] = respuesta[0]
                btn.background_color = (0.2, 0.7, 0.2, 1)
        
        self.btn_ver.text = f"Cargar ({len(self.carrito)})"

    def elegirTodos(self, *args):
        """Selecciona todos los versículos del capítulo actual."""
        if not self.libro_actual or not self.capitulo_actual: return
        
        registros = self.get_biblia().buscarVersiculo(self.libro_actual['name'], self.capitulo_actual, 0, self.libro_actual['id'])
        
        for reg in registros:
            # Dependiendo de tu objeto Registro, accede a los campos (usamos índices o keys)
            # Suponiendo que reg es un objeto con .chapter, .verse, .idBook
            key = f"{self.libro_actual['id']}_{self.capitulo_actual}_{reg['verse']}"
            self.carrito[key] = reg
            
        # Refrescar UI de botones
        for widget in self.grid_opciones.children:
            if isinstance(widget, Button):
                widget.background_color = (0.2, 0.7, 0.2, 1)
        
        self.btn_ver.text = f"Cargar ({len(self.carrito)})"

    def limpiar_carrito(self, *args):
        self.carrito.clear()
        self.btn_ver.text = "Cargar (0)"
        self.btn_clrnew.disabled = True
        # Si estamos en la vista de versículos, los pintamos de gris
        for widget in self.grid_opciones.children:
            if isinstance(widget, Button):
                widget.background_color = (0.4, 0.4, 0.4, 1)

    def _action_atras(self, *args):
        # Lógica de navegación hacia atrás simple
        if self.capitulo_actual:
            self.capitulo_actual = None
            self.mostrar_capitulos(self.libro_actual)
        else:
            self.mostrar_libros()

    def finalizar_seleccion(self, *args):
        if not self.carrito: 
            self.dismiss()
            return
        
        # Convertimos el diccionario a una lista ordenada para el Rollo
        seleccion_ordenada = list(self.carrito.values())
        # Opcional: ordenar por libro, capítulo y versículo aquí
        
        self.dismiss()
        self.callback_finalizar(seleccion_ordenada)
        
class RolloBiblico(ModalView):
    titulo_libro = StringProperty("Libro")
    contenido_texto = StringProperty("Cargando palabra de vida...")
    fuente_titulo = StringProperty("stdt/fonts/LacheyardScript_PERSONAL_USE_ONLY.otf")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__data__ = []        # Datos de los versículos actuales
        self.__point__ = -1       # Índice actual
        self.__exit__ = lambda: None
        self.carrito_estudio = [] # "Carrito" para guardar versículos seleccionados
        # listado de coleccion de biblias distintos idiomas y redundancias 
        self.__libreriaBiblica__ = App.get_running_app().getModel('Biblioteca')
        self.__BibliaActiva__=None
        
        # configuracion general
        self.font_name = App.get_running_app().app_config['FONT_NAME']
                
    def __get_biblia_activa(self):
        # metodo para no repetir busquedas en cada metodo
        if not self.__BibliaActiva__:
            biblioteca = self.Biblioteca
            # la primer biblia del listado
            biblia = biblioteca['contenido']
            # book :     'id' 'book_reference_id testament_reference_id  name 
            rvr1960=None
            for n in biblia:
                #REINA VALERA 1960
                if 'RVR1960' in n.path :
                    # es el reina valera
                    rvr1960 = n
                    break
            self.__BibliaActiva__ = rvr1960
            return self.__BibliaActiva__
        else:
            return self.__BibliaActiva__
        
        
    def iniciar(self,**kwargs):
        Logger.info("Cargando Al iniciar el pasaje. debe ser llamado cuando la calase es invocada")
        
    
    def mostrar_pasaje(self,  indiceInicial ,  ContenidoTotal=None, FunctionExit=None ):
        """Muestra el texto en el rollo."""
        if ContenidoTotal is not None:
            self.__data__ = ContenidoTotal
        
        if FunctionExit is not None:
            self.__exit__ = FunctionExit
        
        if not self.__data__:
            return

        self.__point__ = max(0, min(indiceInicial, len(self.__data__) - 1))
        registro = self.__data__[self.__point__]
        
        Logger.debug(f"mostrando pasaje:libro:{registro['nameBook']},{registro['chapter']}:{registro['verse']} ---> {registro['text']}")
        
        # Formateo de título con markup para fuentes mixtas correcion de fuente
        self.titulo_libro = f"[b]{registro.nameBook}[/b] [color=888888]{registro.chapter}[/color]:[color=228B22]{registro.verse}[/color]"
        self.contenido_texto = registro.text
        
        self.actualizar_grid_navegacion()
        
        if not self._is_open:
            self.open()
                        
    
    def actualizar_grid_navegacion(self):
        """Actualiza los botoncitos de versículos en la cabecera."""
        if not hasattr(self.ids, 'grid_versiculos'):
            return

        self.ids.grid_versiculos.clear_widgets()
        total = len(self.__data__)
        
        # Mostrar rango cercano al punto actual 5
        inicio = max(0, self.__point__ - 2)
        fin = min(total - 1, self.__point__ + 3)

        for i in range(inicio, fin + 1):
            reg_v = self.__data__[i]
            es_actual = (i == self.__point__)
            color_btn = (0.2, 0.6, 0.2, 1) if es_actual else (0.7, 0.6, 0.4, 1)
            #color_btn = (0.85, 0.8, 0.7, 1) if es_actual else (0.7, 0.6, 0.4, 1)
            
            num_versiculo = str(int(reg_v['verse']))
            
            btn_v = Button(
                text=num_versiculo,
                font_name=self.font_name,
                size_hint=(None, None),
                size=(dp(35), dp(35)),
                background_normal='',
                background_color=color_btn,
                color=(1, 1, 1, 1),
                font_size='12sp',
                bold=es_actual,
                disabled=es_actual
            )
            btn_v.bind(on_release=lambda x, idx=i: self.mostrar_pasaje(idx))
            self.ids.grid_versiculos.add_widget(btn_v)   
    
                    
    def checkVersiculo(self,versiculo):
        if isinstance( versiculo , str ):
            # quiere decir que estamos en una secuencia "22-12" o simililar
            inicio=1
            fin=2
            try:
                partes = versiculos.replace(" ","").split("-")
                inicio=int(partes[0])
                fin=int(partes[1])
            except (ValueError, IndexError) as e:
                Logger.error(f"ERROR EXCEPTION!!! {e}")
            return inicio,fin
        else:
            # castear varialbe para asegurar respuesta
            return int(versiculo)
    
    def _cerrar_(self):
        Logger.info("intentando cerrar...")
        self.dismiss()
        self.cerrar()
        
    def cerrar(self):
        '''
            cerrado personalizado
        '''
        self.__exit__()
        
    def ir_a_versiculo(self, numero):
        Logger.info(f"Navegando al versículo {numero}")
        # Aquí podrías hacer scroll automático o resaltar el texto
        self.mostrar_pasaje( numero,self.__data__,None)
        
    def pagina_anterior(self):
        Logger.info("Cargando capítulo anterior...")
        index=int(self.__point__)
        if index>0:
            index-=1
        self.mostrar_pasaje( index,self.__data__,None)
        
    def pagina_siguiente(self):
        Logger.info("Cargando capítulo siguiente...")
        index=int(self.__point__)
        if index<len(self.__data__)-1:
            index+=1
        self.mostrar_pasaje( index,self.__data__,None)
        

            

    def abrir_busqueda(self):
        """Inicia el proceso de búsqueda/selección."""
        Logger.info("RolloBiblico: Iniciando búsqueda secuencial...")
        self.__data__=None # reiniciar data control
        buscador = BuscadorBiblico(callback_finalizar=self.procesar_busqueda)
        buscador.open()
    
    def procesar_busqueda(self, seleccion):
        """Convierte los items del carrito en datos reales para el Rollo."""
        Logger.info(f"Rollo: Cargando {len(seleccion)} versículos seleccionados.")
        # Aquí deberías hacer un query a la DB para obtener el TEXTO real de cada item en seleccion
        # Por ahora los mostramos como lista
        self.mostrar_pasaje(0, ContenidoTotal=seleccion)
    

            
    def elegir_libro(self):
        """Paso 1: Mostrar lista de libros disponibles."""
        biblia = self.__get_biblia_activa()
        libros = biblia.get_all_books() # Asumiendo que tu modelo tiene este método
        
        # Aquí crearíamos un Modal o actualizaríamos el contenido del Rollo
        # para mostrar botones con los nombres de los libros.
        # Por ahora, simulamos la elección para completar la lógica:
        # self.elegir_capitulo(id_libro)
        pass

    def elegir_capitulo(self, id_libro):
        """Paso 2: Elegir capítulo del libro seleccionado."""
        biblia = self.__get_biblia_activa()
        # capítulos = biblia.get_chapters_count(id_libro)
        # Generar grid de números de capítulos...
        pass

    def elegir_versiculos(self, id_libro, num_capitulo):
        """Paso 3: Elegir uno o varios versículos (Carrito de compras)."""
        biblia = self.__get_biblia_activa()
        # versiculos = biblia.get_verses(id_libro, num_capitulo)
        
        # Lógica de Carrito:
        # Al tocar un versículo:
        # self.carrito_estudio.append(registro_versiculo)
        # Botón "Finalizar Selección":
        # self.mostrar_pasaje(0, ContenidoTotal=self.carrito_estudio)
        pass

    def limpiar_estudio(self):
        """Vacía el carrito de versículos."""
        self.carrito_estudio = []
        Logger.info("RolloBiblico: Carrito de estudio vaciado.")

    '''
    TODO: se podria crear una logica pensando en un carrito de compras? para elegir libro, capitulo y varios versiculos y repetir esa eleccion repetidamente?...
    para luego mostrar todo junto????
    '''

'''
ejemplo de uso:
# Ejemplo dentro de una función de VersesScreen

def leer_biblia(self):
    # 1. Obtienes los datos de tu modelo dinámico
    texto_ejemplo = "En el principio creó Dios los cielos y la tierra..."
    
    # 2. Creas e invocas el Rollo
    rollo = Factory.RolloBiblico()
    rollo.mostrar_pasaje("Génesis", texto_ejemplo, total_versiculos=31)

'''


# Registrar en el Factory permite usar <BotonEstilizado> en cualquier KV
# incluso si no se ha importado explícitamente en ese archivo.
Factory.register('BotonEstilizado', cls=BotonEstilizado)
Factory.register('RolloBiblico', cls=RolloBiblico)
