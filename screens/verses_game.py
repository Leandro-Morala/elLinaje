import random
import time
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger
from kivy.app import App
from screens.basescreen import BaseScreen


class VersesGameScreen(BaseScreen):
    """Desafio: dado el texto de un versiculo, adivinar libro, capitulo y versiculo."""

    # Estado de la pantalla
    fase = StringProperty("adivinar")  # 'adivinar' | 'resultado' | 'sin_datos'

    # Verso en juego
    verse_text = StringProperty("")
    vida_info  = StringProperty("")

    # Spinners de adivinanza
    libros_nombres   = ListProperty([])
    capitulos_lista  = ListProperty([])
    versiculos_lista = ListProperty([])
    libro_ok    = BooleanProperty(False)
    capitulo_ok = BooleanProperty(False)

    # Resultado
    score_value    = NumericProperty(0.0)
    score_color    = ListProperty([0.8, 0.2, 0.2, 1])
    resultado_libro = StringProperty("")
    resultado_cap   = StringProperty("")
    resultado_vers  = StringProperty("")
    resultado_color_libro = ListProperty([0.8, 0.2, 0.2, 1])
    resultado_color_cap   = ListProperty([0.8, 0.2, 0.2, 1])
    resultado_color_vers  = ListProperty([0.8, 0.2, 0.2, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capitulos_model = App.get_running_app().getModel('CapitulosModel')
        self._rvr1960    = None
        self._libros_map = {}
        self._verso_actual = None
        self._cargar_biblia()

    def _cargar_biblia(self):
        biblioteca = App.get_running_app().getModel('Biblioteca')
        if not biblioteca or 'contenido' not in biblioteca:
            return
        for biblia in biblioteca['contenido']:
            if 'RVR1960' in biblia.path:
                self._rvr1960 = biblia
                return
        if biblioteca['contenido']:
            self._rvr1960 = biblioteca['contenido'][0]

    # ------------------------------------------------------------------
    # Ciclo de pantalla
    # ------------------------------------------------------------------

    def on_enter(self, *args):
        eliminados = self.capitulos_model.procesar_envejecimiento(1)
        if eliminados:
            nivel_actual = int(self.user.get_tag(1, 'nivel') or 0)
            self.user.set_tag(1, 'nivel', max(0, nivel_actual - eliminados))
            Logger.info(f"[VersesGame] {eliminados} expirados, nivel {nivel_actual} -> {max(0, nivel_actual - eliminados)}")
        if not self.libros_nombres:
            self._cargar_libros()
        self._nuevo_verso()

    def _cargar_libros(self):
        if not self._rvr1960:
            return
        try:
            libros = self._rvr1960.getAllNameBook()
            self._libros_map = {row[0]: row[1] for row in libros}
            self.libros_nombres = [row[0] for row in libros]
        except Exception as e:
            Logger.error(f"[VersesGame] _cargar_libros: {e}")

    def _dias_restantes(self, registros, registro):
        """Dias que le quedan a un verso, usando fecha_renovacion si disponible."""
        total = len(registros)
        vida_seg = self.capitulos_model.calcular_vida_dias(total) * 86400
        ts = self.capitulos_model._get_referencia_ts(registro)
        return (vida_seg - (int(time.time()) - ts)) / 86400

    def _nuevo_verso(self):
        registros = self.capitulos_model.get_by_usuario(1)
        if not registros:
            self.verse_text = "No tienes versiculos guardados.\nVuelve a Lectura Biblica para agregar."
            self.vida_info = ""
            self.fase = 'sin_datos'
            return

        # Calcular dias restantes para cada verso
        with_dias = [(r, self._dias_restantes(registros, r)) for r in registros]

        # Agrupar en buckets de 5 dias (bucket 0 = mas urgente: 0-5 dias restantes)
        buckets = {}
        for r, d in with_dias:
            bucket = max(0, int(d // 5))
            buckets.setdefault(bucket, []).append((r, d))

        # Elegir siempre el bucket mas urgente (numero mas bajo)
        bucket_elegido = sorted(buckets.keys())[0]
        grupo = buckets[bucket_elegido]

        # Pesos dentro del bucket: menor nivel_refuerzo → mas probable
        registros_grupo = [r for r, _ in grupo]
        pesos = [max(1, 6 - r['nivel_refuerzo']) for r in registros_grupo]
        self._verso_actual = random.choices(registros_grupo, weights=pesos, k=1)[0]

        # vida_info del verso seleccionado (no general)
        dias_verso = self._dias_restantes(registros, self._verso_actual)
        dias_str = f"{max(0.0, dias_verso):.1f}"
        refuerzo = self._verso_actual['nivel_refuerzo']
        self.vida_info = f"Vence en {dias_str} dias  |  Refuerzo: {refuerzo}/5"

        self.verse_text = self._verso_actual['texto']
        self.fase = 'adivinar'
        self._reset_spinners()

    def _reset_spinners(self):
        self.capitulos_lista  = []
        self.versiculos_lista = []
        self.libro_ok    = False
        self.capitulo_ok = False
        if 'spinner_libro_g' in self.ids:
            self.ids.spinner_libro_g.text     = "Seleccionar libro..."
            self.ids.spinner_capitulo_g.text  = "Capitulo..."
            self.ids.spinner_versiculo_g.text = "Versiculo..."

    # ------------------------------------------------------------------
    # Callbacks de spinners
    # ------------------------------------------------------------------

    def on_libro_seleccionado(self, texto):
        if not texto or texto not in self._libros_map:
            return
        book_id = self._libros_map[texto]
        try:
            total = self._rvr1960.countCapitulos(book_id)
            self.capitulos_lista = [str(i) for i in range(1, total + 1)]
        except Exception as e:
            Logger.error(f"[VersesGame] countCapitulos: {e}")
            self.capitulos_lista = []
        self.libro_ok    = True
        self.capitulo_ok = False
        self.versiculos_lista = []
        if 'spinner_capitulo_g' in self.ids:
            self.ids.spinner_capitulo_g.text  = "Capitulo..."
            self.ids.spinner_versiculo_g.text = "Versiculo..."

    def on_capitulo_seleccionado(self, texto):
        if not texto or not texto.isdigit():
            return
        cap = int(texto)
        libro_texto = self.ids.spinner_libro_g.text
        book_id = self._libros_map.get(libro_texto)
        if not book_id:
            return
        try:
            total = self._rvr1960.countVersiculos(book_id, cap)
            self.versiculos_lista = [str(i) for i in range(1, total + 1)]
        except Exception as e:
            Logger.error(f"[VersesGame] countVersiculos: {e}")
            self.versiculos_lista = []
        self.capitulo_ok = True
        if 'spinner_versiculo_g' in self.ids:
            self.ids.spinner_versiculo_g.text = "Versiculo..."

    # ------------------------------------------------------------------
    # Logica del juego
    # ------------------------------------------------------------------

    def comprobar(self):
        if not self._verso_actual:
            return
        verso = self._verso_actual

        libro_input = self.ids.spinner_libro_g.text
        cap_input   = self.ids.spinner_capitulo_g.text
        vers_input  = self.ids.spinner_versiculo_g.text

        libro_ok = (libro_input == verso['book_name'])
        cap_ok   = (cap_input.isdigit() and int(cap_input) == verso['capitulo'])
        vers_ok  = (vers_input.isdigit() and int(vers_input) == verso['versiculo'])

        # Puntuacion escalonada: 0.0 / 0.4 / 0.7 / 1.0
        score = 0.0
        if libro_ok:
            score += 0.4
            if cap_ok:
                score += 0.3
                if vers_ok:
                    score += 0.3
        self.score_value = round(score, 2)

        # Color de la barra
        if score >= 1.0:
            self.score_color = [0.2, 0.8, 0.3, 1]
        elif score >= 0.7:
            self.score_color = [0.95, 0.78, 0.1, 1]
        elif score >= 0.4:
            self.score_color = [0.9, 0.5, 0.1, 1]
        else:
            self.score_color = [0.8, 0.2, 0.2, 1]

        # Mensajes de resultado
        verde  = [0.3, 0.85, 0.4, 1]
        rojo   = [0.85, 0.3, 0.3, 1]
        gris   = [0.5, 0.5, 0.5, 1]

        if libro_ok:
            self.resultado_libro       = f"OK  Libro: {verso['book_name']}"
            self.resultado_color_libro = verde
        else:
            self.resultado_libro       = f"X   Libro: dijiste '{libro_input}'  era '{verso['book_name']}'"
            self.resultado_color_libro = rojo

        if libro_ok and cap_ok:
            self.resultado_cap       = f"OK  Capitulo: {verso['capitulo']}"
            self.resultado_color_cap = verde
        elif libro_ok:
            self.resultado_cap       = f"X   Capitulo: dijiste {cap_input}  era {verso['capitulo']}"
            self.resultado_color_cap = rojo
        else:
            self.resultado_cap       = f"--  Capitulo: era {verso['capitulo']}"
            self.resultado_color_cap = gris

        if libro_ok and cap_ok and vers_ok:
            self.resultado_vers       = f"OK  Versiculo: {verso['versiculo']}"
            self.resultado_color_vers = verde
        elif libro_ok and cap_ok:
            self.resultado_vers       = f"X   Versiculo: dijiste {vers_input}  era {verso['versiculo']}"
            self.resultado_color_vers = rojo
        else:
            self.resultado_vers       = f"--  Versiculo: era {verso['versiculo']}"
            self.resultado_color_vers = gris

        # Actualizar estadisticas de nivel_refuerzo
        self.capitulos_model.actualizar_estadisticas(verso['id'], acertado=(score >= 0.7))

        # Renovar vida del verso segun score (equitativo)
        registros = self.capitulos_model.get_by_usuario(1)
        vida_dias = self.capitulos_model.calcular_vida_dias(len(registros) if registros else 0)
        self.capitulos_model.renovar_verso(verso['id'], self.score_value, vida_dias)

        self.fase = 'resultado'

    def siguiente_verso(self):
        self._nuevo_verso()
