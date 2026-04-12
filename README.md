MacroPW - Grupp 6

Repository: https://github.com/Lindbergviktor/MacroPW

Installera
För att kunna köra programmet behöver följande Python-paket installeras.
Kör detta kommando i terminalen:
pip install flask psycopg2-binary

- flask: webbramverket som används
- psycopg2-binary: används för att koppla upp mot PostgreSQL-databasen

Konfiguration
Programmet använder en fil som heter “config.ini” för att koppla upp mot databasen.
Filen finns inkluderad i zipfilen och behöver placeras i samma mapp som “app.py” för att kunna köra programmet.

Starta applikationen
Kör filen “app.py” och gå till http://127.0.0.1:5000 