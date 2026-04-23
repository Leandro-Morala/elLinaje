import os

defaultConfig={
    'VERSION': [0,3,1] ,
    
    # config file
    'CONFIG_PATH' :         os.path.join('data','config.json' ), 
     
    # base de datos nombre de archivo
    'DB_PATH' :             os.path.join('data', 'ElLinaje.db'),
    'IMG_PATH' :            os.path.join('data','img' ),
    'FORMATO_FECHA' : '%Y-%m-%d',                 # FORMATO DE FECHA
    'FORMATO_HORA' : '%H:%M:%S',                   # FORMATO DE HORA
    
    # libreria de biblias
    'SATIC_BIBLES_PATH' :   os.path.join('stdt','bibles'),
    
    # estilo grafico
    'SATIC_FONT_PATH' :     os.path.join('stdt','fonts'),
    'FONT_NAME':            os.path.join('stdt','fonts',"LaMonarchiedeSaintOmbre.ttf"),
    'FONT_SIZE': '40sp'
    
    }
