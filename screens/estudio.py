import json
from kivy.app import App
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout as KBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ListProperty
from screens.basescreen import BaseScreen
from screens.plantilla import BuscadorBiblico, RolloBiblico
from screens.work import _lbl, _canvas_bg


# ──────────────────────────────────────────────────────────────────
# Divisor arrastrable entre secciones
# ──────────────────────────────────────────────────────────────────

class DivisorArrastrable(Widget):
    """Barra draggable que redistribuye size_hint_y entre dos secciones."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(18)
        self._callback = None
        self._touch_y = None

    def set_callback(self, cb):
        self._callback = cb

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._touch_y = touch.y
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._touch_y is not None:
            delta = touch.y - self._touch_y
            self._touch_y = touch.y
            if self._callback:
                self._callback(delta)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._touch_y = None
            return True
        return super().on_touch_up(touch)


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _referencia_de_versos(versos):
    """Construye 'Juan 3:16-18; Romanos 8:28' desde lista de dicts."""
    if not versos:
        return ''
    grupos = {}
    orden = []
    for item in versos:
        key = (item['n'], item['c'])
        if key not in grupos:
            grupos[key] = []
            orden.append(key)
        grupos[key].append(int(item['v']))
    partes = []
    for key in orden:
        libro, cap = key
        vv = sorted(grupos[key])
        ref = f"{vv[0]}-{vv[-1]}" if len(vv) > 1 else str(vv[0])
        partes.append(f"{libro} {cap}:{ref}")
    return '; '.join(partes)


def _lib_nombre(path):
    """Extrae nombre corto de la ruta de una Biblia."""
    base = path.split('/')[-1].replace('.sqlite', '')
    # Prefer acronym in parentheses: "Reina-Valera 1960 (RVR1960)" → "RVR1960"
    if '(' in base and ')' in base:
        return base[base.index('(') + 1: base.index(')')]
    return base[:10]


# ──────────────────────────────────────────────────────────────────
# Página 1 – Lista de estudios
# ──────────────────────────────────────────────────────────────────

class EstudioScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.estudio_model = App.get_running_app().getModel('EstudioModel')

    def on_enter(self, *args):
        self._cargar_lista()

    def _cargar_lista(self):
        if 'estudios_list' not in self.ids:
            return
        container = self.ids.estudios_list
        container.clear_widgets()
        registros = self.estudio_model.get_by_usuario(1) or []
        if not registros:
            container.add_widget(Label(
                text="Sin estudios. Presiona '+ Nuevo Estudio'.",
                font_size='14sp', color=(0.5, 0.5, 0.62, 1),
                size_hint_y=None, height=dp(60),
                halign='center', text_size=(None, None),
            ))
            return
        for reg in registros:
            container.add_widget(self._fila_estudio(reg))

    def _fila_estudio(self, reg):
        titulo    = reg['titulo'] or 'Sin titulo'
        fecha     = reg['fecha_creacion'] or ''
        notas     = reg['notas'] or ''
        tiene_notas = bool(notas.strip())
        alto = dp(62) if tiene_notas else dp(46)

        fila = KBox(size_hint_y=None, height=alto, padding=(dp(12), dp(4)), spacing=dp(6))
        _canvas_bg(fila, (0.08, 0.08, 0.16, 1))

        with fila.canvas.before:
            Color(0.95, 0.78, 0.1, 0.75)
            rect = Rectangle(pos=(fila.x, fila.y), size=(dp(3), alto))
        fila.bind(pos=lambda i, v: setattr(rect, 'pos', (v[0], v[1])))
        fila.bind(size=lambda i, v: setattr(rect, 'size', (dp(3), v[1])))

        info = KBox(orientation='vertical', size_hint_x=0.70)
        info.add_widget(_lbl(titulo, 1, '14sp', (0.95, 0.88, 0.65, 1)))
        sub = fecha
        if tiene_notas:
            snippet = notas[:50] + ('...' if len(notas) > 50 else '')
            info.add_widget(_lbl(snippet, 1, '11sp', (0.6, 0.6, 0.72, 1)))
        else:
            info.add_widget(_lbl(sub, 1, '11sp', (0.5, 0.5, 0.62, 1)))
        fila.add_widget(info)

        btn_abrir = Button(text='Abrir', size_hint_x=0.16, font_size='12sp',
                           background_normal='',
                           background_color=(0.18, 0.38, 0.68, 0.9))
        btn_abrir.bind(on_release=lambda *_: self._abrir(reg['id']))

        btn_del = Button(text='X', size_hint_x=0.14, font_size='12sp',
                         background_normal='',
                         background_color=(0.45, 0.12, 0.12, 0.8))
        btn_del.bind(on_release=lambda *_: self._borrar(reg['id']))

        fila.add_widget(btn_abrir)
        fila.add_widget(btn_del)
        return fila

    def nuevo_estudio(self):
        detalle = self.manager.get_screen('estudio_detalle')
        detalle.cargar(None)
        self.manager.current = 'estudio_detalle'

    def _abrir(self, reg_id):
        detalle = self.manager.get_screen('estudio_detalle')
        detalle.cargar(reg_id)
        self.manager.current = 'estudio_detalle'

    def _borrar(self, reg_id):
        self.estudio_model.borrar(reg_id)
        self._cargar_lista()


# ──────────────────────────────────────────────────────────────────
# Página 2 – Editor de estudio
# ──────────────────────────────────────────────────────────────────

class EstudioDetalleScreen(BaseScreen):

    status_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.estudio_model = App.get_running_app().getModel('EstudioModel')
        self._biblioteca   = App.get_running_app().getModel('Biblioteca')
        self._estudio_id   = None
        self._versiculos   = []   # list of dicts: {b, c, v, n, lib, txt}
        self._biblias_map  = {}   # path → Biblia

    def on_kv_post(self, base_widget):
        if 'divisor' in self.ids:
            self.ids.divisor.set_callback(self._ajustar_secciones)

    def _ajustar_secciones(self, delta_px):
        arr = self.ids.get('versos_seccion')
        aba = self.ids.get('notas_seccion')
        if not arr or not aba:
            return
        flexible_h = arr.height + aba.height
        if flexible_h <= 0:
            return
        total_hint = arr.size_hint_y + aba.size_hint_y
        delta_hint = delta_px * total_hint / flexible_h
        min_hint = total_hint * 0.08
        new_arr = max(min_hint, arr.size_hint_y - delta_hint)
        new_aba = max(min_hint, total_hint - new_arr)
        if new_aba < min_hint:
            new_aba = min_hint
            new_arr = total_hint - new_aba
        arr.size_hint_y = new_arr
        aba.size_hint_y = new_aba

    def cargar(self, reg_id=None):
        """Llamar antes de navegar a esta pantalla."""
        self._estudio_id = reg_id
        self._versiculos = []

    def on_enter(self, *args):
        self._init_biblias()
        if self._estudio_id is not None:
            reg = self.estudio_model.get_one(self._estudio_id)
            if reg:
                if 'ti_titulo' in self.ids:
                    self.ids.ti_titulo.text = reg['titulo'] or ''
                if 'ti_notas' in self.ids:
                    self.ids.ti_notas.text = reg['notas'] or ''
                try:
                    self._versiculos = json.loads(reg['datos_json'] or '[]')
                except Exception:
                    self._versiculos = []
        else:
            if 'ti_titulo' in self.ids:
                self.ids.ti_titulo.text = ''
            if 'ti_notas' in self.ids:
                self.ids.ti_notas.text = ''
        self._render_versos()
        self.status_text = ''

    def _init_biblias(self):
        if not self._biblioteca or not self._biblioteca.get('contenido'):
            return
        self._biblias_map = {}
        for b in self._biblioteca['contenido']:
            if 'alternative' not in b.path.lower():
                self._biblias_map[b.path] = b

    def _get_biblia_por_path(self, path):
        if path in self._biblias_map:
            return self._biblias_map[path]
        # fallback: first available
        if self._biblias_map:
            return next(iter(self._biblias_map.values()))
        return None

    # ── Buscar y agregar versículos ────────────────────────────────

    def abrir_buscador(self):
        buscador = BuscadorBiblico(
            callback_finalizar=lambda sel: self._on_seleccion(sel, buscador)
        )
        buscador.open()

    def _on_seleccion(self, seleccion, buscador):
        if not seleccion:
            return
        biblia = buscador.get_biblia()
        lib_path = biblia.path if biblia else ''
        for r in seleccion:
            self._versiculos.append({
                'b':   r['idBook'],
                'c':   r['chapter'],
                'v':   r['verse'],
                'n':   r['nameBook'],
                'lib': lib_path,
                'txt': r['text'] or '',
            })
        self._render_versos()

    def _remover_verso(self, idx):
        if 0 <= idx < len(self._versiculos):
            del self._versiculos[idx]
            self._render_versos()

    # ── Renderizado de versículos ──────────────────────────────────

    def _render_versos(self):
        if 'versos_list' not in self.ids:
            return
        container = self.ids.versos_list
        container.clear_widgets()

        if not self._versiculos:
            container.add_widget(Label(
                text='Agrega versiculos con el boton "+".',
                font_size='12sp', color=(0.4, 0.4, 0.55, 1),
                size_hint_y=None, height=dp(36),
                halign='center', text_size=(None, None),
            ))
            return

        for idx, item in enumerate(self._versiculos):
            container.add_widget(self._fila_verso(item, idx))

    def _fila_verso(self, item, idx):
        lib_badge = _lib_nombre(item.get('lib', ''))
        texto = item.get('txt', '')

        outer = KBox(size_hint_y=None, spacing=dp(6), padding=(dp(8), dp(4)))
        _canvas_bg(outer, (0.09, 0.09, 0.18, 1))

        # Left accent (green)
        with outer.canvas.before:
            Color(0.3, 0.75, 0.45, 0.7)
            acc = Rectangle(pos=(outer.x, outer.y), size=(dp(3), dp(60)))
        outer.bind(pos=lambda i, v: setattr(acc, 'pos', (v[0], v[1])))

        col = KBox(orientation='vertical', size_hint=(0.84, None))
        col.bind(minimum_height=col.setter('height'))

        # Reference row: badge + book:ch:v
        ref_row = KBox(size_hint_y=None, height=dp(20), spacing=dp(6))
        lbl_badge = Label(
            text=lib_badge, font_size='9sp', bold=True,
            size_hint=(None, 1), width=dp(68),
            color=(0.95, 0.78, 0.1, 1), halign='left',
        )
        lbl_badge.bind(size=lambda w, v: setattr(w, 'text_size', v))
        lbl_ref = Label(
            text=f"{item['n']}  {item['c']}:{item['v']}",
            font_size='11sp', color=(0.7, 0.7, 0.85, 1), halign='left',
        )
        lbl_ref.bind(size=lambda w, v: setattr(w, 'text_size', v))
        ref_row.add_widget(lbl_badge)
        ref_row.add_widget(lbl_ref)

        # Verse text (wrapping, auto-height)
        lbl_txt = Label(
            text=texto, font_size='13sp',
            color=(0.88, 0.88, 0.92, 1),
            size_hint_y=None, halign='left', valign='top',
        )
        lbl_txt.bind(
            width=lambda w, v: setattr(w, 'text_size', (v, None)),
            texture_size=lambda w, v: setattr(w, 'height', v[1]),
        )

        col.add_widget(ref_row)
        col.add_widget(lbl_txt)

        btn_x = Button(
            text='X', size_hint=(None, None), size=(dp(28), dp(28)),
            background_normal='', background_color=(0.45, 0.12, 0.12, 0.85),
            font_size='11sp',
        )
        btn_x.bind(on_release=lambda *_, i=idx: self._remover_verso(i))

        outer.add_widget(col)
        outer.add_widget(btn_x)

        # Propagate col height → outer height
        col.bind(height=lambda inst, val: setattr(outer, 'height', val + dp(10)))
        outer.height = dp(70)  # initial estimate

        return outer

    def leer_en_rollo(self):
        """Re-carga versículos desde sus Biblias originales y abre RolloBiblico."""
        if not self._versiculos:
            self.status_text = 'Sin versiculos cargados'
            return
        regs = []
        for item in self._versiculos:
            biblia = self._get_biblia_por_path(item.get('lib', ''))
            if not biblia:
                continue
            res = biblia.buscarVersiculo(item['n'], item['c'], item['v'], item['b'])
            if res:
                regs.append(res[0])
        if regs:
            RolloBiblico().mostrar_pasaje(0, ContenidoTotal=regs)

    # ── Guardar ────────────────────────────────────────────────────

    def guardar(self):
        titulo = self.ids.ti_titulo.text.strip() if 'ti_titulo' in self.ids else ''
        notas  = self.ids.ti_notas.text.strip()  if 'ti_notas'  in self.ids else ''
        datos  = json.dumps(self._versiculos)

        if self._estudio_id is not None:
            self.estudio_model.actualizar(
                self._estudio_id,
                titulo=titulo,
                datos_json=datos,
                notas=notas,
            )
        else:
            new_id = self.estudio_model.insertar(
                titulo=titulo,
                datos_json=datos,
                notas=notas,
            )
            self._estudio_id = new_id

        self.status_text = 'Guardado!'

    def volver(self):
        self.manager.current = 'estudio'
