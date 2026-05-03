# MacroPW

En webbaserad applikation för kost- och träningsloggning, byggd med Flask, Bootstrap och PostgreSQL.

## Innehåll

- [Funktioner](#funktioner)
- [Teknikstack](#teknikstack)
- [Förutsättningar](#förutsättningar)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Starta applikationen](#starta-applikationen)
- [Projektstruktur](#projektstruktur)
- [Testanvändare](#testanvändare)

## Funktioner

- Registrering och inloggning av användare
- Loggning av måltider med kalori- och makroberäkning
- Hantering av livsmedel
- Skapande och redigering av sparade måltider
- Träningsloggning
- Statistiksida med daglig och veckovis översikt
- Personligt kalorimål beräknat utifrån användarprofil

## Teknikstack

| Kategori       | Teknik                  |
|----------------|-------------------------|
| Backend        | Python 3, Flask         |
| Databas        | PostgreSQL, psycopg2    |
| Frontend       | Jinja2, Bootstrap, CSS  |

## Förutsättningar

- Python 3.x
- En körande PostgreSQL-instans med projektets databas

## Installation

1. Klona repot:
   ```bash
   git clone https://github.com/Lindbergviktor/MacroPW.git
   cd MacroPW
   ```

2. Installera beroenden:
   ```bash
   pip install flask psycopg2-binary
   ```

## Konfiguration

Applikationen ansluter till databasen via filen `config.ini`. Denna fil tillhandahålls separat med korrekta värden redan ifyllda.

Placera `config.ini` i projektmappen (samma mapp som `app.py`) innan du startar applikationen.

> **OBS:** `config.ini` är listad i `.gitignore` och ska aldrig checkas in i versionshanteringen eftersom den innehåller känsliga uppgifter.

## Starta applikationen

```bash
python app.py
```

Öppna sedan webbläsaren och gå till: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Testanvändare

För att testa applikationen utan att registrera ett nytt konto:

| Fält     | Värde           |
|----------|-----------------|
| E-post   | anna@mail.com   |
| Lösenord | lösenord123     |

## Projektstruktur

```
MacroPW/
├── app.py               # Applikationens routes och logik
├── db.py                # Databasanslutning
├── nutrition.py         # Beräkningar för kalorimål och ålder
├── config.ini           # Databasuppgifter (ingår ej i repo)
├── config.ini.example   # Mall för konfiguration
├── static/
│   ├── style.css        # Stilsättning
│   └── images/          # Bilder
└── templates/           # Jinja2-mallar (HTML)
    ├── index.html
    ├── login.html
    ├── register.html
    ├── meals.html
    ├── foods.html
    ├── statistics.html
    └── ...
```
