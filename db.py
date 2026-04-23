import psycopg2
import configparser

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

DB_CONFIG = {
    "host": config.get('database', 'host'),
    "database": config.get('database', 'database'),
    "user": config.get('database', 'user'),
    "password": config.get('database', 'password'),
    "port": config.getint('database', 'port')
}

def get_db_connection():
    """
    Establishes and returns a PostgreSQL database connection.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        raise