import pandas as pd

class DataPreprocessor:
    def __init__(self,data,data2,data3):
        self.data = data
        self.data2 = data2
        self.data3 = data3

    def preprocess_data(self):
        #Eliminar valores duplicados de acciones_df
        self.data.drop_duplicates(['ID_OFERTA_FORMATIVA','DNI_DOCENTE'],keep='last',inplace=True)
        
        #Pendiente realizar el cruce con los id de los cursos de la oferta formativa
        #del cruce sale acciones_df_validos
        cursos_validos = list(self.data2['ID'])

        docentes_validos = list(self.data3['USUARIO_DOCUMENTO'].unique())
        

        acciones_df_validos = self.data[self.data['ID_OFERTA_FORMATIVA'].isin(cursos_validos)]
        # # #acciones_df_validos = self.data2.merge(self.data, how='left',left_on='ID',right_on='ID_OFERTA_FORMATIVA')

        #exclusión de docentes que no se encuentran en los cursos completados 
        acciones_df_validos = acciones_df_validos[acciones_df_validos['DNI_DOCENTE'].isin(docentes_validos)]
        

        # #Exclusión de registros con VISTAS > 0 
        acciones_df_validos =acciones_df_validos[acciones_df_validos['VISTAS']>0]

        #Selección de usuarios con mayor a 2  cursos
        usuario_interaccion_count = acciones_df_validos.groupby(['DNI_DOCENTE','ID_OFERTA_FORMATIVA']).size().groupby('DNI_DOCENTE').size()
        usuario_interaccion_mayor_2 = usuario_interaccion_count[usuario_interaccion_count >= 2].reset_index()
        usuario_considerado = list(usuario_interaccion_mayor_2['DNI_DOCENTE'])

        # "Exclusión de usuario con mas de dos acciones en acciones_df"
        acciones_seleccionadas = acciones_df_validos[acciones_df_validos['DNI_DOCENTE'].isin(usuario_considerado)]

        # #Selección de variables a usar
        acciones_full_df = acciones_seleccionadas[['ID_OFERTA_FORMATIVA','DNI_DOCENTE','VISTAS']]

        # #Calculo de la variable PUNTAJE
        acciones_full_df['PUNTAJE'] = pd.qcut(acciones_full_df['VISTAS'], q=5, labels=False,duplicates='drop') + 1

        acciones_full_df.drop(['VISTAS'],axis=1,inplace=True)
        return acciones_full_df