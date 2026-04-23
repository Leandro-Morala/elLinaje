from db.base import db
from kivy.logger import Logger
import time
import calendar
from datetime import datetime


class CapitulosModel(db):
    """Versiculos biblicos memorizados por el usuario."""

    def table_name(self):
        return 'capitulos'

    def table_list_columns(self):
        return [
            ('id',               0,  'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('id_usuario',       1,  'INTEGER NOT NULL'),
            ('book_id',          0,  'INTEGER NOT NULL'),
            ('book_name',        '', 'TEXT NOT NULL'),
            ('capitulo',         0,  'INTEGER NOT NULL'),
            ('versiculo',        0,  'INTEGER NOT NULL'),
            ('texto',            '', 'TEXT NOT NULL'),
            ('fecha_creacion',   0,  'INTEGER DEFAULT 0'),   # unix timestamp de creacion
            ('fecha_renovacion', 0,  'INTEGER DEFAULT 0'),   # unix timestamp de ultima renovacion (score)
            ('veces_acertado',   0,  'INTEGER DEFAULT 0'),
            ('veces_fallado',    0,  'INTEGER DEFAULT 0'),
            ('nivel_refuerzo',   0,  'INTEGER DEFAULT 0'),
        ]

    def insertar(self, id_usuario, book_id, book_name, capitulo, versiculo, texto):
        ahora = int(time.time())
        return self.__insertar__(
            id_usuario=id_usuario,
            book_id=book_id,
            book_name=book_name,
            capitulo=capitulo,
            versiculo=versiculo,
            texto=texto,
            fecha_creacion=ahora,
            fecha_renovacion=ahora,   # empieza con vida completa
        )

    def get_by_usuario(self, id_usuario):
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_usuario = ? ORDER BY book_id, capitulo, versiculo;")
        cursor = self.__run_executa_sql__(query, (id_usuario,), 'SELECT')
        if cursor:
            return cursor.fetchall()
        return []

    def get_existing(self, id_usuario, book_id, capitulo, versiculo):
        """Devuelve el registro si existe, None si no."""
        query = (f"SELECT * FROM {self.table_name()} "
                 f"WHERE id_usuario = ? AND book_id = ? AND capitulo = ? AND versiculo = ? LIMIT 1;")
        cursor = self.__run_executa_sql__(query, (id_usuario, book_id, capitulo, versiculo), 'SELECT')
        if cursor:
            return cursor.fetchone()
        return None

    def existe(self, id_usuario, book_id, capitulo, versiculo):
        return self.get_existing(id_usuario, book_id, capitulo, versiculo) is not None

    # ------------------------------------------------------------------
    # Sistema de vida util (calculado en tiempo real)
    # ------------------------------------------------------------------

    def calcular_vida_dias(self, total_versiculos):
        """1 dia por versiculo, minimo 7, maximo 365."""
        return min(365, max(7, total_versiculos))

    def _fecha_a_timestamp(self, fecha):
        """Convierte fecha_creacion (int unix o string SQLite UTC) a unix timestamp."""
        if isinstance(fecha, (int, float)) and fecha > 1_000_000_000:
            return int(fecha)
        try:
            dt = datetime.strptime(str(fecha), '%Y-%m-%d %H:%M:%S')
            return calendar.timegm(dt.timetuple())
        except Exception:
            Logger.warning(f"[Capitulos] No se pudo parsear fecha: {fecha!r}")
            return int(time.time())

    def _get_referencia_ts(self, registro):
        """
        Devuelve el timestamp de referencia para calcular dias vividos.
        Prioriza fecha_renovacion si es valida (> 0 y en el pasado).
        Caso contrario usa fecha_creacion.
        """
        ahora = int(time.time())
        try:
            fr = registro['fecha_renovacion']
        except (KeyError, IndexError):
            fr = 0
        if fr and 0 < fr <= ahora:
            return fr
        return self._fecha_a_timestamp(registro['fecha_creacion'])

    def calcular_expirados(self, id_usuario):
        """
        Calcula en tiempo real cuales versiculos expiraron.
        vida_dias se basa en el total ACTUAL antes de borrar nada.
        """
        registros = self.get_by_usuario(id_usuario)
        total = len(registros) if registros else 0
        if total == 0:
            return []
        vida_seg = self.calcular_vida_dias(total) * 86400
        ahora = int(time.time())
        return [r for r in registros
                if (ahora - self._get_referencia_ts(r)) > vida_seg]

    def procesar_envejecimiento(self, id_usuario):
        """Elimina versiculos expirados y devuelve la cantidad."""
        expirados = self.calcular_expirados(id_usuario)
        for r in expirados:
            self.borrar(r['id'])
        if expirados:
            Logger.info(f"[Capitulos] {len(expirados)} versiculos expirados eliminados")
        return len(expirados)

    # ------------------------------------------------------------------
    # Renovacion de vida segun score del desafio
    # ------------------------------------------------------------------

    def renovar_verso(self, reg_id, score, vida_dias):
        """
        Actualiza fecha_renovacion segun el score obtenido:
          score >= 0.7  → renovacion completa (100% de vida)
          score == 0.4  → penalizacion 25% (queda 75% de vida restante)
          score == 0.0  → penalizacion 50%, minimo siempre 1 dia
        """
        ahora = int(time.time())
        vida_seg = vida_dias * 86400

        if score >= 0.7:
            nueva_renovacion = ahora
        else:
            registro = self.get_one(reg_id)
            if not registro:
                return
            ts_ref = self._get_referencia_ts(registro)
            dias_restantes = (vida_seg - (ahora - ts_ref)) / 86400

            if score >= 0.4:
                nuevos_dias = dias_restantes * 0.75
            else:  # score == 0.0
                nuevos_dias = max(1.0, dias_restantes * 0.5)

            # fecha_renovacion = ahora - (tiempo que "ya vivio" el verso en el nuevo calculo)
            nueva_renovacion = ahora - int((vida_dias - nuevos_dias) * 86400)

        self.actualizar(reg_id, fecha_renovacion=nueva_renovacion)
        Logger.info(f"[Capitulos] verso {reg_id} renovado, score={score}, "
                    f"nueva_renovacion={nueva_renovacion}")

    # ------------------------------------------------------------------
    # Estadisticas del juego
    # ------------------------------------------------------------------

    def actualizar_estadisticas(self, reg_id, acertado=True):
        registro = self.get_one(reg_id)
        if not registro:
            return False
        try:
            if acertado:
                return self.actualizar(reg_id,
                    veces_acertado=registro['veces_acertado'] + 1,
                    nivel_refuerzo=min(5, registro['nivel_refuerzo'] + 1),
                )
            else:
                return self.actualizar(reg_id,
                    veces_fallado=registro['veces_fallado'] + 1,
                    nivel_refuerzo=max(0, registro['nivel_refuerzo'] - 1),
                )
        except Exception as e:
            Logger.error(f"[CapitulosModel] actualizar_estadisticas: {e}")
            return False
