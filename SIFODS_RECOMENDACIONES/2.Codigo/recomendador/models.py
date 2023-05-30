class RecomendadorPopular:

    MODEL_NAME = 'Popularidad'

    def __init__(self, popularidad_df, items_df=None):
        self.popularidad_df = popularidad_df
        self.items_df = items_df

    def get_model_name(self) :
        return self.MODEL_NAME

    def recommend_items(self, DNI_DOCENTE, items_para_ignorar=[], topn=5, verbose=False):
        # Recomienda los cursos más populares que el usuario no ha calificado
        recomendaciones_df = self.popularidad_df[~self.popularidad_df['ID_OFERTA_FORMATIVA'].isin(items_para_ignorar)] \
                                                                .sort_values('Q', ascending = False) \
                                                                .head(topn)
        if verbose :
            if self.items_df is None :
                raise Exception(' "items_df" is required in verbose mode')

            recomendaciones_df = recomendaciones_df.merge(self.items_df, how='left',
                                                            left_on='ID_OFERTA_FORMATIVA',
                                                            right_on = 'ID_OFERTA_FORMATIVA')
        return recomendaciones_df




class CFRecommender:
    
    MODEL_NAME = 'Filtrado Colaborativo'
    
    def __init__(self, cf_predictions_df, items_df=None):
        self.cf_predictions_df = cf_predictions_df
        self.items_df = items_df
        
    def get_model_name(self):
        return self.MODEL_NAME
        
    def recommend_items(self, user_id, items_para_ignorar=[], topn=10, verbose=False):
        # Get and sort the user's predictions
        sorted_user_predictions = self.cf_predictions_df[user_id].sort_values(ascending=False) \
                                    .reset_index().rename(columns={user_id: 'PUN_PREDICT'})

        # Recommend the highest predicted rating movies that the user hasn't seen yet.
        recommendations_df = sorted_user_predictions[~sorted_user_predictions['ID_OFERTA_FORMATIVA'].isin(items_para_ignorar)] \
                               .sort_values('PUN_PREDICT', ascending = False) \
                               .head(topn)

        if verbose:
            if self.items_df is None:
                raise Exception('"items_df" is required in verbose mode')

            recommendations_df = recommendations_df.merge(self.items_df, how = 'left', 
                                                          left_on = 'ID_OFERTA_FORMATIVA', 
                                                          right_on = 'ID')
        return recommendations_df

