# =========================================
# Proyecto: Proyecto Cluster de actividades de docentes
# Autor: Junior T. Ortiz Mejia
# Fecha: 13 de Agosto de 2023
# Descripción: El obbjetivo es utilizar las las actividades de los cursos para realizar la agrupación de docentes
# =========================================

#Librerias Usadas
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import scale
from sklearn.metrics import silhouette_score, davies_bouldin_score

from sklearn.cluster import KMeans

import warnings
warnings.filterwarnings("ignore") 

import datetime 
import pyodbc
import joblib 

import os 



# Configurar el espacio de trabajo
path ='D:/difods_2023_prod/cluster'
os.chdir(path)





# Credenciales 
conn = pyodbc.connect(DRIVER = '{ODBC Driver 17 for SQL Server}',
                      SERVER = 'med000008646',
                      DATABASE = 'BD_BA',
                      UID = 'usconsulta',
                      PWD = 'consulta')


#Extraccion del dataset inical 
## maestro de cursos de la oferta formativa 
query1 = """SELECT * 
            FROM [dbo].[MON_Transaccional_Preguntas] 
            WHERE COURSE_ID IN ('5') """

df = pd.read_sql_query(query1,conn)


df_1=df[['COURSE_ID','USER_DNI','QUIZ_CUESTIONARIO','QUIZ_GRADES_ULTIMA_NOTA']]
df_table = pd.pivot_table(df_1, values='QUIZ_GRADES_ULTIMA_NOTA', columns=['QUIZ_CUESTIONARIO'], index=['COURSE_ID','USER_DNI'])


df_table.reset_index(inplace=True)

df_table.fillna(-1,inplace=True)



valores = [-2, 0, 11,20]
cat = [-1,1,2]
df_table['CE']= pd.cut(df_table['Cuestionario de entrada'], bins=valores,labels=cat).astype('int')
df_table['CS']= pd.cut(df_table['Cuestionario de salida'], bins=valores,labels=cat).astype('int')
df_table['W12']= pd.cut(df_table['W1 2: Desarrollo Cuestionario'], bins=valores,labels=cat).astype('int')
df_table['W22']= pd.cut(df_table['W2 2: Desarrollo Cuestionario'], bins=valores,labels=cat).astype('int')



df_norm = StandardScaler().fit_transform(df_table.drop(['COURSE_ID','USER_DNI'],axis=1))

#Importar el modelo 
kmeans =joblib.load("kmeans_cluster1.pkl")


#Realizar las predicciones con el modelo preentrenado
predicted_clusters_kmeans = kmeans.predict(df_norm)


df_table['CLUSTER'] = predicted_clusters_kmeans + 1


#Cambiar el nombre de las columnas
df_table.rename({'QUIZ_CUESTIONARIO':'IDX','Cuestionario de entrada':'N_CE','Cuestionario de salida':'N_CS','W1 2: Desarrollo Cuestionario':'N_W12','W2 2: Desarrollo Cuestionario':'N_W22'}, axis=1 , inplace=True)

#calcular la fecha de ejecución del modelo 
df_table['FECHA_REPORTE'] = datetime.datetime.now().date()


#Carga de datos 
conn3 = pyodbc.connect(DRIVER = '{ODBC Driver 17 for SQL Server}',
                      SERVER = 'med000008646',
                      DATABASE = 'BD_BA',
                      UID = 'usconsulta',
                      PWD = 'consulta')

cursor = conn3.cursor()
cursor.fast_executemany = True
# Borrar los datos de la tabla ml.cluste_2022
cursor.execute("TRUNCATE TABLE ml.docentes_cluster_pnfds")
conn3.commit()

# Insertar valores
sql_insert = """INSERT INTO ml.docentes_cluster_pnfds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
val = df_table[['COURSE_ID', 'USER_DNI', 'N_CE','N_CS','N_W12','N_W22','CE','CS','W12','W22','CLUSTER','FECHA_REPORTE']].values.tolist()
cursor.fast_executemany = True
cursor.executemany(sql_insert, val)
conn3.commit()
# Cerrar las conexiones
conn3.close()



