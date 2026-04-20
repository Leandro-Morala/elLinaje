from db.base import db
import os
import re
from kivy.logger import Logger
import unicodedata

'''
CREATE TABLE book (
	id INTEGER NOT NULL, 
	book_reference_id INTEGER, 
	testament_reference_id INTEGER, 
	name VARCHAR(50), 
	PRIMARY KEY (id)
)
'''

class bookModel(db):
    
    def table_name(self):
        return 'book'
    def table_list_columns(self):
        return[
        ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),
        ('book_reference_id',0,'INTEGER'),
        ('testament_reference_id',0,'INTEGER'),
        ('name','','VARCHAR(50)')
        ]
    def insertar(self, book_reference_id,testament_reference_id,name ):
        return self.__insertar__(book_reference_id=book_reference_id,testament_reference_id=testament_reference_id,name=name )

    def get_all_names(self):
        '''
            devolver el nombre libros, book_id 
        '''
        sqll="SELECT name, book_reference_id , testament_reference_id FROM book ORDER BY book_reference_id ASC "; 
        cursor = self.__run_executa_sql__(sqll,'' ,'SELECT')
        todos = cursor.fetchall()
        return todos

    def _un_libro_(self,idLibro):
        '''
            devolver datos del libro
        '''
        table_name=self.table_name()
        query= f"SELECT id, book_reference_id, testament_reference_id, name from {table_name} WHERE id = ? LIMIT 1  ;"
        cursor = self.__run_executa_sql__(query,(idLibro,),'SELECT') 
        return cursor.fetchall()
        

'''
CREATE TABLE metadata (
	"key" VARCHAR(255) NOT NULL, 
	value VARCHAR(255), 
	PRIMARY KEY ("key")
)
'''

class metadataModel(db):
    
    def table_name(self):
        return 'metadata'
    def table_list_columns(self):
        return[
            ('key','','VARCHAR(255) NOT NULL PRIMARY KEY'),
            ('value','','VARCHAR(255)')
            ]
    def insertar(self, key,value):
        return self.__insertar__(key=key,value=value)


'''
CREATE TABLE verse (
	id INTEGER NOT NULL, 
	book_id INTEGER, 
	chapter INTEGER, 
	verse INTEGER, 
	text TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(book_id) REFERENCES book (id)
)
'''

class verseModel(db):
    
    def table_name(self):
        return 'verse'

    def table_list_columns(self):
        return[
            ('id',0,'INTEGER NOT NULL PRIMARY KEY'),
            ('book_id',0,'INTEGER NOT NULL REFERENCES book(id)'),
            ('chapter',0,'INTEGER'),
            ('verse',0,'INTEGER'),
            ('text','','TEXT')
            ]

    def insertar(self,book_id,chapter,verse, text):
        # no se adminte modificacion de la tabla
        return None
        #return self.__insertar__(book_id=book_id,chapter=chapter,verse=verse, text=text)

    
    # devolver un unico versiculo de un libro
    def versiculo(self,idLibro,capitulo,versiculo):
        '''
            devuelve un unico versiculo de un libro identificado por ide de libro, capitulo, versiculo
            se suguiere buscar primero el libro, obtener su idBook. para mejorar el resultado
            no se adminte busqueda por rango.
        '''
        return self._un_versiculo_(idLibro,capitulo,versiculo)
            
    def _un_versiculo_(self,idLibro,chapter,verse):
        '''
            obtener un versiculo biblico con el 
                nombre del libro, id_registro, idBook, capitulo, versiculo, texto
            a partir del identificador del id_libro, capitulo y versiculo. ( no se contempla la database )
        '''
        table_name=self.table_name()
        query = f"SELECT b.name,v.id, v.book_id,v.chapter,v.verse,v.text FROM {table_name} v INNER JOIN book b ON b.id = v.book_id WHERE v.book_id = ?  AND v.chapter = ? AND  v.verse = ? LIMIT 1 ;"
        cursor = self.__run_executa_sql__(query,(idLibro,chapter,verse),'SELECT') 
        return cursor.fetchone()
    

    def contar(self,idLibro):
        '''
            total de capitulos de un libro en la base de datos
        '''
        table_name=self.table_name()
        query = f"SELECT count(DISTINCT(chapter))  FROM  {table_name} WHERE book_id = ? ;"
        cursor = self.__run_executa_sql__(query,(idLibro,),'SELECT')
        respuesta = cursor.fetchone()
        if not respuesta:
            Logger.error(f"[VERSICULOS] error al intentar contar capitulos de tabla libro {idLibro}")
            return 0
        else:
            return int(respuesta[0])
    
    def countVersiculo(self,idLibro,Capitulo):
        '''
            total de versiculos de un capitulo en un libro en la base de datos
        '''
        table_name=self.table_name()
        query = f"SELECT count(id) FROM  {table_name} WHERE book_id = ? AND chapter = ?;"
        cursor = self.__run_executa_sql__(query,(idLibro,Capitulo),'SELECT')
        respuesta = cursor.fetchone()
        if not respuesta:
            Logger.error(f"[VERSICULOS] error al intentar contar versiculos de tabla libro {idLibro}, {Capitulo}")
            return 0
        else:
            return int(respuesta[0])
            
class Reg:
    # (None, 29431, 50, 3, 9, 'y por ser hallado en él, no teniendo mi justicia, que es por la ley, sino la que es por la fe de Cristo, la justicia que es de Dios por la fe;')
    #def __init__(self,book,cap,verse,text,*args):
    def __init__(self,nameBook,idRegistro,idBook,chapter,verse,text,*args):
        self.nameBook = nameBook
        self.idRegistro = idRegistro
        self.idBook=idBook
        self.chapter=chapter
        self.verse=verse
        self.text=text
        self.__counter__=0

    def __getitem__(self,key):
        '''
            metodo para obtener de la clase <variable>['nameBook'] 
        '''
        l={'nameBook':self.nameBook,'idRegistro':self.idRegistro,'idBook':self.idBook,'chapter':self.chapter,'verse':self.verse,'text':self.text}
        if key in l :
            val= l.get(key)
            return val
             

class BibliaInstancia:
    """Representa una base de datos SQLite de Biblia completa con sus 3 modelos."""
    def __init__(self, path):
        self.path = path
        self.path_maestra = os.path.join( 'stdt','bibles','Las_Sagradas_Escrituras.sqlite')   #'bibles/Las_Sagradas_Escrituras.sqlite'
        
        self.meta = metadataModel()
        self.meta.set_custom_db(path)
        
        self.books = bookModel()
        self.books.set_custom_db(path)
        
        self.verses = verseModel()
        self.verses.set_custom_db(path)
        
        # modelos bases de la tabla maestra:
        self.baseModel=metadataModel()
        self.baseModel.set_custom_db(self.path_maestra)
        
        self.baseBooks=bookModel()
        self.baseBooks.set_custom_db(self.path_maestra)
        
        self.baseVerse=verseModel()
        self.baseVerse.set_custom_db(self.path_maestra)
    

class Biblia:
    '''
        esto es una biblia y tiene sus metodos unicos de solo lectura
    '''
    def __init__(self):
        #self.Libro=bookModel()
        #self.Meta=metadataModel()
        #self.verseModel=verseModel()
        self.path_maestra = os.path.join( 'stdt','bibles','Las_Sagradas_Escrituras.sqlite')   #'bibles/Las_Sagradas_Escrituras.sqlite'
        self._biblia_ = None # para instanciar a BibliaInstancia
        self.path=''
        
        
    def set_custom_db(self,valuepath):
        '''
            ajuste de nueva ruta para la biblia
        '''
        self.path = valuepath
        self._biblia_ = BibliaInstancia(valuepath)

    def get_capitulo(self, idLibro, capitulo):
        """
            Recupera todos los versículos de un capitulo de un libro.
        """
        # saber cuantos versiculos son
        total_versiculos=self.countVersiculos( idLibro,capitulo)
        respuesta = []

        for x in range(1, total_versiculos+1 ):
            self.buscarVersiculo(idLibro,capitulo,x)
        

    
    def check_libro(self,nombre_libro,MasterBible=False,idbook=-1): # dejar opcocion para negar esta posibilidad
        '''
            metodo para verificar si un libro existe o esta bien escrito
        '''
        
        nombre_clean = nombre_libro.strip()
        texto =  unicodedata.normalize('NFD',nombre_clean)                                # quitar los acentos a vocales
        patron_busqueda = "".join( c for c in texto if unicodedata.category(c) != 'Mn' ) # quitar espacios y ñ
        
        param_like = f"%{patron_busqueda}%"
        
        #self.Libro.set_custom_db(self.path)
        #resultados = self.Libro._listar_con_filtro_key_(nombre_libro, 'name')
        resultados = self.__checker_libros_(param_like,self.path )
        
        # Si la biblia actual no tiene versículos (archivo pequeño), usamos la maestra
        if not resultados and not MasterBible    :
            Logger.info(f"[Biblia] {self.path} parece incompleta. Usando respaldo: {self.path_maestra}")
            # probar de nuevo con biblia maestra
            resultados = self.__checker_libros_(param_like,self.path_maestra )
            
        if resultados and len(resultados) > 0:
            return resultados
        
        if idbook != -1:
            # alternativa idregistro, book_reference, testament_reference , name
            Logger.error(f"falla al buscar libro:: {idbook}")
            resultados = self._biblia_.baseBooks._un_libro_(idbook)
            if resultados:
                idregistro,book_reference,testament_reference,name = resultados[0]
                return idregistro,book_reference,testament_reference,name
        return None
    
    def __checker_libros_(self,nombre_libro,rutePath):
        if rutePath == self.path :
            # ruta por defecto
            #resultados = self.Libro._listar_con_filtro_key_(nombre_libro, 'name')
            resultados = self._biblia_.books._listar_con_filtro_key_(nombre_libro, 'name')
        else:
            # se utiliza la base
            resultados = self._biblia_.baseBooks._listar_con_filtro_key_(nombre_libro, 'name')
        
        Logger.info(f"{nombre_libro}-->libro{[x for x in resultados]}")
        if resultados :
            # regresar toda la informacion del libro como por ejempolo la cantidad de versiculos que posee
            idregistro,book_reference,testament_reference,name = resultados[0]
            return  idregistro, book_reference, testament_reference , name
        return False
        
    def buscarVersiculo(self, libro, capitulo, versiculo, idbook=-1):
        '''
            metodo principal de busqueda con 3 variantes
            libro = necesario debe contener el nombre del libro a buscar ( se validara )
            capitulo = numero entero , si es = a 0 , y el versiculo igual se obtendra todo el libro como resultado
            versiculo = numero entero, si es = a 0 , se obtendra como resultado el capitulo entero.
        '''
        info_libro = self.check_libro(libro,idbook=idbook)
        if not info_libro: return []

        id_registro_libro = info_libro[0]
        resultado_final = []
        NombreLibro = info_libro[3]
        
        if isinstance(versiculo, str) and "-" in versiculo:
            # caso de buscar por rango
            try:
                partes = versiculo.replace(" ", "").split("-")
                inicio, fin = int(partes[0]), int(partes[1])
                
                for v_num in range(inicio, fin + 1):
                    # como conozco el id del libro lo paso como parametro
                    lectura = self._getVersiculoUnico(id_registro_libro , capitulo, v_num )
                    
                    libro_nombre,v_id, v_book_id,v_chapter,v_verse,v_text=lectura
                    ElRegistro = Reg(NombreLibro , v_id, v_book_id,v_chapter,v_verse,v_text)
                    if lectura: resultado_final.append(ElRegistro)
                return resultado_final
            except Exception as e:
                Logger.error(f"Error en rango: {e}")
        else:
            # caso de bucar por versiculo individual
            lectura = self._getVersiculoUnico(id_registro_libro, capitulo, int(versiculo))
            Logger.info(f"cantidad : {len(lectura)}")
            try:
                if len(lectura) == 6 : # un unico registro son 6 campos
                    try:
                        #lectura = self.__ejecutar_busqueda_completa(id_registro_libro, capitulo, int(versiculo))
                        libro_nombre,v_id, v_book_id,v_chapter,v_verse,v_text = lectura
                        ElRegistro = Reg(NombreLibro , v_id, v_book_id,v_chapter,v_verse,v_text)
                        if lectura:  resultado_final.append( ElRegistro )
                    except TypeError as e:
                        Logger.error(f"Error en registro Unico: {e}")
                        Logger.error(f"valores de busqueda completa: {id_registro_libro}, {capitulo}, {versiculo}")                    
                        Logger.error(f"resultado : {lectura=}")                    
                else:
                    
                    Logger.error(f"ERROR DE TRADUCCION FALLO RESPUESTA{lectura=}")
                    resultado_final=[Reg()] # vacio, invalido
                           
                # se devuelve un listado de un elemento solo RegistroBiblico 
                return resultado_final
                
            except Exception as e:
                Logger.error(f"Error en registro Simple: {e}")
                Logger.error(f"valores de busqueda completa: {libro}, {capitulo}, {versiculo}")
    
    def getAllNameBook(self):
        '''
            obtener todos los nombres de los libros
            name, book_reference_id , testament_reference_id
            testament_reference_id = 1 antiguo, 2 nuevo
            
        '''
        #self.Libro.set_custom_db(self.path)
        #return self.Libro.get_all_names()
        # nombre de los libros en la tabla seleccionada
        respuesta = self._biblia_.books.get_all_names()
        respustaBase = self._biblia_.baseBooks.get_all_names()
        # bucar si FaltanLibros
        for items in respustaBase:
            if not items in respuesta :
                Logger.debug(f"{items=} no esta en {respuesta=}")
            
        return respuesta
        
    def countCapitulos(self,idLibro):
        '''
            responder cuantos capitulos tiene un libro
        en la tabla de correcciones para el conteo hay erroes de sumas
        '''
        resultados = self.__countCaptiulos__(idLibro,self.path_maestra)
        return int(resultados)
    
    def __countCaptiulos__(self,idlibro,path):
        
        if path == self.path :
            respuesta = self._biblia_.verses.contar(idlibro)
        else:
            respuesta =  self._biblia_.baseVerse.contar(idlibro)
        
        return respuesta
    
    def countVersiculos(self,idLibro,Capitulo):
        '''
            responder cuantos capitulos tiene un libro
            mismo que con capitulos, en conteo de versiculos
            utilizo solo tabla maestra
        '''
        resultados = self._biblia_.baseVerse.countVersiculo(idLibro,Capitulo)
        return int(resultados)
    
    def _getVersiculoUnico(self, idbook,capitulo,versiculo):
        '''
            devolver el versiculo biblico
        '''
        rst=self._biblia_.verses.versiculo(idbook,capitulo,versiculo)
        if not rst :
            Logger.warning("no se encontro en la ruta original, devolviendo el de base.")
            # si no existe devolver el de la base
            rst=self._biblia_.baseVerse.versiculo(idbook,capitulo,versiculo)
                  
        return rst
    

class BibliasDisponibles():
    ruta_biblias = os.path.join('stdt', 'bibles')
    
    def __init__(self):
        self.ruta_biblias
        
    def listar_biblias_disponibles(self):
        """
        Escanea la carpeta stdt/bibles y devuelve los nombres de 
        los archivos sqlite/db encontrados.
        """
        ruta_biblias = os.path.join(self.ruta_biblias)
        
        # Asegurarse de que la ruta existe
        if not os.path.exists(ruta_biblias):
            return []

        # Listar solo archivos con extensión .sqlite o .db
        archivos = [f for f in os.listdir(ruta_biblias) 
                    if f.endswith(('.sqlite', '.db'))]
        
        return archivos
        
