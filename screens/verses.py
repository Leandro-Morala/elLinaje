from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.logger import Logger
from kivy.app import App
from screens.basescreen import BaseScreen


class VersesScreen(BaseScreen):
    """Pantalla para memorizar versiculos biblicos usando la Biblia RVR1960."""

    libros_nombres   = ListProperty([])
    capitulos_lista  = ListProperty([])
    versiculos_lista = ListProperty([])

    libro_ok     = BooleanProperty(False)
    capitulo_ok  = BooleanProperty(False)
    versiculo_ok = BooleanProperty(False)

    verse_count = StringProperty("Versiculos guardados: 0")
    status_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capitulos_model = App.get_running_app().getModel('CapitulosModel')
        self._rvr1960    = None
        self._libros_map = {}
        self._libro_id   = None
        self._libro_nombre = None
        self._capitulo_num = None
        self._versiculo_num = None
        self._cargar_biblia()

    # ------------------------------------------------------------------

    def _cargar_biblia(self):
        biblioteca = App.get_running_app().getModel('Biblioteca')
        if not biblioteca or 'contenido' not in biblioteca:
            Logger.error("[Verses] Biblioteca no disponible")
            return
        for biblia in biblioteca['contenido']:
            if 'RVR1960' in biblia.path:
                self._rvr1960 = biblia
                return
        if biblioteca['contenido']:
            self._rvr1960 = biblioteca['contenido'][0]
            Logger.warning("[Verses] RVR1960 no encontrada, usando primera biblia")

    def on_enter(self, *args):
        if not self.libros_nombres:
            self._cargar_libros()
        self._reset_form()
        self._update_verse_count()

    def _cargar_libros(self):
        if not self._rvr1960:
            return
        try:
            libros = self._rvr1960.getAllNameBook()
            self._libros_map = {row[0]: row[1] for row in libros}
            self.libros_nombres = [row[0] for row in libros]
            Logger.info(f"[Verses] {len(self.libros_nombres)} libros cargados")
        except Exception as e:
            Logger.error(f"[Verses] _cargar_libros: {e}")

    def _reset_form(self):
        self.libro_ok    = False
        self.capitulo_ok = False
        self.versiculo_ok = False
        self.capitulos_lista  = []
        self.versiculos_lista = []
        self.status_text = ""
        self._libro_id     = None
        self._libro_nombre = None
        self._capitulo_num = None
        self._versiculo_num = None
        if 'spinner_libro' in self.ids:
            self.ids.spinner_libro.text     = "Seleccionar libro..."
            self.ids.spinner_capitulo.text  = "Capitulo..."
            self.ids.spinner_versiculo.text = "Versiculo..."
            self.ids.text_input.text = ""

    # ------------------------------------------------------------------
    # Callbacks de spinners
    # ------------------------------------------------------------------

    def on_libro_seleccionado(self, texto):
        if not texto or texto not in self._libros_map:
            return
        book_id = self._libros_map[texto]
        self._libro_id     = book_id
        self._libro_nombre = texto
        try:
            total = self._rvr1960.countCapitulos(book_id)
            self.capitulos_lista = [str(i) for i in range(1, total + 1)]
        except Exception as e:
            Logger.error(f"[Verses] countCapitulos: {e}")
            self.capitulos_lista = []
        self.libro_ok    = True
        self.capitulo_ok = False
        self.versiculo_ok = False
        self.versiculos_lista = []
        if 'spinner_capitulo' in self.ids:
            self.ids.spinner_capitulo.text  = "Capitulo..."
            self.ids.spinner_versiculo.text = "Versiculo..."
        if 'text_input' in self.ids:
            self.ids.text_input.text = ""

    def on_capitulo_seleccionado(self, texto):
        if not texto or not texto.isdigit():
            return
        cap = int(texto)
        self._capitulo_num = cap
        try:
            total = self._rvr1960.countVersiculos(self._libro_id, cap)
            self.versiculos_lista = [str(i) for i in range(1, total + 1)]
        except Exception as e:
            Logger.error(f"[Verses] countVersiculos: {e}")
            self.versiculos_lista = []
        self.capitulo_ok  = True
        self.versiculo_ok = False
        if 'spinner_versiculo' in self.ids:
            self.ids.spinner_versiculo.text = "Versiculo..."
        if 'text_input' in self.ids:
            self.ids.text_input.text = ""

    def on_versiculo_seleccionado(self, texto):
        if not texto or not texto.isdigit():
            return
        self._versiculo_num = int(texto)
        self.versiculo_ok = True

    # ------------------------------------------------------------------
    # Guardar
    # ------------------------------------------------------------------

    def guardar_versiculo(self):
        texto = self.ids.text_input.text.strip()
        if not texto:
            self.status_text = "Escribe el texto del versiculo primero."
            return
        if self.capitulos_model.existe(1, self._libro_id, self._capitulo_num, self._versiculo_num):
            self.status_text = "Este versiculo ya esta guardado."
            return
        result = self.capitulos_model.insertar(
            id_usuario=1,
            book_id=self._libro_id,
            book_name=self._libro_nombre,
            capitulo=self._capitulo_num,
            versiculo=self._versiculo_num,
            texto=texto,
        )
        if result:
            referencia = f"{self._libro_nombre} {self._capitulo_num}:{self._versiculo_num}"
            self.capitulos_model.renovar_vida(1)
            subio = self._verificar_nivel()
            if subio:
                self.status_text = f"Guardado: {referencia}  |  Subiste de nivel!"
            else:
                self.status_text = f"Guardado: {referencia}"
            self._reset_form()
            self._update_verse_count()
        else:
            self.status_text = "Error al guardar. Intenta de nuevo."

    def _verificar_nivel(self):
        """Sube nivel del usuario cada 10 versiculos. Devuelve True si subio."""
        registros = self.capitulos_model.get_by_usuario(1)
        total = len(registros) if registros else 0
        nivel_por_versiculos = total // 10
        nivel_actual = int(self.user.get_tag(1, 'nivel') or 0)
        if nivel_por_versiculos > nivel_actual:
            self.user.set_tag(1, 'nivel', nivel_por_versiculos)
            Logger.info(f"[Verses] nivel subio a {nivel_por_versiculos}")
            return True
        return False

    def _update_verse_count(self):
        registros = self.capitulos_model.get_by_usuario(1)
        count = len(registros) if registros else 0
        vida  = self.capitulos_model.calcular_vida_dias(count)
        self.verse_count = f"{count} versiculos guardados  |  vida: {vida} dias"

    # ------------------------------------------------------------------

    def ir_a_partida(self):
        registros = self.capitulos_model.get_by_usuario(1)
        if not registros:
            self.status_text = "Guarda al menos un versiculo para jugar."
            return
        if self.manager.has_screen('verses_game'):
            self.manager.current = 'verses_game'
        else:
            self.status_text = "Pantalla de partida aun no disponible."
