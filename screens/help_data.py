from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.logger import Logger

HELP_DATA = {
    "inicio": [
        {
            "titulo": "Bienvenido, A EL LINAJE",
            "cuerpo": "Has entrado en 'El Linaje'. Este no es solo un juego, es un registro de tu caminar espiritual. \n\nPara comenzar, observa la barra de poder en la parte superior.",
            "imagen": "assets/images/help/intro.png"
        },
        {
            "titulo": "La Llama Espiritual",
            "cuerpo": "Tu barra representa tu fortaleza actual. El mundo y el tiempo la consumen lentamente. \n\nNo dejes que se apague; la oración es tu combustible.",
            "imagen": "assets/images/help/power.png"
        }
    ],
    "biblia": [
        {
            "titulo": "Las Sagradas Escrituras",
            "cuerpo": "Cada capítulo que leas aquí se guardará en tu historial. Leer la palabra aumenta tu sabiduría y desbloquea nuevos niveles de entendimiento.",
            "imagen": "assets/images/help/bible.png"
        },
        {
            "titulo": "Las Sagradas Escrituras",
            "cuerpo": "Con paciencia y conocimiento el pueblo se hace mas sabio y puede conquistar hasta lo imposible. La disciplina crea sabiduria.",
            "imagen": "assets/images/help/bible.png"
        },
    ],
    "oracion": [
        {
            "titulo": "El Altar de Oración",
            "cuerpo": "Al presionar 'Iniciar', el tiempo comenzará a contar. Ese tiempo se transformará en energía para tu barra principal al terminar.",
            "imagen": "assets/images/help/prayer_logic.png"
        }
    ]
}

'''
modo de uso:
    
    def on_enter(self):
    # Verificamos si ya vió la ayuda de esta pantalla
    if not self.usuario_modelo.ya_vio_ayuda('biblia'):
        # Creamos la hoja de ayuda para esta sección
        ayuda = HelpSheet(section_key='biblia')
        
        # La mostramos en un Popup elegante
        from kivy.uix.popup import Popup
        self.popup_ayuda = Popup(
            title="Guía Espiritual",
            content=ayuda,
            size_hint=(0.85, 0.7),
            background='assets/images/popup_bg.png' # Tu textura de pergamino
        )
        self.popup_ayuda.open()


'''
class HelpSheet(BoxLayout):
    """
    Esta clase maneja la lógica de las 'hojas de ayuda'.
    Permite navegar entre páginas y actualizar la interfaz.
    """
    pages = ListProperty([])
    current_index = NumericProperty(0)
    total_pages = NumericProperty(0)
    
    # Estas propiedades se vinculan automáticamente con los Labels en el archivo KV
    current_title = StringProperty("")
    current_body = StringProperty("")
    current_image = StringProperty("")

    def __init__(self, section_key="inicio", **kwargs):
        super().__init__(**kwargs)
        # Cargamos la sección de datos correspondiente
        self.pages = HELP_DATA.get(section_key, [])
        self.total_pages = len(self.pages)
        
        if self.total_pages > 0:
            self.update_content()
        else:
            Logger.warning(f"Ayuda: La sección '{section_key}' no contiene páginas.")

    def update_content(self):
        """Actualiza las propiedades que el archivo KV está observando."""
        if 0 <= self.current_index < self.total_pages:
            page = self.pages[self.current_index]
            self.current_title = page.get('titulo', "Sin Título")
            self.current_body = page.get('cuerpo', "")
            self.current_image = page.get('imagen', "")

    def next_page(self):
        """Avanza a la siguiente página o cierra si es la última."""
        if self.current_index < self.total_pages - 1:
            self.current_index += 1
            self.update_content()
        else:
            self.dismiss_help()

    def prev_page(self):
        """Vuelve a la página anterior."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_content()

    def dismiss_help(self):
        """Busca el Popup que contiene esta hoja y lo cierra."""
        # Esta es una forma limpia de cerrar el popup desde adentro
        p = self.parent
        while p:
            if hasattr(p, 'dismiss'):
                p.dismiss()
                break
            p = p.parent
