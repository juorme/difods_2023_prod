#############################################################################################
#Proyecto: Modelo de Recomendación para la oferta formativa SIFODS
#Creado por: Junior Ortiz
#Fecha de Creación: 01/05/2023
#Fecha de Modificación: 31/05/2023
#############################################################################################

from dotenv import load_dotenv
import os 
import pandas as pd

path ='D:/difods_2023_prod/recomendador'
os.chdir(path)

#sys.path.append('D:/difods_2023_prod/recomendador')
from modules.data_loader import data_loader
from modules.data_preprocessor import DataPreprocessor
from modules.model_fc import FCRecomendador
from modules.model_pop import PopRecomendador
from modules.data_save import data_save



#carga de variables de entorno
load_dotenv()
db_server = os.getenv('DB_SERVER')
db_database = os.getenv('DB_DATABASE')
db_usuario = os.getenv('DB_USUARIO')
db_contra = os.getenv('DB_CONTRA')

#Parametros de conexion a base de datas
db = data_loader(db_server, db_database, db_usuario, db_contra)
db.connect()

#Carga de datos
oferta_formativa_df = db.read_sql("""SELECT A.ID, 
		A.NOMBRE, 
		A.PROPOSITO,
		A.PUBLICO_OBJETIVO,
		B.DESCRIPCION AS TIPO_OFERTA_FORMATIVA,
		C.DESCRIPCION AS AREA_EDUCATIVA,
		D.DESCRIPCION AS NVEL_EDUCATIVO, 
		E.DESCRIPCION AS MODALIDAD_EDUCATIVA
	FROM [st].[SI_acfm.maestro.oferta_formativa] A
	LEFT JOIN [st].[SI_dbo.maestro.parametros] B ON A.TIPO_OFERTA_FORMATIVA = B.ID
	LEFT JOIN [st].[SI_dbo.maestro.parametros] C ON A.AREA_EDUCATIVA = C.ID
	LEFT JOIN [st].[SI_dbo.maestro.parametros] D ON A.NIVEL_EDUCATIVO = D.ID
	LEFT JOIN [st].[SI_dbo.maestro.parametros] E ON A.MODALIDAD_EDUCATIVA = E.ID
	WHERE A.ACTIVO = '1' AND B.DESCRIPCION = 'Curso'""")

acciones_df = db.read_sql("""SELECT ID_OFERTA_FORMATIVA,DNI_DOCENTE,PREFERENCIA,VISTAS,CALIFICACIONES,CALIFICACION,COMPARTIR,COMENTARIOS 
				FROM [st].[SI_acfm.transaccional.oferta_formativa_accion]""")

# df 02
curso_participante_df = db.read_sql("""SELECT A.ID_OFERTA_FORMATIVA,B.USUARIO_DOCUMENTO
				FROM [st].[SI_acfm.transaccional.oferta_formativa_curso_participante_ultimo] A
				INNER JOIN [st].[SI_acfm.transaccional.oferta_formativa_participante] B on A.ID_PARTICIPANTE=B.ID_PARTICIPANTE
				WHERE A.CUMPLIMIENTO_ACTIVIDAD = 'COMPLETARON'""")

#Desconectarse de la base de datos 
db.disconnect()

#Pre-procesamineto de datos 
preprocessor = DataPreprocessor(data=acciones_df,data2=oferta_formativa_df,data3=curso_participante_df)
acciones_full_df = preprocessor.preprocess_data()

#Modelo filtrado colaborativo
model_process = FCRecomendador(datafinal=acciones_full_df,data_cursos=curso_participante_df)
cf_preds_ratings = model_process.model_process()

#Modelo Popularidad
model_process_pop = PopRecomendador(acciones_full_df)
pop_preds_ratings = model_process_pop.model_process_pop()

preds_ratings= pd.concat([cf_preds_ratings, pop_preds_ratings])

#Carga de datos a la tabla ml_recomendación
ds = data_save(db_server, db_database, db_usuario, db_contra,preds_ratings)
ds.connect()
truncate = "TRUNCATE TABLE [dbo].[ML_RECOMENDACION]"
save_q = "INSERT INTO [dbo].[ML_RECOMENDACION] VALUES (?,?,?,?)"
ds.sql_save(truncate, save_q)
ds.disconnect_save()
