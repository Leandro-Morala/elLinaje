import json
import os
import re
from datetime import datetime
from kivy.app import App
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout as KBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from screens.basescreen import BaseScreen
from screens.plantilla import BuscadorBiblico, RolloBiblico
from screens.work import _lbl, _canvas_bg


# ──────────────────────────────────────────────────────────────────
# Helpers de exportación / importación
# ──────────────────────────────────────────────────────────────────

_RE_TAG = re.compile(r'\[/?[^\]]+\]')


def _strip_markup(text):
    return _RE_TAG.sub('', text or '')


def _kivy_a_rl(text):
    """Convierte markup Kivy a markup compatible con ReportLab Paragraph."""
    t = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = t.replace('[b]', '<b>').replace('[/b]', '</b>')
    t = t.replace('[i]', '<i>').replace('[/i]', '</i>')
    t = re.sub(r'\[size=(\d+)\]', r'<font size="\1">', t)
    t = t.replace('[/size]', '</font>')
    t = re.sub(r'\[color=([^\]]+)\]', lambda m: f'<font color="#{m.group(1)}">', t)
    t = t.replace('[/color]', '</font>')
    t = _RE_TAG.sub('', t)   # elimina tags Kivy restantes
    return t


def _nombre_seguro(titulo, ext):
    base = re.sub(r'[^\w\s-]', '', titulo or 'estudio').strip().replace(' ', '_')
    fecha = datetime.now().strftime('%Y%m%d_%H%M')
    return f"{base or 'estudio'}_{fecha}.{ext}"


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

    # ── Exportar ──────────────────────────────────────────────────

    def exportar_popup(self):
        registros = self.estudio_model.get_by_usuario(1) or []
        if not registros:
            self.echo('No hay estudios para exportar.')
            return

        content = KBox(orientation='vertical', padding=dp(10), spacing=dp(6))
        _canvas_bg(content, (0.07, 0.07, 0.14, 1))

        content.add_widget(Label(
            text='Seleccionar estudio', size_hint_y=None, height=dp(28),
            font_size='14sp', bold=True, color=(0.95, 0.88, 0.65, 1),
        ))

        scroll = ScrollView(size_hint_y=1)
        lista = KBox(orientation='vertical', size_hint_y=None, spacing=dp(3))
        lista.bind(minimum_height=lista.setter('height'))
        btn_group = []
        for reg in registros:
            btn = ToggleButton(
                text=(reg['titulo'] or 'Sin título')[:42],
                size_hint_y=None, height=dp(40),
                group='export_sel', font_size='13sp',
                background_normal='', background_down='',
                background_color=(0.13, 0.13, 0.24, 1),
                color=(0.88, 0.88, 0.95, 1),
            )
            btn._reg = reg
            btn_group.append(btn)
            lista.add_widget(btn)
        if btn_group:
            btn_group[0].state = 'down'
            btn_group[0].background_color = (0.18, 0.35, 0.65, 1)
        for b in btn_group:
            def _on_toggle(inst, val, _b=b, _all=btn_group):
                for x in _all:
                    x.background_color = (0.18, 0.35, 0.65, 1) if x.state == 'down' else (0.13, 0.13, 0.24, 1)
            b.bind(state=_on_toggle)
        scroll.add_widget(lista)
        content.add_widget(scroll)

        content.add_widget(Label(
            text='Formato de exportación', size_hint_y=None, height=dp(22),
            font_size='12sp', color=(0.6, 0.7, 0.8, 1),
        ))
        fmt_box = KBox(size_hint_y=None, height=dp(38), spacing=dp(16),
                       padding=(dp(8), 0))
        cb_txt = CheckBox(group='fmt_exp', active=True,
                          size_hint_x=None, width=dp(28))
        cb_pdf = CheckBox(group='fmt_exp', active=False,
                          size_hint_x=None, width=dp(28))
        lbl_txt = Label(text='TXT  (texto plano con tags de formato)',
                        font_size='12sp', color=(0.80, 0.92, 0.80, 1),
                        halign='left', text_size=(None, None))
        lbl_pdf = Label(text='PDF  (documento con formato visual)',
                        font_size='12sp', color=(0.80, 0.85, 0.95, 1),
                        halign='left', text_size=(None, None))
        row_txt = KBox(size_hint_y=None, height=dp(34), spacing=dp(4))
        row_txt.add_widget(cb_txt)
        row_txt.add_widget(lbl_txt)
        row_pdf = KBox(size_hint_y=None, height=dp(34), spacing=dp(4))
        row_pdf.add_widget(cb_pdf)
        row_pdf.add_widget(lbl_pdf)
        fmt_col = KBox(orientation='vertical', size_hint_y=None, height=dp(72))
        fmt_col.add_widget(row_txt)
        fmt_col.add_widget(row_pdf)
        content.add_widget(fmt_col)

        act_box = KBox(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup_ref = [None]

        def _do_export(_inst):
            reg = next((b._reg for b in btn_group if b.state == 'down'), None)
            if not reg:
                return
            fmt = 'pdf' if cb_pdf.active else 'txt'
            popup_ref[0].dismiss()
            self._hacer_export(reg, fmt)

        btn_cancel = Button(text='Cancelar', background_normal='',
                            background_color=(0.28, 0.28, 0.28, 0.9), font_size='13sp')
        btn_exp = Button(text='Exportar ▶', background_normal='',
                         background_color=(0.18, 0.45, 0.78, 1), font_size='13sp', bold=True)
        btn_exp.bind(on_release=_do_export)
        act_box.add_widget(btn_cancel)
        act_box.add_widget(btn_exp)
        content.add_widget(act_box)

        popup = Popup(title='Exportar Estudio Bíblico', content=content,
                      size_hint=(0.93, 0.78),
                      background='', background_color=(0.05, 0.05, 0.12, 0.97))
        btn_cancel.bind(on_release=popup.dismiss)
        popup_ref[0] = popup
        popup.open()

    def _hacer_export(self, reg, fmt):
        reg = dict(reg)
        nombre = _nombre_seguro(reg.get('titulo', ''), fmt)

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            def _cb(perms, results):
                if all(results):
                    self._abrir_file_chooser_export(reg, fmt, nombre)
                else:
                    self.echo('Permisos denegados.')
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ], _cb)
        else:
            self._abrir_file_chooser_export(reg, fmt, nombre)

    def _abrir_file_chooser_export(self, reg, fmt, nombre_sugerido):
        content = KBox(orientation='vertical', padding=dp(10), spacing=dp(8))
        _canvas_bg(content, (0.07, 0.07, 0.14, 1))

        content.add_widget(Label(
            text=f'Guardar como:  [b]{nombre_sugerido}[/b]',
            markup=True, size_hint_y=None, height=dp(28),
            font_size='12sp', color=(0.75, 0.85, 0.95, 1),
            halign='left', text_size=(None, None),
        ))

        fc = FileChooserListView(
            path=self._get_storage_path(),
            dirselect=True,
        )
        content.add_widget(fc)

        act_box = KBox(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup_ref = [None]

        def _do_save(_inst):
            carpeta = fc.selection[0] if fc.selection else fc.path
            if not os.path.isdir(carpeta):
                carpeta = os.path.dirname(carpeta)
            ruta = os.path.join(carpeta, nombre_sugerido)
            popup_ref[0].dismiss()
            try:
                if fmt == 'txt':
                    self._exportar_txt(reg, ruta)
                else:
                    self._exportar_pdf(reg, ruta)
                self.echo(f'Guardado: {ruta}')
                Logger.info(f'[export] {ruta}')
            except Exception as e:
                Logger.error(f'[export] {e}')
                self.echo(f'Error: {e}')

        btn_cancel = Button(text='Cancelar', background_normal='',
                            background_color=(0.28, 0.28, 0.28, 0.9), font_size='13sp')
        btn_save = Button(text='Guardar aquí ▶', background_normal='',
                          background_color=(0.18, 0.45, 0.78, 1), font_size='13sp', bold=True)
        btn_save.bind(on_release=_do_save)
        act_box.add_widget(btn_cancel)
        act_box.add_widget(btn_save)
        content.add_widget(act_box)

        popup = Popup(title='Elegir ubicación para guardar', content=content,
                      size_hint=(0.93, 0.85),
                      background='', background_color=(0.05, 0.05, 0.12, 0.97))
        btn_cancel.bind(on_release=popup.dismiss)
        popup_ref[0] = popup
        popup.open()

    def _exportar_txt(self, reg, ruta):
        titulo  = reg.get('titulo') or 'Sin título'
        fecha   = reg.get('fecha_creacion') or ''
        notas   = reg.get('notas') or ''          # conserva tags de formato Kivy
        try:
            versos = json.loads(reg.get('datos_json') or '[]')
        except Exception:
            versos = []

        sep   = '=' * 54
        sep2  = '─' * 54
        lines = [
            sep,
            '  EL LINAJE — ESTUDIO BÍBLICO',
            sep,
            f'TITULO   : {titulo}',
            f'FECHA    : {fecha}',
            f'EXPORTADO: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            '', '── NOTAS ' + '─' * 45, '',
            notas,
            '',
        ]
        if versos:
            lines += ['── BIBLIOGRAFÍA ' + '─' * 38, '']
            for i, v in enumerate(versos, 1):
                lib = _lib_nombre(v.get('lib', ''))
                lines.append(f'[{i}] {v["n"]}  {v["c"]}:{v["v"]}  —  {lib}')
                if v.get('txt'):
                    lines.append(f'    "{v["txt"]}"')
                lines.append('')
            # Sección legible por máquina para reimportación
            lines += ['── DATOS (no modificar) ' + '─' * 30]
            for v in versos:
                txt_e = v.get('txt', '').replace('|', '/')
                lines.append(
                    f'__VERSO__:{v["b"]}|{v["c"]}|{v["v"]}|{v["n"]}|{v.get("lib","")}|{txt_e}'
                )
        lines.append(sep)

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _exportar_pdf(self, reg, ruta):
        from fpdf import FPDF, XPos, YPos

        titulo = reg.get('titulo') or 'Sin título'
        fecha  = reg.get('fecha_creacion') or ''
        notas  = reg.get('notas') or ''
        try:
            versos = json.loads(reg.get('datos_json') or '[]')
        except Exception:
            versos = []

        NL = {'new_x': XPos.LMARGIN, 'new_y': YPos.NEXT}

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_margins(left=25, top=22, right=25)
        pdf.set_auto_page_break(auto=True, margin=22)
        pdf.add_page()

        # Encabezado app
        pdf.set_font('Helvetica', size=9)
        pdf.set_text_color(100, 100, 110)
        pdf.cell(0, 5, 'El Linaje — Estudio Bíblico', **NL)
        pdf.ln(1)

        # Título del estudio
        pdf.set_font('Helvetica', style='B', size=20)
        pdf.set_text_color(30, 58, 110)
        pdf.multi_cell(0, 10, titulo)
        pdf.ln(1)

        # Fecha — izquierda, separada del título
        pdf.set_font('Helvetica', size=9)
        pdf.set_text_color(100, 100, 110)
        pdf.cell(0, 5,
                 f'Fecha: {fecha}   |   Exportado: {datetime.now().strftime("%Y-%m-%d")}',
                 **NL)
        pdf.ln(3)

        # Línea separadora azul
        pdf.set_draw_color(30, 58, 110)
        pdf.set_line_width(0.5)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.epw, pdf.get_y())
        pdf.ln(5)

        # Sección notas
        pdf.set_font('Helvetica', style='B', size=13)
        pdf.set_text_color(30, 58, 110)
        pdf.cell(0, 7, 'Notas', **NL)
        pdf.ln(2)

        pdf.set_text_color(30, 30, 30)
        for linea in notas.split('\n'):
            texto = _strip_markup(linea)
            es_titulo = '[size=18]' in linea or ('[b]' in linea and len(linea) < 120)
            if es_titulo and texto.strip():
                pdf.set_font('Helvetica', style='B', size=12)
            else:
                pdf.set_font('Helvetica', size=11)
            if texto.strip():
                pdf.multi_cell(0, 6, texto)
            else:
                pdf.ln(3)

        # Bibliografía
        if versos:
            pdf.ln(4)
            pdf.set_draw_color(120, 120, 120)
            pdf.set_line_width(0.3)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.epw, pdf.get_y())
            pdf.ln(4)

            pdf.set_font('Helvetica', style='B', size=13)
            pdf.set_text_color(30, 58, 110)
            pdf.cell(0, 7, 'Bibliografía', **NL)
            pdf.ln(2)

            for i, v in enumerate(versos, 1):
                lib = _lib_nombre(v.get('lib', ''))
                ref = f'[{i}]  {v["n"]}  {v["c"]}:{v["v"]}  —  {lib}'
                pdf.set_font('Helvetica', style='B', size=10)
                pdf.set_text_color(26, 95, 62)
                pdf.cell(0, 5, ref, **NL)
                if v.get('txt'):
                    pdf.set_font('Helvetica', style='I', size=10)
                    pdf.set_text_color(40, 40, 40)
                    pdf.set_x(pdf.get_x() + 10)
                    pdf.multi_cell(pdf.epw - 10, 5, f'\u00ab{v["txt"]}\u00bb')
                pdf.ln(2)

        pdf.output(ruta)

    # ── Importar ──────────────────────────────────────────────────

    def importar_popup(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            def _cb(perms, results):
                if all(results):
                    self._abrir_file_chooser_import()
                else:
                    self.echo('Permisos denegados.')
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ], _cb)
        else:
            self._abrir_file_chooser_import()

    def _abrir_file_chooser_import(self):
        content = KBox(orientation='vertical', padding=dp(10), spacing=dp(8))
        _canvas_bg(content, (0.07, 0.07, 0.14, 1))

        fc = FileChooserListView(
            path=self._get_storage_path(),
            filters=['*.txt'],
        )
        content.add_widget(fc)

        act_box = KBox(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup_ref = [None]

        def _do_import(_inst):
            if not fc.selection:
                self.echo('Selecciona un archivo .txt')
                return
            popup_ref[0].dismiss()
            try:
                self._importar_txt(fc.selection[0])
                self._cargar_lista()
                self.echo('Estudio importado.')
            except Exception as e:
                Logger.error(f'[import] {e}')
                self.echo(f'Error al importar: {e}')

        btn_cancel = Button(text='Cancelar', background_normal='',
                            background_color=(0.28, 0.28, 0.28, 0.9), font_size='13sp')
        btn_imp = Button(text='Importar ▶', background_normal='',
                         background_color=(0.22, 0.52, 0.28, 1), font_size='13sp', bold=True)
        btn_imp.bind(on_release=_do_import)
        act_box.add_widget(btn_cancel)
        act_box.add_widget(btn_imp)
        content.add_widget(act_box)

        popup = Popup(title='Importar Estudio (.txt)', content=content,
                      size_hint=(0.93, 0.82),
                      background='', background_color=(0.05, 0.05, 0.12, 0.97))
        btn_cancel.bind(on_release=popup.dismiss)
        popup_ref[0] = popup
        popup.open()

    def _importar_txt(self, ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            texto = f.read()

        titulo = ''
        m = re.search(r'^TITULO\s*:\s*(.+)$', texto, re.MULTILINE)
        if m:
            titulo = m.group(1).strip()

        notas = ''
        m = re.search(r'── NOTAS .+\n\n?(.*?)(?=── BIBLIOGRAFÍA|── DATOS|={10})',
                      texto, re.DOTALL)
        if m:
            notas = m.group(1).strip()

        versos = []
        for m in re.finditer(r'^__VERSO__:(.+)$', texto, re.MULTILINE):
            parts = m.group(1).split('|')
            if len(parts) >= 5:
                versos.append({
                    'b':   int(parts[0]),
                    'c':   int(parts[1]),
                    'v':   int(parts[2]),
                    'n':   parts[3],
                    'lib': parts[4],
                    'txt': parts[5] if len(parts) > 5 else '',
                })

        self.estudio_model.insertar(
            titulo=titulo or os.path.basename(ruta),
            datos_json=json.dumps(versos),
            notas=notas,
        )


# ──────────────────────────────────────────────────────────────────
# Página 2 – Editor de estudio
# ──────────────────────────────────────────────────────────────────

class EstudioDetalleScreen(BaseScreen):

    status_text  = StringProperty('')
    modo_edicion = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.estudio_model = App.get_running_app().getModel('EstudioModel')
        self._biblioteca   = App.get_running_app().getModel('Biblioteca')
        self._estudio_id   = None
        self._versiculos   = []   # list of dicts: {b, c, v, n, lib, txt}
        self._biblias_map  = {}   # path → Biblia
        self._ultima_accion = None

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
        new_arr = max(min_hint, arr.size_hint_y + delta_hint)
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
        # asegurar modo edición al entrar
        if not self.modo_edicion:
            ti     = self.ids.get('ti_notas')
            scroll = self.ids.get('preview_scroll')
            if ti and scroll:
                scroll.size_hint_y = None
                scroll.height      = 0
                ti.size_hint_y     = 1
                ti.disabled        = False
            self.modo_edicion = True
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

    # ── Toggle edición / preview ───────────────────────────────────

    def toggle_preview(self):
        ti     = self.ids.get('ti_notas')
        scroll = self.ids.get('preview_scroll')
        lbl    = self.ids.get('lbl_preview')
        if not all([ti, scroll, lbl]):
            return
        self.modo_edicion = not self.modo_edicion
        if self.modo_edicion:
            scroll.size_hint_y = None
            scroll.height      = 0
            ti.size_hint_y     = 1
            ti.disabled        = False
        else:
            lbl.text           = ti.text
            ti.size_hint_y     = None
            ti.height          = 0
            ti.disabled        = True
            scroll.size_hint_y = 1

    # ── Barra de herramientas de texto (markup Kivy) ───────────────

    def _ti_notas(self):
        return self.ids.get('ti_notas')

    def _inicio_linea(self, ti):
        idx = ti.cursor_index()
        start = ti.text.rfind('\n', 0, idx)
        return start + 1 if start >= 0 else 0

    def _fin_linea(self, ti):
        idx = ti.cursor_index()
        end = ti.text.find('\n', idx)
        return end if end != -1 else len(ti.text)

    def titulo(self):
        ti = self._ti_notas()
        if not ti:
            return
        start = self._inicio_linea(ti)
        end   = self._fin_linea(ti)
        linea = ti.text[start:end]
        pre, suf = '[size=18][b]', '[/b][/size]'
        if linea.startswith(pre) and linea.endswith(suf):
            nueva = linea[len(pre):-len(suf)]
        else:
            nueva = pre + linea + suf
        ti.text   = ti.text[:start] + nueva + ti.text[end:]
        ti.cursor = ti.get_cursor_from_index(start + len(nueva))
        self._ultima_accion = 'titulo'

    def lista(self):
        ti = self._ti_notas()
        if not ti:
            return
        cursor_idx = ti.cursor_index()
        start = self._inicio_linea(ti)
        prefijo = '• '
        if ti.text[start:start + len(prefijo)] == prefijo:
            return
        ti.text   = ti.text[:start] + prefijo + ti.text[start:]
        ti.cursor = ti.get_cursor_from_index(cursor_idx + len(prefijo))
        self._ultima_accion = 'lista'

    def formato(self):
        ti = self._ti_notas()
        if not ti:
            return
        sel = ti.selection_text
        if sel:
            s, e = sorted([ti.selection_from, ti.selection_to])
            ti.text = ti.text[:s] + '[b]' + sel + '[/b]' + ti.text[e:]
            ti.cancel_selection()
            ti.cursor = ti.get_cursor_from_index(s + len(sel) + 7)
        else:
            idx = ti.cursor_index()
            ti.text   = ti.text[:idx] + '[b][/b]' + ti.text[idx:]
            ti.cursor = ti.get_cursor_from_index(idx + 3)
        self._ultima_accion = 'formato'

    def repetir(self):
        if not self._ultima_accion:
            return
        if self._ultima_accion == 'titulo':
            self.titulo()
        elif self._ultima_accion == 'lista':
            self.lista()
        elif self._ultima_accion == 'formato':
            self.formato()

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
