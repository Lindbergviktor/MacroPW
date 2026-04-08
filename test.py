from decimal import Decimal
from db import connection

cursor = connection.cursor()
cursor.execute("SELECT * FROM food")
rows = cursor.fetchall()

for row in rows:
    # Konvertera Decimal till int om det är heltal
    converted_row = [int(value) if isinstance(value, Decimal) else value for value in row]
    print(converted_row)