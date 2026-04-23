from datetime import datetime
from kivy.app import App
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout as KivyBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.utils import platform
from kivy.core.window import Window
from screens.basescreen import BaseScreen

MESES_ES = ['Todos', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def _mes_str_to_num(mes_str):
    """'Ene' -> '01', 'Feb' -> '02', etc."""
    try:
        idx = MESES_ES.index(mes_str)
        return str(idx).zfill(2)
    except ValueError:
        return None


def _parse_fecha(texto):
    """Acepta dd/mm/yyyy o yyyy-mm-dd; devuelve 'YYYY-MM-DD' o None."""
    t = texto.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(t, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None


def _fecha_display(iso_str):
    """'2025-03-15' -> '15/03/2025'"""
    try:
        return datetime.strptime(iso_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return iso_str or '—'


def _ts_display(ts):
    """unix timestamp -> '15/03/2025'"""
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
    except Exception:
        return '—'


def _ts_to_iso(ts):
    """unix timestamp -> 'YYYY-MM-DD'"""
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except Exception:
        return ''


# ------------------------------------------------------------------
# Modal selector de fecha (touch-friendly, especialmente para Android)
# ------------------------------------------------------------------

class FechaPicker(ModalView):
    def __init__(self, callback, fecha_inicial=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint  = (0.88, None)
        self.height     = dp(260)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.7)
        self._callback = callback

        hoy = fecha_inicial or datetime.now()

        contenedor = KivyBox(orientation='vertical', padding=dp(14), spacing=dp(10))
        with contenedor.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.1, 0.1, 0.22, 1)
            self._bg = RoundedRectangle(pos=contenedor.pos, size=contenedor.size, radius=[dp(12)])
        contenedor.bind(pos=lambda i, v: setattr(self._bg, 'pos', v))
        contenedor.bind(size=lambda i, v: setattr(self._bg, 'size', v))

        titulo = Label(text="Seleccionar Fecha", font_size='15sp', bold=True,
                       color=(0.95, 0.78, 0.1, 1), size_hint_y=None, height=dp(30))
        contenedor.add_widget(titulo)

        dias   = [str(i).zfill(2) for i in range(1, 32)]
        meses  = [str(i).zfill(2) for i in range(1, 13)]
        anios  = [str(y) for y in range(2020, datetime.now().year + 3)]

        row = KivyBox(size_hint_y=None, height=dp(50), spacing=dp(8))
        sp_kw = dict(background_normal='', background_color=(0.18, 0.18, 0.35, 1),
                     color=(0.95, 0.95, 0.9, 1), font_size='14sp')

        self.sp_dia  = Spinner(text=str(hoy.day).zfill(2),   values=dias,   **sp_kw)
        self.sp_mes  = Spinner(text=str(hoy.month).zfill(2), values=meses,  **sp_kw)
        self.sp_anio = Spinner(text=str(hoy.year),            values=anios,  **sp_kw)

        row.add_widget(self.sp_dia)
        row.add_widget(self.sp_mes)
        row.add_widget(self.sp_anio)
        contenedor.add_widget(row)

        btns = KivyBox(size_hint_y=None, height=dp(46), spacing=dp(8))
        btn_ok = Button(text="Confirmar", background_normal='',
                        background_color=(0.18, 0.45, 0.78, 1), font_size='14sp', bold=True)
        btn_cancel = Button(text="Cancelar", background_normal='',
                            background_color=(0.3, 0.3, 0.3, 0.8), font_size='14sp')
        btn_ok.bind(on_release=self._confirmar)
        btn_cancel.bind(on_release=lambda *_: self.dismiss())
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        contenedor.add_widget(btns)

        self.add_widget(contenedor)

    def _confirmar(self, *_):
        fecha_iso = f"{self.sp_anio.text}-{self.sp_mes.text}-{self.sp_dia.text}"
        self._callback(fecha_iso)
        self.dismiss()


# ------------------------------------------------------------------
# Pantalla principal
# ------------------------------------------------------------------

class WorkScreen(BaseScreen):
    """Panel unificado de Colaboraciones (servicio) y Ofrendas (monetarias)."""

    total_horas    = StringProperty("0.0 h de servicio")
    total_ofrendas = StringProperty("$ 0.00 ofrendado")
    status_colab   = StringProperty("")
    status_ofrenda = StringProperty("")

    editing_colab   = BooleanProperty(False)
    editing_ofrenda = BooleanProperty(False)

    colab_anios_lista   = ListProperty(['Todos'])
    ofrenda_anios_lista = ListProperty(['Todos'])
    list_max_height     = NumericProperty(300)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trabajos_model = App.get_running_app().getModel('TrabajosModel')
        self.ofrendas_model = App.get_running_app().getModel('OfrendasModel')
        self._colab_editing_id   = None
        self._ofrenda_editing_id = None
        self._filter_colab_anio  = None
        self._filter_colab_mes   = None
        self._filter_ofrenda_anio = None
        self._filter_ofrenda_mes  = None

    def on_enter(self, *args):
        self.list_max_height = max(150, Window.height * 0.42)
        self._set_default_dates()
        self._actualizar_filtros()
        self._cargar_colaboraciones()
        self._cargar_ofrendas()

    def _set_default_dates(self):
        hoy = datetime.now().strftime('%d/%m/%Y')
        if 'fecha_colab' in self.ids and not self.ids.fecha_colab.text:
            self.ids.fecha_colab.text = hoy
        if 'fecha_ofrenda' in self.ids and not self.ids.fecha_ofrenda.text:
            self.ids.fecha_ofrenda.text = hoy

    def _actualizar_filtros(self):
        anios_c = self.trabajos_model.get_anios() or []
        self.colab_anios_lista = ['Todos'] + anios_c
        anios_o = self.ofrendas_model.get_anios(1) or []
        self.ofrenda_anios_lista = ['Todos'] + anios_o

    # ------------------------------------------------------------------
    # Callbacks de filtros
    # ------------------------------------------------------------------

    def on_filter_colab(self, anio, mes):
        self._filter_colab_anio = None if anio == 'Todos' else anio
        self._filter_colab_mes  = _mes_str_to_num(mes) if mes != 'Todos' else None
        self._cargar_colaboraciones()

    def on_filter_ofrenda(self, anio, mes):
        self._filter_ofrenda_anio = None if anio == 'Todos' else anio
        self._filter_ofrenda_mes  = _mes_str_to_num(mes) if mes != 'Todos' else None
        self._cargar_ofrendas()

    # ------------------------------------------------------------------
    # Date picker
    # ------------------------------------------------------------------

    def abrir_fecha_picker(self, seccion):
        campo_id = 'fecha_colab' if seccion == 'colab' else 'fecha_ofrenda'
        if campo_id not in self.ids:
            return
        texto = self.ids[campo_id].text.strip()
        iso = _parse_fecha(texto)
        try:
            dt = datetime.strptime(iso, '%Y-%m-%d') if iso else datetime.now()
        except Exception:
            dt = datetime.now()

        def _on_fecha(fecha_iso):
            self.ids[campo_id].text = _fecha_display(fecha_iso)

        FechaPicker(callback=_on_fecha, fecha_inicial=dt).open()

    # ------------------------------------------------------------------
    # Colaboraciones
    # ------------------------------------------------------------------

    def _cargar_colaboraciones(self):
        if 'colab_list' not in self.ids:
            return
        container = self.ids.colab_list
        container.clear_widgets()
        registros = self.trabajos_model.get_filtrado(
            anio=self._filter_colab_anio,
            mes=self._filter_colab_mes,
            limit=500,
        ) or []
        total_h = 0.0
        for r in registros:
            fecha_iso = r['tiempo_inicio'] or ''
            horas_s   = r['tiempo_acumulado'] or '0'
            desc      = r['objservaciones'] or ''
            try:
                total_h += float(horas_s)
            except ValueError:
                pass
            container.add_widget(
                self._fila_colab(r['id'], fecha_iso, horas_s, desc)
            )
        self.total_horas = f"{total_h:.1f} h de servicio registradas"

    def _fila_colab(self, reg_id, fecha_iso, horas, desc):
        fecha_disp = _fecha_display(fecha_iso)
        row = KivyBox(size_hint_y=None, height=dp(44), spacing=dp(3), padding=(dp(6), dp(2)))
        _canvas_bg(row, (0.1, 0.1, 0.2, 1))
        row.add_widget(_lbl(fecha_disp,      0.28, '12sp', (0.75, 0.75, 0.8, 1)))
        row.add_widget(_lbl(f"{horas} h",    0.17, '12sp', (0.95, 0.78, 0.1, 1), align='center'))
        row.add_widget(_lbl(desc,            0.39, '11sp', (0.65, 0.65, 0.7, 1)))
        btn_e = Button(text='✏', size_hint_x=0.08, font_size='13sp',
                       background_normal='', background_color=(0.18, 0.38, 0.7, 1))
        btn_x = Button(text='✗', size_hint_x=0.08, font_size='13sp',
                       background_normal='', background_color=(0.55, 0.15, 0.15, 1))
        btn_e.bind(on_release=lambda *_: self.editar_colaboracion(reg_id))
        btn_x.bind(on_release=lambda *_: self._borrar_colab(reg_id))
        row.add_widget(btn_e)
        row.add_widget(btn_x)
        return row

    def editar_colaboracion(self, reg_id):
        r = self.trabajos_model.get_one(reg_id)
        if not r:
            return
        self._colab_editing_id = reg_id
        self.editing_colab = True
        if 'fecha_colab' in self.ids:
            self.ids.fecha_colab.text  = _fecha_display(r['tiempo_inicio'] or '')
            self.ids.horas_colab.text  = str(r['tiempo_acumulado'] or '')
            self.ids.desc_colab.text   = str(r['objservaciones'] or '')
        self.status_colab = "Editando registro de servicio..."

    def guardar_colaboracion(self, fecha_txt, horas_txt, desc_txt):
        iso = _parse_fecha(fecha_txt)
        if not iso:
            self.status_colab = "Fecha invalida — usa dd/mm/yyyy"
            return
        try:
            horas = float(horas_txt.strip())
            if horas <= 0:
                raise ValueError
        except ValueError:
            self.status_colab = "Ingresa horas validas (ej: 2.5)"
            return

        if self.editing_colab and self._colab_editing_id:
            ok = self.trabajos_model.actualizar(
                self._colab_editing_id,
                tiempo_inicio=iso,
                tiempo_acumulado=str(horas),
                objservaciones=desc_txt.strip(),
            )
            self.status_colab = "Colaboracion actualizada" if ok else "Error al actualizar"
        else:
            ok = self.trabajos_model.insertar(fecha=iso, duracion_horas=horas,
                                              descripcion=desc_txt.strip())
            self.status_colab = f"Colaboracion guardada  ({horas} h el {_fecha_display(iso)})" if ok else "Error al guardar"

        if ok:
            self._reset_form_colab()
            self._actualizar_filtros()
            self._cargar_colaboraciones()

    def cancelar_edicion_colab(self):
        self._reset_form_colab()

    def _borrar_colab(self, reg_id):
        self.trabajos_model.borrar(reg_id)
        self._actualizar_filtros()
        self._cargar_colaboraciones()

    def _reset_form_colab(self):
        self._colab_editing_id = None
        self.editing_colab = False
        self.status_colab  = ""
        if 'fecha_colab' not in self.ids:
            return
        self.ids.fecha_colab.text = datetime.now().strftime('%d/%m/%Y')
        self.ids.horas_colab.text = ''
        self.ids.desc_colab.text  = ''

    # ------------------------------------------------------------------
    # Ofrendas
    # ------------------------------------------------------------------

    def _cargar_ofrendas(self):
        if 'ofrenda_list' not in self.ids:
            return
        container = self.ids.ofrenda_list
        container.clear_widgets()
        registros = self.ofrendas_model.get_filtrado(
            id_usuario=1,
            anio=self._filter_ofrenda_anio,
            mes=self._filter_ofrenda_mes,
            limit=500,
        ) or []
        total = 0.0
        for r in registros:
            ts    = r['fecha']
            monto = float(r['monto'] or 0)
            total += monto
            desc  = r['descripcion'] or ''
            container.add_widget(
                self._fila_ofrenda(r['id'], ts, monto, desc)
            )
        self.total_ofrendas = f"$ {total:.2f} ofrendado en total"

    def _fila_ofrenda(self, reg_id, ts, monto, desc):
        fecha_disp = _ts_display(ts)
        row = KivyBox(size_hint_y=None, height=dp(44), spacing=dp(3), padding=(dp(6), dp(2)))
        _canvas_bg(row, (0.07, 0.14, 0.1, 1))
        row.add_widget(_lbl(fecha_disp,          0.27, '12sp', (0.75, 0.75, 0.8, 1)))
        row.add_widget(_lbl(f"$ {monto:.2f}",    0.24, '12sp', (0.4, 0.9, 0.5, 1), align='center'))
        row.add_widget(_lbl(desc,                0.33, '11sp', (0.65, 0.65, 0.7, 1)))
        btn_e = Button(text='✏', size_hint_x=0.08, font_size='13sp',
                       background_normal='', background_color=(0.15, 0.4, 0.2, 1))
        btn_x = Button(text='✗', size_hint_x=0.08, font_size='13sp',
                       background_normal='', background_color=(0.55, 0.15, 0.15, 1))
        btn_e.bind(on_release=lambda *_: self.editar_ofrenda(reg_id))
        btn_x.bind(on_release=lambda *_: self._borrar_ofrenda(reg_id))
        row.add_widget(btn_e)
        row.add_widget(btn_x)
        return row

    def editar_ofrenda(self, reg_id):
        r = self.ofrendas_model.get_one(reg_id)
        if not r:
            return
        self._ofrenda_editing_id = reg_id
        self.editing_ofrenda = True
        if 'fecha_ofrenda' in self.ids:
            self.ids.fecha_ofrenda.text  = _ts_display(r['fecha'])
            self.ids.monto_ofrenda.text  = str(r['monto'] or '')
            self.ids.desc_ofrenda.text   = str(r['descripcion'] or '')
        self.status_ofrenda = "Editando registro de ofrenda..."

    def guardar_ofrenda(self, fecha_txt, monto_txt, desc_txt):
        try:
            monto = float(monto_txt.strip())
            if monto <= 0:
                raise ValueError
        except ValueError:
            self.status_ofrenda = "Ingresa un monto valido (ej: 500)"
            return

        import time as _time
        iso = _parse_fecha(fecha_txt)
        try:
            ts = int(datetime.strptime(iso, '%Y-%m-%d').timestamp()) if iso else int(_time.time())
        except Exception:
            ts = int(_time.time())

        if self.editing_ofrenda and self._ofrenda_editing_id:
            ok = self.ofrendas_model.actualizar(
                self._ofrenda_editing_id,
                fecha=ts,
                monto=monto,
                descripcion=desc_txt.strip(),
            )
            self.status_ofrenda = "Ofrenda actualizada" if ok else "Error al actualizar"
        else:
            ok = self.ofrendas_model.insertar(id_usuario=1, monto=monto,
                                              descripcion=desc_txt.strip())
            self.status_ofrenda = f"Ofrenda guardada  ($ {monto:.2f})" if ok else "Error al guardar"

        if ok:
            self._reset_form_ofrenda()
            self._actualizar_filtros()
            self._cargar_ofrendas()

    def cancelar_edicion_ofrenda(self):
        self._reset_form_ofrenda()

    def _borrar_ofrenda(self, reg_id):
        self.ofrendas_model.borrar(reg_id)
        self._actualizar_filtros()
        self._cargar_ofrendas()

    def _reset_form_ofrenda(self):
        self._ofrenda_editing_id = None
        self.editing_ofrenda = False
        self.status_ofrenda  = ""
        if 'monto_ofrenda' not in self.ids:
            return
        self.ids.fecha_ofrenda.text  = datetime.now().strftime('%d/%m/%Y')
        self.ids.monto_ofrenda.text  = ''
        self.ids.desc_ofrenda.text   = ''


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _lbl(text, size_hint_x, font_size, color, align='left'):
    lbl = Label(
        text=str(text),
        size_hint_x=size_hint_x,
        font_size=font_size,
        color=color,
        halign=align,
        valign='middle',
        shorten=True,
        shorten_from='right',
    )
    lbl.bind(size=lambda inst, v: setattr(inst, 'text_size', (v[0], None)))
    return lbl


def _canvas_bg(widget, color):
    from kivy.graphics import Color, Rectangle
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda inst, v: setattr(rect, 'pos', v))
    widget.bind(size=lambda inst, v: setattr(rect, 'size', v))
