import pyodbc
import pandas as pd

class data_loader:
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password
        self.connection = pyodbc.connect(connection_string)

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def read_sql(self, query):
        if not self.connection:
            self.connect()
        result = pd.read_sql(query, self.connection)
        return result