# =========================================
# Proyecto: Proyecto Análisis de temas en foros 
# Autor: Junior T. Ortiz Mejia
# Fecha: 17 de Agosto de 2023
# Descripción: El obbjetivo es identificar los temas relevantes en los foros del PNFDS
# =========================================

# Librerias a usar 
import pandas as pd 
import pyodbc 
import re 
import matplotlib.pyplot as plt

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import joblib 
import os 


# Configurar el espacio de trabajo
path ='D:/difods_2023_prod/foros'
os.chdir(path)



# Credenciales 
conn = pyodbc.connect(DRIVER = '{ODBC Driver 17 for SQL Server}',
                      SERVER = 'med000008646',
                      DATABASE = 'BD_BA',
                      UID = 'usconsulta',
                      PWD = 'consulta')


## maestro de cursos de la oferta formativa 
query1 = """SELECT  * FROM [dbo].[MON_foros]
            WHERE usuario_post_forum not in ('2','3','19797','276201') and dni != '' and curso_id in (24,26,4)"""
    
foros_df = pd.read_sql_query(query1,conn)

#Cerrar la conexion
conn.close()



## Selección, limpieza y transformación

mensaje = foros_df['mensaje']

# Convertir a minúsculas
mensaje= mensaje.str.lower()
# Eliminar signos de puntuación
mensaje = mensaje.apply(lambda x: re.sub(r'[^\w\s]', '', x))

# Tokenización
mensaje = mensaje.apply(word_tokenize)


# Eliminación de stop words
custom_stopwords = set(['buenas','buenos','dias','tardes','tengo','espero','ie','auala','aula','traves','tener','espero',
                        'promuevo','promover','democracia','intercultural','convivencia','áreas','competencia',
                        'desarrollo','lectura','leer','lectora','desarrollar','tener','realizar','hacer',
                        'curricular','diverso','diferente','noches','estimada','estimadas'])

stop_words = set(stopwords.words('spanish'))

stop_words.update(custom_stopwords)
mensaje = mensaje.apply(lambda x: [word for word in x if word not in stop_words])



# Lematización
lemmatizer = WordNetLemmatizer()
mensaje = mensaje.apply(lambda x: [lemmatizer.lemmatize(word) for word in x])

# Unir tokens nuevamente en mensajes
mensaje = mensaje.apply(lambda x: ' '.join(x))


### Mineria de Texto
# Crear una matriz de términos (bag of words) usando CountVectorizer
vectorizer = CountVectorizer(max_features=500)  # Puedes ajustar el número de características
X = vectorizer.fit_transform(mensaje)


#Importar el modelo 
lda_model =joblib.load("lda_model1.pkl")


# Obtener la distribución de tópicos para cada mensaje
topic_distribution = lda_model.transform(X)

# Asociar cada mensaje al tópico más relevante
topic_assignments = topic_distribution.argmax(axis=1)

# Agregar las asignaciones de tópicos a tus datos originales
foros_df['topic'] = topic_assignments + 1
foros_df['preprocesado'] = mensaje

df_f = foros_df[['curso_id','foro_id','dni','preprocesado','topic','grupo_id']]

#Carga de datos 
conn3 = pyodbc.connect(DRIVER = '{ODBC Driver 17 for SQL Server}',
                      SERVER = 'med000008646',
                      DATABASE = 'BD_BA',
                      UID = 'usconsulta',
                      PWD = 'consulta')

cursor = conn3.cursor()
cursor.fast_executemany = True
# Borrar los datos de la tabla ml.docentes_foros_pnfds
cursor.execute("TRUNCATE TABLE ml.docentes_foros_pnfds")
conn3.commit()


# Insertar valores
sql_insert = """INSERT INTO ml.docentes_foros_pnfds VALUES (?,?,?,?,?,?)"""
val = df_f[['curso_id','foro_id','dni','preprocesado','topic','grupo_id']].values.tolist()
cursor.fast_executemany = True
cursor.executemany(sql_insert, val)
conn3.commit()
# Cerrar las conexiones
conn3.close()