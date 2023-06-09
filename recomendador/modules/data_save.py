import pyodbc

class data_save:
    def __init__(self, server, database, username, password,data_carga):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.data_carga = data_carga
        self.connection = None
        

    def connect(self):
        connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password
        self.connection = pyodbc.connect(connection_string)

    def disconnect_save(self):
        if self.connection:
            self.connection.close()
    
    def sql_save(self, truncate,save_q):
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(truncate)
        self.connection.commit()

        valores = self.data_carga[['ID_OFERTA_FORMATIVA','DNI_DOCENTE','PUNTUACION','FECHA_EJEC']].values.tolist()
        cursor.fast_executemany = True
        cursor.executemany(save_q,valores)
        self.connection.commit()
        