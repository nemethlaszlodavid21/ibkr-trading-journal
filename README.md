# IBKR Trading Journal

Python és Streamlit alapú kereskedési teljesítményelemző webalkalmazás Interactive Brokers Activity Statement CSV-fájlok feldolgozásához.

## Funkciók

- IBKR Tevékenységkimutatás CSV-feltöltése
- tranzakciós adatok automatikus feldolgozása
- BUY és SELL tranzakciók felismerése
- automatikus devizakonverziók kiszűrése
- lezáró tranzakciók azonosítása
- realizált P/L számítása
- win rate
- nyerő és vesztes trade-ek száma
- profit factor
- legjobb és legrosszabb lezárás
- kumulált P/L grafikon
- instrumentumonkénti teljesítmény
- EUR és USD eredmények külön kezelése
- interaktív Streamlit dashboard

## Technológiák

- Python
- Pandas
- Streamlit
- Plotly
- Git és GitHub

## Telepítés

A repository klónozása után telepítsd a szükséges csomagokat:

```bash
python3 -m pip install -r requirements.txt