import os
import json
import zipfile
import shutil
import tempfile
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, ListProperty

from kivy.factory import Factory
from screens.basescreen import BaseScreen


# Tablas que se combinan en un merge (excluye datos estáticos/semilla)
_TABLAS_MERGE = [
    'oraciones', 'trabajos', 'propositos', 'pasos',
    'capitulos', 'ofrendas', 'estudio_versiculos',
]

FONTS_MAP = {
    'Roboto (predeterminado)':  '',
    'La Monarchie':             os.path.join('stdt', 'fonts', 'LaMonarchiedeSaintOmbre.ttf'),
    'Lacheyard Script':         os.path.join('stdt', 'fonts', 'LacheyardScript_PERSONAL_USE_ONLY.otf'),
}
TAMANOS_MAP = {
    'Pequeno  (12sp)': '12sp',
    'Normal   (14sp)': '14sp',
    'Grande   (16sp)': '16sp',
    'X-Grande (18sp)': '18sp',
}


class ConfigScreen(BaseScreen):

    user_nombre      = StringProperty('--')
    user_nivel       = StringProperty('Nivel 0')
    user_oraciones   = StringProperty('')
    status_backup    = StringProperty('')
    status_apariencia = StringProperty('')

    font_opciones    = ListProperty(list(FONTS_MAP.keys()))
    tamano_opciones  = ListProperty(list(TAMANOS_MAP.keys()))
    font_actual      = StringProperty('Roboto (predeterminado)')
    tamano_actual    = StringProperty('Normal   (14sp)')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zip_pendiente = None
        self._oraciones_model = App.get_running_app().getModel('OracionesModel')

    def on_enter(self, *args):
        self._cargar_usuario()
        self._cargar_apariencia()

    # ── Info de usuario ────────────────────────────────────────────

    def _cargar_usuario(self):
        usr = self.user.get_one(1) if self.user else None
        if not usr:
            return
        self.user_nombre = usr['username'] or '--'
        nivel = self.get_player_nivel() or 0
        self.user_nivel = f"Nivel  {nivel}"

        if self._oraciones_model:
            try:
                total = len(self._oraciones_model.obtener_todos() or [])
                self.user_oraciones = f"Oraciones registradas: {total}"
            except Exception:
                pass

    def ir_a_perfil(self):
        self.manager.current = 'player_data'

    # ── RolloBiblico ───────────────────────────────────────────────

    def abrir_rollo(self):
        contenido = App.get_running_app().get_promesa()
        if not contenido:
            return
        rollo = Factory.RolloBiblico()
        rollo.mostrar_pasaje(0, ContenidoTotal=contenido)

    # ── Exportar ───────────────────────────────────────────────────

    @mainthread
    def abrir_selector_exportar(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))

        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            except Exception:
                pass

        fc = FileChooserListView(
            path=self._carpeta_backup(),
            dirselect=True,
            filters=[],
        )
        content.add_widget(fc)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btn_c = Button(text='Cancelar', background_normal='',
                       background_color=(0.3, 0.3, 0.3, 1))
        btn_s = Button(text='Exportar aqui', background_normal='',
                       background_color=(0.18, 0.48, 0.28, 1), bold=True)
        btn_row.add_widget(btn_c)
        btn_row.add_widget(btn_s)
        content.add_widget(btn_row)

        self._popup = Popup(title='Elegir carpeta destino',
                            content=content, size_hint=(0.95, 0.9))
        btn_c.bind(on_release=self._popup.dismiss)
        btn_s.bind(on_release=lambda *_: self._confirmar_exportar(fc.path))
        self._popup.open()

    def _confirmar_exportar(self, carpeta):
        self._popup.dismiss()
        self.exportar(carpeta)

    def exportar(self, carpeta=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre    = f"ElLinaje_{timestamp}.zip"
        destino   = os.path.join(carpeta or self._carpeta_backup(), nombre)

        try:
            version = App.get_running_app().app_config.get('VERSION', [0, 3, 0])
            ver_str = '.'.join(str(v) for v in version)

            with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('version.txt', ver_str)
                for root, _dirs, files in os.walk('data'):
                    for f in files:
                        fp = os.path.join(root, f)
                        zf.write(fp, arcname=fp)

            self.status_backup = f"Guardado: {nombre}\nEn: {self._carpeta_backup()}"
        except Exception as e:
            self.status_backup = f"Error al exportar: {e}"
            Logger.error(f"[Config] export: {e}")

    def _carpeta_backup(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                return primary_external_storage_path()
            except Exception:
                pass
        return os.path.expanduser("~")

    # ── Importar ───────────────────────────────────────────────────

    @mainthread
    def abrir_selector_importar(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))

        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE,
                                     Permission.WRITE_EXTERNAL_STORAGE])
            except Exception:
                pass

        fc = FileChooserListView(
            path=self._carpeta_backup(),
            filters=['*.zip'],
        )
        content.add_widget(fc)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btn_c = Button(text='Cancelar', background_normal='',
                       background_color=(0.3, 0.3, 0.3, 1))
        btn_s = Button(text='Seleccionar', background_normal='',
                       background_color=(0.18, 0.45, 0.78, 1), bold=True)
        btn_row.add_widget(btn_c)
        btn_row.add_widget(btn_s)
        content.add_widget(btn_row)

        self._popup = Popup(title='Seleccionar backup (.zip)',
                            content=content, size_hint=(0.95, 0.9))
        btn_c.bind(on_release=self._popup.dismiss)
        btn_s.bind(on_release=lambda *_: self._verificar_zip(fc.selection))
        self._popup.open()

    def _verificar_zip(self, selection):
        if not selection:
            self.status_backup = 'Selecciona un archivo .zip primero'
            return
        zip_path = selection[0]
        if not os.path.exists(zip_path):
            self.status_backup = 'Archivo no encontrado'
            return

        self._popup.dismiss()

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                nombres = zf.namelist()
                if not any('ElLinaje.db' in n for n in nombres):
                    self.status_backup = 'ZIP invalido: no contiene ElLinaje.db'
                    return
                # Version check
                ver_msg = ''
                if 'version.txt' in nombres:
                    ver_imp = zf.read('version.txt').decode().strip()
                    ver_act = '.'.join(str(v) for v in
                                      App.get_running_app().app_config.get('VERSION', [0, 3, 0]))
                    if ver_imp != ver_act:
                        ver_msg = f"Backup v{ver_imp}  /  App v{ver_act}\n"
        except Exception as e:
            self.status_backup = f'Error leyendo zip: {e}'
            return

        self._zip_pendiente = zip_path
        self._modal_confirmacion(ver_msg)

    @mainthread
    def _modal_confirmacion(self, ver_msg=''):
        content = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))

        content.add_widget(Label(
            text=f"{ver_msg}Elige como importar los datos:",
            font_size='13sp', color=(0.88, 0.88, 0.92, 1),
            size_hint_y=None, height=dp(52), halign='center',
        ))

        btn_comb = Button(
            text="Combinar\n(agrega registros nuevos, mantiene los actuales)",
            background_normal='', background_color=(0.18, 0.45, 0.28, 1),
            font_size='12sp', halign='center',
        )
        btn_remp = Button(
            text="Reemplazar\n(hace backup y reemplaza todo — requiere reinicio)",
            background_normal='', background_color=(0.55, 0.22, 0.12, 1),
            font_size='12sp', halign='center',
        )
        btn_cancel = Button(
            text='Cancelar', background_normal='',
            background_color=(0.25, 0.25, 0.25, 1),
            size_hint_y=None, height=dp(42),
        )

        content.add_widget(btn_comb)
        content.add_widget(btn_remp)
        content.add_widget(btn_cancel)

        self._popup2 = Popup(title='Importar backup',
                             content=content, size_hint=(0.9, 0.58))
        btn_comb.bind(on_release=lambda *_: self._importar_combinar())
        btn_remp.bind(on_release=lambda *_: self._importar_reemplazar())
        btn_cancel.bind(on_release=self._popup2.dismiss)
        self._popup2.open()

    def _importar_combinar(self):
        self._popup2.dismiss()
        zip_path = self._zip_pendiente
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(tmpdir)

                imported_db = self._buscar_db_en_tmpdir(tmpdir)
                if not imported_db:
                    self.status_backup = 'No se encontro ElLinaje.db en el backup'
                    return

                resultados = self._merge_databases(imported_db)

                # Copiar archivos nuevos de todos los subdirectorios (img, snd, etc.)
                src_data_dir = os.path.join(tmpdir, 'data')
                if os.path.exists(src_data_dir):
                    for subdir in os.listdir(src_data_dir):
                        src_sub = os.path.join(src_data_dir, subdir)
                        if not os.path.isdir(src_sub):
                            continue
                        dst_sub = os.path.join('data', subdir)
                        os.makedirs(dst_sub, exist_ok=True)
                        for f in os.listdir(src_sub):
                            src_f = os.path.join(src_sub, f)
                            dst_f = os.path.join(dst_sub, f)
                            if os.path.isfile(src_f) and not os.path.exists(dst_f):
                                shutil.copy2(src_f, dst_f)

            total = sum(v for v in resultados.values() if isinstance(v, int))
            self.status_backup = f"Combinado: {total} registros nuevos importados"
        except Exception as e:
            self.status_backup = f"Error combinando: {e}"
            Logger.error(f"[Config] merge: {e}")

    def _copiar_dir(self, src, dst):
        """Copia recursiva sin copiar metadatos (compatible con SELinux en Android)."""
        os.makedirs(dst, exist_ok=True)
        for entry in os.scandir(src):
            s = entry.path
            d = os.path.join(dst, entry.name)
            if entry.is_dir(follow_symlinks=False):
                self._copiar_dir(s, d)
            elif entry.is_file(follow_symlinks=False):
                shutil.copyfile(s, d)

    def _importar_reemplazar(self):
        self._popup2.dismiss()
        zip_path = self._zip_pendiente
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak_dir   = f"data_bak_{timestamp}"
            if os.path.exists('data'):
                self._copiar_dir('data', bak_dir)

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(tmpdir)

                src_data = os.path.join(tmpdir, 'data')
                if os.path.exists(src_data):
                    if os.path.exists('data'):
                        shutil.rmtree('data')
                    self._copiar_dir(src_data, 'data')
                    self.status_backup = (f"Reemplazado correctamente.\n"
                                          f"Backup anterior: {bak_dir}\n"
                                          f"Reinicia la aplicacion para ver los cambios.")
                else:
                    self.status_backup = 'No se encontro carpeta data/ en el backup'
        except Exception as e:
            self.status_backup = f"Error reemplazando: {e}"
            Logger.error(f"[Config] replace: {e}")

    def _buscar_db_en_tmpdir(self, tmpdir):
        opciones = [
            os.path.join(tmpdir, 'data', 'ElLinaje.db'),
            os.path.join(tmpdir, 'ElLinaje.db'),
        ]
        for p in opciones:
            if os.path.exists(p):
                return p
        return None

    def _merge_databases(self, src_path):
        conn_src = sqlite3.connect(src_path)
        conn_src.row_factory = sqlite3.Row
        conn_dst = sqlite3.connect('data/ElLinaje.db')
        resultados = {}

        for tabla in _TABLAS_MERGE:
            try:
                rows = conn_src.execute(f"SELECT * FROM {tabla}").fetchall()
                if not rows:
                    resultados[tabla] = 0
                    continue
                cols   = list(rows[0].keys())
                ph     = ','.join(['?'] * len(cols))
                colstr = ','.join(cols)
                count  = 0
                for row in rows:
                    try:
                        conn_dst.execute(
                            f"INSERT OR IGNORE INTO {tabla} ({colstr}) VALUES ({ph})",
                            tuple(row)
                        )
                        count += 1
                    except Exception:
                        pass
                conn_dst.commit()
                resultados[tabla] = count
            except Exception as e:
                resultados[tabla] = 0
                Logger.warning(f"[Config] merge {tabla}: {e}")

        conn_src.close()
        conn_dst.close()
        return resultados

    # ── Apariencia ─────────────────────────────────────────────────

    def _cargar_apariencia(self):
        cfg = App.get_running_app().app_config
        font_path = cfg.get('FONT_NAME', '')
        font_size = cfg.get('FONT_SIZE', '14sp')

        for nombre, path in FONTS_MAP.items():
            if path == font_path:
                self.font_actual = nombre
                break

        for nombre, size in TAMANOS_MAP.items():
            if size == font_size:
                self.tamano_actual = nombre
                break

    def aplicar_apariencia(self):
        font_path = FONTS_MAP.get(self.font_actual, '')
        font_size = TAMANOS_MAP.get(self.tamano_actual, '14sp')

        cfg = App.get_running_app().app_config
        cfg['FONT_NAME'] = font_path
        cfg['FONT_SIZE'] = font_size

        # Persistir
        config_path = cfg.get('CONFIG_PATH', os.path.join('data', 'config.json'))
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({'FONT_NAME': font_path, 'FONT_SIZE': font_size}, f)
            self.status_apariencia = 'Guardado. Se aplica al reiniciar.'
        except Exception as e:
            self.status_apariencia = f'Error guardando: {e}'
