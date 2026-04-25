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
Filen finns inkluderad i zip-filen som lämnas in, och behöver placeras i projektmappen (samma mapp som som app.py) för att programmet ska fungera.

Starta applikationen
Kör filen app.py och gå till http://127.0.0.1:5000 

Testanvändare
För att testa applikationen kan följande inloggning användas:
- Email: anna@mail.com
- Lösenord: lösenord123