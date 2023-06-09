from datetime import datetime
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
import numpy as np
import pandas as pd

class FCRecomendador:
    def __init__(self,datafinal,data_cursos):
        self.datafinal = datafinal
        self.data_cursos = data_cursos

    def model_process(self):
        #Creación de la tabla dispersa con usuarios en filas y cursos en columnas
        user_items_pivot_df = self.datafinal.pivot(index = 'DNI_DOCENTE',
                                                   columns = 'ID_OFERTA_FORMATIVA',
                                                   values ='PUNTAJE').fillna(0)
        users_pivot_matrix = user_items_pivot_df.values
        users_ids = list(user_items_pivot_df.index)
        users_items_pivot_sparse_matrix = csr_matrix(users_pivot_matrix)
        U, sigma, Vt = svds(users_items_pivot_sparse_matrix)
        sigma = np.diag(sigma)

        all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) 

        all_user_predicted_ratings_norm = (all_user_predicted_ratings - all_user_predicted_ratings.min()) / (all_user_predicted_ratings.max() - all_user_predicted_ratings.min())

        cf_preds_df = pd.DataFrame(all_user_predicted_ratings_norm, columns = user_items_pivot_df.columns, index=users_ids)
        cf_preds_ratings = cf_preds_df.reset_index().melt(id_vars='index',var_name='ID_OFERTA_FORMATIVA',value_name='PUNTUACION') \
                                                                                                                                .rename({'index':"DNI_DOCENTE"},axis=1)
        users_preds_cruce = cf_preds_ratings.merge(self.data_cursos, how='left', left_on=['ID_OFERTA_FORMATIVA','DNI_DOCENTE'],right_on=['ID_OFERTA_FORMATIVA','USUARIO_DOCUMENTO'])
        
        users_preds_cruce = users_preds_cruce.loc[users_preds_cruce['USUARIO_DOCUMENTO'].isna()]
       
        users_pred_topn = users_preds_cruce.sort_values(['DNI_DOCENTE','PUNTUACION'],ascending=False).groupby('DNI_DOCENTE').head(3)

        users_pred_topn = users_pred_topn.drop('USUARIO_DOCUMENTO',axis=1)
        
        users_pred_topn = users_pred_topn.reindex(columns=['ID_OFERTA_FORMATIVA','DNI_DOCENTE','PUNTUACION'],copy=False)
        users_pred_topn["FECHA_EJEC"] = datetime.today().strftime('%Y-%m-%d')
        return users_pred_topn