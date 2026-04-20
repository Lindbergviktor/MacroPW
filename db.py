import psycopg2 as psql
import configparser

"""
Databasanslutning för applikationen.

Läser konfigurationen från config.ini och skapar uppkoppling till PostgresSQL-databasen
"""

config = configparser.ConfigParser()
config.read('./config.ini')

db_config = {
    'host': config['database']['host'],
    'user': config['database']['user'],
    'port': config['database']['port'],
    'password': config['database']['password'],
    'database': config['database']['database']
}

def get_db_connection():
    """
    Skapar och returnerar en databasanslutning

    Returnerar:
        connection (psycopg2 connection) om lyckad anslutning
        None om anslutningen misslyckas
    """
    try:
        connection = psql.connect(**db_config)
        return connection
        
    except Exception as e:
        print("Fel i anslutning till databasen:", e)
        return None