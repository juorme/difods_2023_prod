#Librerias 

import numpy as np 
import pandas as pd 
import pyodbc
import random 
import os, sys


from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds


path ='D:/difods_2023_prod/Recomendador'

os.chdir(path)

from models import RecomendadorPopular
import cfg 

#Credenciales
conn = pyodbc.connect(DRIVER = cfg.DRIVER,
                        SERVER = cfg.SERVER,
                        DATABASE = cfg.DATABASE,
                        UID = cfg.UID,
                        PWD = cfg.PWD)

print(conn)

#Extraccion de dataset inicial 
## maestro de cursos de la oferta formativa 
query1 = """SELECT A.ID, 
		A.NOMBRE, 
		A.PROPOSITO,
		A.PUBLICO_OBJETIVO,
		B.DESCRIPCION AS TIPO_OFERTA_FORMATIVA,
		C.DESCRIPCION AS AREA_EDUCATIVA,
		D.DESCRIPCION AS NVEL_EDUCATIVO, 
		E.DESCRIPCION AS MODALIDAD_EDUCATIVA
	FROM [st].[SI_acfm.maestro.oferta_formativa] A
	LEFT JOIN [st].[SI_maestro.parametros] B ON A.TIPO_OFERTA_FORMATIVA = B.ID
	LEFT JOIN [st].[SI_maestro.parametros] C ON A.AREA_EDUCATIVA = C.ID
	LEFT JOIN [st].[SI_maestro.parametros] D ON A.NIVEL_EDUCATIVO = D.ID
	LEFT JOIN [st].[SI_maestro.parametros] E ON A.MODALIDAD_EDUCATIVA = E.ID
	WHERE A.ACTIVO = '1' AND B.DESCRIPCION = 'Curso'"""
oferta_formativa_df = pd.read_sql_query(query1,conn)

## interacciones del usuario con sifods
query2 = """SELECT ID_OFERTA_FORMATIVA,DNI_DOCENTE,PREFERENCIA,VISTAS,CALIFICACIONES,CALIFICACION,COMPARTIR,COMENTARIOS 
			FROM st.[SI_acfm.transaccional.oferta_formativa_accion] 
			WHERE FECHA_MODIFICACION IS NOT NULL"""
acciones_df = pd.read_sql_query(query2,conn)

## Participantes en los cursos de la oferta formativa
query3 = """SELECT ID_OFERTA_FORMATIVA, A.ID_PARTICIPANTE,CUMPLIMIENTO_ACTIVIDAD
			FROM [st].[SI_acfm.transaccional.oferta_formativa_curso_participante] A
			INNER JOIN (
						SELECT DISTINCT(ID_PARTICIPANTE),MAX(ID) AS LASTREG
						FROM [st].[SI_acfm.transaccional.oferta_formativa_curso_participante]
						GROUP BY ID_PARTICIPANTE) AS B ON A.ID=B.LASTREG
			WHERE CUMPLIMIENTO_ACTIVIDAD = 'COMPLETARON'"""
curso_participante_df = pd.read_sql_query(query3,conn)

## maestro de docentes inscritos en sifods
# query4 = """SELECT ID,DNI,APELLIDO_PATERNO,APELLIDO_MATERNO,APELLIDO_CASADA,APELLIDO_MATERNO_CASADA,NOMBRES,PAIS_DOMICILIO,DEPARTAMENTO_DOMICILIO,PROVINCIA_DOMICILIO
# 			FROM [st].[SI_maestro.persona]"""
# maestro_docentes_df = pd.read_sql_query(query4,conn)

#Cerrar la conexion
conn.close()


#Conversion a mayusculas el nombre de la oferta formativa
oferta_formativa_df = oferta_formativa_df.apply(lambda x: x.astype(str).str.upper())

#Reduccion de ocurrencias de ID_OFERTA_FORMATIVA, DNI_DOCENTE
acciones_df = acciones_df.drop_duplicates(['ID_OFERTA_FORMATIVA','DNI_DOCENTE'],keep='last')

#acciones_df.shape


acciones_df_count = acciones_df.groupby(['DNI_DOCENTE','ID_OFERTA_FORMATIVA']).size().groupby('DNI_DOCENTE').size()
print("# usuarios %d : " %len(acciones_df_count))
usuarios_con_interacciones = acciones_df_count[acciones_df_count >=2].reset_index()[['DNI_DOCENTE']]
print("# usuarios con mas de 2 interacciones %d : " % len(usuarios_con_interacciones))


acciones_desde_acciones_df = acciones_df.merge(usuarios_con_interacciones, 
                            how = 'right',
                            left_on ='DNI_DOCENTE',
                            right_on ='DNI_DOCENTE')
print("# de interacciones con usuarios con mas de 2 interacciones en cursos: %d" %len(acciones_desde_acciones_df))

acciones_full_df = acciones_desde_acciones_df[['ID_OFERTA_FORMATIVA','DNI_DOCENTE','VISTAS']]

#Division en cuartiles
acciones_full_df['Q'] = pd.qcut(acciones_full_df['VISTAS'], q=4, labels=False) +1


acciones_full_df= acciones_full_df.drop(['VISTAS'],axis=1)


### MODELO POPULARIDAD ###

#Calcular los curso mas populares de la oferta formativa
curso_popular_df = acciones_full_df.groupby('ID_OFERTA_FORMATIVA')['Q'].sum().sort_values(ascending=False).reset_index()

# modelo_popularidad = RecomendadorPopular(curso_popular_df, oferta_formativa_df)


### MODELO FILTRADO COLABORATIVO ###

# Creación de una tabla dinámica dispersa con usuarios en filas y elementos en columnas
users_items_pivot_matrix_df = acciones_full_df.pivot(index='DNI_DOCENTE',
                                                        columns = 'ID_OFERTA_FORMATIVA',
                                                        values= 'Q').fillna(0)

users_items_pivot_matrix = users_items_pivot_matrix_df.values

users_ids = list(users_items_pivot_matrix_df.index)

users_items_pivot_sparse_matrix = csr_matrix(users_items_pivot_matrix)
U, sigma, Vt = svds(users_items_pivot_sparse_matrix)

sigma = np.diag(sigma)

all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) 

all_user_predicted_ratings_norm = (all_user_predicted_ratings - all_user_predicted_ratings.min()) / (all_user_predicted_ratings.max() - all_user_predicted_ratings.min())

cf_preds_df = pd.DataFrame(all_user_predicted_ratings_norm, columns = users_items_pivot_matrix_df.columns, index=users_ids)
cf_preds_df = cf_preds_df.reset_index(names=['DNI_DOCENTE'])
cf_preds_df


#Dataset de resultados
df_f = cf_preds_df.melt(id_vars='DNI_DOCENTE' , var_name='ID_OFERTA_FORMATIVA',value_name='PRED_RATING')


