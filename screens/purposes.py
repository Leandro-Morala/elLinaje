from datetime import datetime
from kivy.app import App
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout as KBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from screens.basescreen import BaseScreen
from screens.work import FechaPicker, _lbl, _canvas_bg, _parse_fecha, _fecha_display


# ──────────────────────────────────────────────────────────────────
# Modal: Nueva / Editar Meta
# ──────────────────────────────────────────────────────────────────

class NuevaMetaModal(ModalView):
    def __init__(self, callback, meta=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint    = (0.92, None)
        self.height       = dp(310)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.75)
        self._callback = callback

        caja = KBox(orientation='vertical', padding=dp(14), spacing=dp(10))
        _canvas_bg(caja, (0.08, 0.08, 0.18, 1))
        self.add_widget(caja)

        caja.add_widget(Label(
            text="Editar Meta" if meta else "Nueva Meta",
            font_size='16sp', bold=True,
            color=(0.95, 0.78, 0.1, 1),
            size_hint_y=None, height=dp(28),
        ))

        ti_kw = dict(
            multiline=False, size_hint_y=None, height=dp(42),
            background_color=(0.1, 0.1, 0.22, 1),
            foreground_color=(0.95, 0.95, 0.88, 1),
            hint_text_color=(0.35, 0.35, 0.5, 1),
            cursor_color=(0.95, 0.78, 0.1, 1),
            font_size='13sp', padding=(dp(8), dp(10)),
        )
        self.ti_objetivo = TextInput(hint_text="Objetivo (título de la meta)", **ti_kw)
        self.ti_alcanzar = TextInput(hint_text="¿Qué quiero alcanzar?", **ti_kw)

        fecha_row = KBox(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.ti_fecha = TextInput(hint_text="Fecha límite (dd/mm/aaaa)",
                                  size_hint_x=0.78, **ti_kw)
        btn_cal = Button(text="📅", size_hint_x=0.22, font_size='16sp',
                         background_normal='', background_color=(0.18, 0.18, 0.38, 1))
        btn_cal.bind(on_release=lambda *_: FechaPicker(
            callback=lambda iso: setattr(self.ti_fecha, 'text', _fecha_display(iso))
        ).open())
        fecha_row.add_widget(self.ti_fecha)
        fecha_row.add_widget(btn_cal)

        if meta:
            self.ti_objetivo.text = meta['proposito'] or ''
            self.ti_alcanzar.text = meta['objetivo'] or ''
            iso = meta['fecha_objetivo'] or ''
            self.ti_fecha.text = _fecha_display(iso) if iso else ''

        caja.add_widget(self.ti_objetivo)
        caja.add_widget(self.ti_alcanzar)
        caja.add_widget(fecha_row)

        self.lbl_err = Label(text='', font_size='12sp', color=(1, 0.4, 0.4, 1),
                             size_hint_y=None, height=0)
        caja.add_widget(self.lbl_err)

        btns = KBox(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_ok = Button(text="Guardar" if meta else "Crear Meta",
                        background_normal='', background_color=(0.18, 0.45, 0.78, 1),
                        font_size='14sp', bold=True)
        btn_cancel = Button(text="Cancelar", background_normal='',
                            background_color=(0.3, 0.3, 0.3, 0.8), font_size='13sp')
        btn_ok.bind(on_release=self._confirmar)
        btn_cancel.bind(on_release=lambda *_: self.dismiss())
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        caja.add_widget(btns)

    def _confirmar(self, *_):
        objetivo = self.ti_objetivo.text.strip()
        if not objetivo:
            self.lbl_err.text = "El objetivo no puede estar vacío"
            self.lbl_err.height = dp(18)
            return
        iso = _parse_fecha(self.ti_fecha.text) or ''
        self._callback(objetivo, self.ti_alcanzar.text.strip(), iso)
        self.dismiss()


# ──────────────────────────────────────────────────────────────────
# Modal: Agregar / Editar Progreso
# ──────────────────────────────────────────────────────────────────

class NuevoProgresoModal(ModalView):
    def __init__(self, id_proposito, callback, progreso=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint    = (0.92, None)
        self.height       = dp(310)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.75)
        self._callback = callback

        caja = KBox(orientation='vertical', padding=dp(14), spacing=dp(10))
        _canvas_bg(caja, (0.07, 0.12, 0.1, 1))
        self.add_widget(caja)

        caja.add_widget(Label(
            text="Editar Progreso" if progreso else "Registrar Progreso",
            font_size='16sp', bold=True,
            color=(0.4, 0.9, 0.55, 1),
            size_hint_y=None, height=dp(28),
        ))

        ti_kw = dict(
            multiline=False, size_hint_y=None, height=dp(42),
            background_color=(0.1, 0.1, 0.22, 1),
            foreground_color=(0.95, 0.95, 0.88, 1),
            hint_text_color=(0.35, 0.35, 0.5, 1),
            cursor_color=(0.4, 0.9, 0.55, 1),
            font_size='13sp', padding=(dp(8), dp(10)),
        )
        fecha_row = KBox(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.ti_fecha = TextInput(hint_text="Fecha (dd/mm/aaaa)",
                                  size_hint_x=0.78, **ti_kw)
        self.ti_fecha.text = datetime.now().strftime('%d/%m/%Y')
        btn_cal = Button(text="📅", size_hint_x=0.22, font_size='16sp',
                         background_normal='', background_color=(0.1, 0.28, 0.18, 1))
        btn_cal.bind(on_release=lambda *_: FechaPicker(
            callback=lambda iso: setattr(self.ti_fecha, 'text', _fecha_display(iso))
        ).open())
        fecha_row.add_widget(self.ti_fecha)
        fecha_row.add_widget(btn_cal)

        self.ti_logro = TextInput(hint_text="Logro alcanzado", **ti_kw)
        self.ti_dios  = TextInput(hint_text="Doy gracias a Dios por...", **ti_kw)

        if progreso:
            self.ti_fecha.text = _fecha_display(progreso['fecha_creacion'] or '')
            self.ti_logro.text = progreso['paso'] or ''
            self.ti_dios.text  = progreso['observaciones'] or ''

        caja.add_widget(fecha_row)
        caja.add_widget(self.ti_logro)
        caja.add_widget(self.ti_dios)

        self.lbl_err = Label(text='', font_size='12sp', color=(1, 0.4, 0.4, 1),
                             size_hint_y=None, height=0)
        caja.add_widget(self.lbl_err)

        btns = KBox(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_ok = Button(text="Guardar", background_normal='',
                        background_color=(0.15, 0.48, 0.28, 1),
                        font_size='14sp', bold=True)
        btn_cancel = Button(text="Cancelar", background_normal='',
                            background_color=(0.3, 0.3, 0.3, 0.8), font_size='13sp')
        btn_ok.bind(on_release=self._confirmar)
        btn_cancel.bind(on_release=lambda *_: self.dismiss())
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        caja.add_widget(btns)

    def _confirmar(self, *_):
        logro = self.ti_logro.text.strip()
        if not logro:
            self.lbl_err.text = "El logro no puede estar vacío"
            self.lbl_err.height = dp(18)
            return
        iso = _parse_fecha(self.ti_fecha.text) or datetime.now().strftime('%Y-%m-%d')
        self._callback(logro, self.ti_dios.text.strip(), iso)
        self.dismiss()


# ──────────────────────────────────────────────────────────────────
# Pantalla principal
# ──────────────────────────────────────────────────────────────────

class PurposesScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proposito_model = App.get_running_app().getModel('PropositoModel')
        self.pasos_model     = App.get_running_app().getModel('PasosModel')

    def on_enter(self, *args):
        self._cargar_metas()

    # ── Construcción de la lista ────────────────────────────────

    def _cargar_metas(self):
        if 'metas_list' not in self.ids:
            return
        container = self.ids.metas_list
        container.clear_widgets()

        metas = self.proposito_model.get_by_usuario(1) or []
        if not metas:
            container.add_widget(Label(
                text="Sin metas. Presiona '+ Nueva Meta'.",
                font_size='14sp', color=(0.5, 0.5, 0.62, 1),
                size_hint_y=None, height=dp(60),
                halign='center', text_size=(None, None),
            ))
            return

        for meta in metas:
            container.add_widget(self._bloque_meta(meta))

    def _bloque_meta(self, meta):
        """Tarjeta completa: cabecera + pasos inline + barra de acciones."""
        completado = bool(meta['completado'])
        pasos = self.pasos_model.get_by_proposito(meta['id']) or []

        # ── Contenedor principal de la tarjeta
        bloque = KBox(
            orientation='vertical',
            size_hint_y=None,
            spacing=0,
        )
        bloque.bind(minimum_height=bloque.setter('height'))

        # ── Cabecera ────────────────────────────────────────────
        header = KBox(size_hint_y=None, height=dp(54),
                      padding=(dp(10), dp(6)), spacing=dp(6))
        hbg = (0.1, 0.18, 0.12, 1) if completado else (0.1, 0.12, 0.25, 1)
        _canvas_bg(header, hbg)
        # Línea inferior del header
        with header.canvas.after:
            Color(*(0.55, 0.88, 0.55, 0.5) if completado else (0.95, 0.78, 0.1, 0.4))
            self._header_line = Line(
                points=[header.x, header.y, header.x + header.width, header.y],
                width=1.2)
        header.bind(pos=lambda i, v: self._update_line(i),
                    size=lambda i, v: self._update_line(i))

        info_col = KBox(orientation='vertical', size_hint_x=0.72)
        badge = "  (OK) Completada" if completado else ""
        color_tit = (0.58, 0.92, 0.62, 1) if completado else (0.95, 0.95, 0.88, 1)
        info_col.add_widget(_lbl(f"{meta['proposito']}{badge}", 1, '14sp', color_tit))
        sub = []
        if meta['objetivo']:
            sub.append(meta['objetivo'])
        if meta['fecha_objetivo']:
            sub.append(f"límite {_fecha_display(meta['fecha_objetivo'])}")
        if sub:
            info_col.add_widget(_lbl("  -  ".join(sub), 1, '11sp', (0.6, 0.6, 0.72, 1)))
        header.add_widget(info_col)

        # Botones cabecera: editar y borrar
        btn_edit = Button(text='E', size_hint=(None, None),
                          size=(dp(34), dp(34)),
                          background_normal='',
                          background_color=(0.18, 0.35, 0.65, 1), font_size='14sp')
        btn_edit.bind(on_release=lambda *_: self._editar_meta(meta))
        btn_del = Button(text='X', size_hint=(None, None),
                         size=(dp(34), dp(34)),
                         background_normal='',
                         background_color=(0.5, 0.15, 0.15, 1), font_size='14sp')
        btn_del.bind(on_release=lambda *_: self._borrar_meta(meta['id']))
        header.add_widget(btn_edit)
        header.add_widget(btn_del)
        bloque.add_widget(header)

        # ── Pasos inline ────────────────────────────────────────
        if pasos:
            for paso in pasos:
                bloque.add_widget(self._fila_paso(paso, meta['id']))
        else:
            vacio = KBox(size_hint_y=None, height=dp(30),
                         padding=(dp(14), dp(4)))
            _canvas_bg(vacio, (0.08, 0.09, 0.16, 1))
            vacio.add_widget(_lbl("Sin progresos registrados aún...", 1,
                                  '12sp', (0.4, 0.4, 0.55, 1)))
            bloque.add_widget(vacio)

        # ── Barra de acciones ───────────────────────────────────
        footer = KBox(size_hint_y=None, height=dp(38),
                      padding=(dp(6), dp(4)), spacing=dp(6))
        _canvas_bg(footer, (0.07, 0.08, 0.14, 1))

        btn_prog = Button(text="+ Progreso",
                          background_normal='',
                          background_color=(0.15, 0.42, 0.25, 1),
                          font_size='12sp', bold=True)
        btn_prog.bind(on_release=lambda *_: self._agregar_progreso(meta['id']))

        lbl_n = Label(
            text=f"{len(pasos)} paso{'s' if len(pasos) != 1 else ''}",
            font_size='11sp', color=(0.5, 0.5, 0.65, 1),
            size_hint_x=0.3,
        )

        btn_comp = Button(
            text="Reabrir" if completado else "(OK) Meta cumplida",
            background_normal='',
            background_color=(0.28, 0.45, 0.28, 1) if completado else (0.22, 0.48, 0.22, 1),
            font_size='11sp',
        )
        btn_comp.bind(on_release=lambda *_: self._toggle_completada(meta['id'], completado))

        footer.add_widget(btn_prog)
        footer.add_widget(lbl_n)
        footer.add_widget(btn_comp)
        bloque.add_widget(footer)

        # Separador entre tarjetas
        sep = KBox(size_hint_y=None, height=dp(8))
        bloque.add_widget(sep)

        return bloque

    def _fila_paso(self, paso, meta_id):
        """Fila de un paso dentro de la tarjeta de la meta."""
        logro = paso['paso'] or ''
        dios  = paso['observaciones'] or ''
        fecha = _fecha_display(paso['fecha_creacion'] or '')

        tiene_dios = bool(dios)
        alto = dp(54) if tiene_dios else dp(36)

        fila = KBox(size_hint_y=None, height=alto,
                    padding=(dp(14), dp(4)), spacing=dp(6))
        _canvas_bg(fila, (0.09, 0.1, 0.18, 1))

        # Línea izquierda decorativa (acento verde)
        with fila.canvas.before:
            Color(0.3, 0.75, 0.45, 0.8)
            rect_acc = Rectangle(pos=(fila.x, fila.y), size=(dp(3), alto))
        fila.bind(pos=lambda i, v: setattr(rect_acc, 'pos', (v[0], v[1])))
        fila.bind(size=lambda i, v: setattr(rect_acc, 'size', (dp(3), v[1])))

        contenido = KBox(orientation='vertical', size_hint_x=0.65,
                         padding=(dp(4), 0))
        contenido.add_widget(
            _lbl(f"{fecha}  —  {logro}", 1, '12sp', (0.88, 0.88, 0.92, 1))
        )
        if tiene_dios:
            contenido.add_widget(
                _lbl(f"*  {dios}", 1, '11sp', (0.45, 0.82, 0.55, 1))
            )
        fila.add_widget(contenido)

        btn_e = Button(text='E', size_hint_x=0.17, font_size='12sp',
                       background_normal='',
                       background_color=(0.18, 0.35, 0.65, 0.9))
        btn_e.bind(on_release=lambda *_: self._editar_paso(paso))
        btn_x = Button(text='X', size_hint_x=0.17, font_size='12sp',
                       background_normal='',
                       background_color=(0.45, 0.12, 0.12, 0.8))
        btn_x.bind(on_release=lambda *_: self._borrar_paso(paso['id']))
        fila.add_widget(btn_e)
        fila.add_widget(btn_x)
        return fila

    @staticmethod
    def _update_line(header):
        """Actualiza la línea decorativa inferior del header."""
        for instr in header.canvas.after.children:
            if isinstance(instr, Line):
                instr.points = [
                    header.x, header.y,
                    header.x + header.width, header.y
                ]

    # ── Acciones ────────────────────────────────────────────────

    def nueva_meta(self):
        def _guardar(objetivo, alcanzar, fecha_iso):
            self.proposito_model.insertar(
                proposito=objetivo,
                objetivo=alcanzar,
                fecha_objetivo=fecha_iso,
            )
            self._cargar_metas()
        NuevaMetaModal(callback=_guardar).open()

    def _editar_meta(self, meta):
        def _guardar(objetivo, alcanzar, fecha_iso):
            self.proposito_model.actualizar(
                meta['id'],
                proposito=objetivo,
                objetivo=alcanzar,
                fecha_objetivo=fecha_iso,
            )
            self._cargar_metas()
        NuevaMetaModal(callback=_guardar, meta=meta).open()

    def _agregar_progreso(self, meta_id):
        def _guardar(logro, dios_ayudo, fecha_iso):
            self.pasos_model.insertar_progreso(
                id_proposito=meta_id,
                logro=logro,
                dios_ayudo=dios_ayudo,
                fecha=fecha_iso,
            )
            self._cargar_metas()
        NuevoProgresoModal(id_proposito=meta_id, callback=_guardar).open()

    def _editar_paso(self, paso):
        def _guardar(logro, dios_ayudo, fecha_iso):
            self.pasos_model.actualizar(
                paso['id'],
                paso=logro,
                observaciones=dios_ayudo,
                fecha_creacion=fecha_iso,
            )
            self._cargar_metas()
        NuevoProgresoModal(id_proposito=paso['id_proposito'],
                           callback=_guardar, progreso=paso).open()

    def _toggle_completada(self, meta_id, actualmente_completado):
        nuevo = 0 if actualmente_completado else 1
        self.proposito_model.marcar_completada(meta_id, nuevo)
        self._cargar_metas()

    def _borrar_paso(self, paso_id):
        self.pasos_model.borrar(paso_id)
        self._cargar_metas()

    def _borrar_meta(self, meta_id):
        for p in (self.pasos_model.get_by_proposito(meta_id) or []):
            self.pasos_model.borrar(p['id'])
        self.proposito_model.borrar(meta_id)
        self._cargar_metas()
