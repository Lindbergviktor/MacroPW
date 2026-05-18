from contextlib import contextmanager
import configparser

import psycopg2

# Läser konfiguration från config.ini
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
    Upprättar och returnerar en anslutning till PostgreSQL-databasen.
    
    Returns:
        psycopg2.connection: Objekt som representerar databasanslutningen.
        
    Raises:
        psycopg2.Error: Om anslutningen misslyckas
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        raise


@contextmanager
def get_db():
    """Ger en cursor med automatisk commit/rollback och städning."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
