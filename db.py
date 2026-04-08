import psycopg2 as psql
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

db_config = {
    'host': config['database']['host'],
    'user': config['database']['user'],
    'port': config['database']['port'],
    'password': config['database']['password'],
    'database': config['database']['database']
}

try:
    connection = psql.connect(**db_config)
    print("Uppkopplad till databasen")
    
except Exception as e:
    print("Fel i anslutning till databasen:", e)
    exit()