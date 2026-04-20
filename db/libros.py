from db.base import db

class LibrosBiblicosModel(db):
    def table_name(self):
        return 'librosbiblicos'
    
    def table_list_columns(self):
        return [
            ('id',0,'INTEGER PRIMARY KEY AUTOINCREMENT'),     
            ('nombre','','TEXT UNIQUE NOT NULL'),
            ('id_libro',0,'INT'),
            ('total_capitulos',0,'INT NOT NULL'),
            ('version','AUTOR','TEXT DEFAULT \'AUTOR\''),                          # publicacion y datos, en caso de cargado manual dice AUTOR
            ('tag','','TEXT DEFAULT \'{}\'')
        ]   

    def insertar(self, nombre , id_libro, total_capitulos , version ='AUTOR'  , tag ="{}"):
        '''
            modulo para insertar libros dentro de la base de datos generica
        '''
        return self.__insertar__(
            nombre=nombre,
            total_capitulos=total_capitulos,
            id_libro=id_libro,
            version=version,
            tag=tag)

    def autoinsertar(self):
        # insertar registros automaticos
        libros_biblia = [
            [ "GÉNESIS",  1,  50  ] ,[ "EXODO",  2,  40  ] , [ "LEVITICUS",  3,  27 ] , [ "NÚMEROS",  4,  36  ] ,[ "DEUTERONOMIO",  5,  34 ] ,
            [ "JOSUÉ",  6,  24 ] , [ "JUECES",  7,  21 ] ,[ "RUT",  8,  4 ] ,[ "1 SAMUEL",  9,  31 ] ,[ "2 SAMUEL",  10,  24 ] ,[ "1 REYES",  11,  22 ] ,
            [ "2 REYES",  12,  25 ] ,[ "1 CRÓNICAS",  13,  29 ] ,[ "2 CRÓNICAS",  14,  36 ] ,[ "ESDRAS",  15,  10 ] ,[ "NEHEMÍAS",  16,  13 ] ,
            [ "ESTER",  17,  10 ] ,[ "JOB",  18,  42 ] ,[ "SALMOS",  19,  150 ] ,[ "PROVERBIOS",  20,  31 ] ,[ "ECLESIASTÉS",  21,  12 ] ,
            [ "CANTARES",  22,  8 ] ,[ "ISAÍAS",  23,  66 ] ,[ "JEREMÍAS",  24,  52 ] ,[ "LAMENTACIONES",  25,  5 ] ,[ "EZEQUIEL",  26,  48 ] ,
            [ "DANIEL",  27,  12 ] ,[ "OSEAS",  28,  14 ] ,[ "JOEL",  29,  3 ] ,[ "AMOS",  30,  9 ] ,[ "ABDÍAS",  31,  1 ] , [ "JONÁS",  32,  4 ] ,
            [ "MIQUEAS",  33,  7 ] , [ "NAHÚM",  34,  3 ] ,[ "HABACUC",  35,  3 ] ,
            [ "SOFONÍAS",  36,  3 ] ,[ "HAGEO",  37,  2 ] ,[ "ZACARÍAS",  38,  14 ] ,[ "MALAQUÍAS",  39,  4 ] ,[ "MATEO",  40,  28 ] ,[ "MARCOS",  41,  16 ] ,
            [ "LUCAS",  42,  24 ] ,[ "JUAN",  43,  21 ] , [ "HECHOS",  44,  28 ] , [ "ROMANOS",  45,  16 ] ,[ "1 CORINTIOS",  46,  16 ] ,
            [ "2 CORINTIOS",  47,  13 ] , [ "GÁLATAS",  48,  6 ] , [ "EFESIOS",  49,  6 ] , [ "FILIPENSES",  50,  4 ] , [ "COLOSENSES",  51,  4 ] ,
            [ "1 TESALONICENSES",  52,  5 ] ,[ "2 TESALONICENSES",  53,  3 ] , [ "1 TIMOTEO",  54,  6 ] , [ "2 TIMOTEO",  55,  4 ] , [ "TITO",  56,  3 ] ,
            [ "FILEMÓN",  57,  1 ] ,[ "HEBREOS",  58,  13 ] , [ "SANTIAGO",  59,  5 ] , [ "1 PEDRO",  60,  5 ] , [ "2 PEDRO",  61,  3 ] ,
            [ "1 JUAN",  62,  5 ] , [ "2 JUAN",  63,  1 ] , [ "3 JUAN",  64,  1 ] , [ "JUDAS",  65,  1 ] , [ "APOCALIPSIS",  66,  22 ] ]
        for n in libros_biblia :
            self.insertar( n[0], n[1], n[2], 'DEFAULT' ,'{"content":"none"}' )
    
    

            
