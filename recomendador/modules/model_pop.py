from datetime import datetime
import pandas as pd

class PopRecomendador:
    def __init__(self,dataacciones):
        self.dataacciones = dataacciones

    def model_process_pop(self):
            #Calculando los cursos con mayor interacción
            cursos_pop_df = self.dataacciones.groupby('ID_OFERTA_FORMATIVA')['PUNTAJE'].sum().sort_values(ascending=False).reset_index().head(5)
            cursos_pop_df['PUNTUACION'] =  (cursos_pop_df.PUNTAJE -cursos_pop_df.PUNTAJE.min())/(cursos_pop_df.PUNTAJE.max()-cursos_pop_df.PUNTAJE.min())
            cursos_pop_df['DNI_DOCENTE'] = '00000001'
            cursos_pop_df["FECHA_EJEC"] = datetime.today().strftime('%Y-%m-%d')
            cursos_pop_df = cursos_pop_df.reindex(columns  =['ID_OFERTA_FORMATIVA','DNI_DOCENTE','PUNTUACION','FECHA_EJEC'],copy=False)
            return cursos_pop_df
