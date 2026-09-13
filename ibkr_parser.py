import argparse
import csv
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# SAJÁT HIBAOSZTÁLY
# --------------------------------------------------

class IBKRImportHiba(ValueError):
    pass


# --------------------------------------------------
# MAGYAR ÉS ANGOL ELNEVEZÉSEK
# --------------------------------------------------

UGYLET_SZEKCIOK = {
    "Ügyletek",
    "Trades",
}

RESZVENY_KATEGORIAK = {
    "Részvények",
    "Stocks",
}

OSZLOP_NEVEK = {
    "Eszközkategória": "eszkoz_kategoria",
    "Asset Category": "eszkoz_kategoria",

    "Deviza": "deviza",
    "Currency": "deviza",

    "Ticker kód": "ticker",
    "Symbol": "ticker",

    "Dátum / Idő": "datum",
    "Date/Time": "datum",

    "Mennyiség": "elojeles_mennyiseg",
    "Quantity": "elojeles_mennyiseg",

    "Ügyleti ár": "ar",
    "T. Price": "ar",

    "Jut./díj": "jutalek",
    "Comm/Fee": "jutalek",

    "Realizált P/L": "realizalt_pl",
    "Realized P/L": "realizalt_pl",
}


KOTELEZO_OSZLOPOK = {
    "eszkoz_kategoria",
    "deviza",
    "ticker",
    "datum",
    "elojeles_mennyiseg",
    "ar",
    "jutalek",
    "realizalt_pl",
}


KIMENETI_OSZLOPOK = [
    "datum",
    "ticker",
    "irany",
    "mennyiseg",
    "elojeles_mennyiseg",
    "ar",
    "jutalek",
    "deviza",
    "realizalt_pl",
]


# --------------------------------------------------
# CSV-FÁJL ELLENŐRZÉSE
# --------------------------------------------------

def csv_fajl_ellenorzese(csv_utvonal):
    csv_fajl = Path(csv_utvonal)

    if not csv_fajl.exists():
        raise IBKRImportHiba(
            "A kiválasztott CSV-fájl nem található."
        )

    if not csv_fajl.is_file():
        raise IBKRImportHiba(
            "A kiválasztott elérési út nem fájl."
        )

    if csv_fajl.suffix.lower() != ".csv":
        raise IBKRImportHiba(
            "Nem megfelelő fájltípus. "
            "Kérlek, CSV-fájlt tölts fel."
        )

    if csv_fajl.stat().st_size == 0:
        raise IBKRImportHiba(
            "A feltöltött CSV-fájl üres."
        )

    return csv_fajl


# --------------------------------------------------
# SZÁMOK ÁTALAKÍTÁSA
# --------------------------------------------------

def szam_atalakitasa(
    ertek,
    mezo_neve,
    ticker,
    alapertelmezett=None,
):
    if ertek is None or str(ertek).strip() == "":
        if alapertelmezett is not None:
            return alapertelmezett

        raise IBKRImportHiba(
            f"Hiányzó {mezo_neve} érték "
            f"a(z) {ticker} instrumentumnál."
        )

    try:
        return float(
            str(ertek)
            .strip()
            .replace(" ", "")
        )

    except ValueError as hiba:
        raise IBKRImportHiba(
            f"Hibás {mezo_neve} érték "
            f"a(z) {ticker} instrumentumnál: "
            f"{ertek}"
        ) from hiba


# --------------------------------------------------
# KIMUTATÁS IDŐSZAKA
# --------------------------------------------------

def kimutatas_idoszak_lekerese(csv_utvonal):
    csv_fajl = csv_fajl_ellenorzese(
        csv_utvonal
    )

    try:
        with csv_fajl.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as fajl:

            csv_olvaso = csv.reader(fajl)

            for sor in csv_olvaso:
                if (
                    len(sor) >= 4
                    and sor[0] == "Statement"
                    and sor[1] == "Data"
                    and sor[2] in {
                        "Period",
                        "Időszak",
                    }
                ):
                    return sor[3]

    except UnicodeDecodeError as hiba:
        raise IBKRImportHiba(
            "A CSV karakterkódolása nem megfelelő. "
            "IBKR-ből közvetlenül exportált "
            "UTF-8 CSV szükséges."
        ) from hiba

    return "Az időszak nem található"


# --------------------------------------------------
# IBKR TRANZAKCIÓK BETÖLTÉSE
# --------------------------------------------------

def ibkr_tranzakciok_betoltese(csv_utvonal):
    csv_fajl = csv_fajl_ellenorzese(
        csv_utvonal
    )

    tranzakciok = []
    fejlec = None
    ugylet_szekcio_megtalalva = False

    try:
        with csv_fajl.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as fajl:

            csv_olvaso = csv.reader(fajl)

            for sor in csv_olvaso:
                if len(sor) < 2:
                    continue

                if sor[0] not in UGYLET_SZEKCIOK:
                    continue

                if (
                    sor[1] == "Header"
                    and "DataDiscriminator" in sor
                ):
                    ugylet_szekcio_megtalalva = True
                    fejlec = sor[2:]
                    continue

                if (
                    sor[1] != "Data"
                    or fejlec is None
                ):
                    continue

                ertekek = sor[2:]

                nyers_rekord = dict(
                    zip(
                        fejlec,
                        ertekek,
                    )
                )

                if (
                    nyers_rekord.get(
                        "DataDiscriminator"
                    )
                    != "Order"
                ):
                    continue

                rekord = {}

                for eredeti_nev, ertek in nyers_rekord.items():
                    if eredeti_nev in OSZLOP_NEVEK:
                        uj_nev = OSZLOP_NEVEK[
                            eredeti_nev
                        ]

                        rekord[uj_nev] = (
                            ertek.strip()
                        )

                eszkoz_kategoria = rekord.get(
                    "eszkoz_kategoria"
                )

                # Devizaváltások és más eszközök
                # kiszűrése az oszlopellenőrzés előtt.
                if (
                    eszkoz_kategoria
                    not in RESZVENY_KATEGORIAK
                ):
                    continue

                hianyzo_oszlopok = (
                    KOTELEZO_OSZLOPOK
                    - set(rekord.keys())
                )

                if hianyzo_oszlopok:
                    raise IBKRImportHiba(
                        "A CSV részvényügyleteiből "
                        "kötelező oszlopok hiányoznak: "
                        + ", ".join(
                            sorted(
                                hianyzo_oszlopok
                            )
                        )
                    )

                ticker = rekord["ticker"]

                if not ticker:
                    raise IBKRImportHiba(
                        "Az egyik tranzakciónál "
                        "hiányzik a ticker."
                    )

                elojeles_mennyiseg = (
                    szam_atalakitasa(
                        rekord[
                            "elojeles_mennyiseg"
                        ],
                        "mennyiség",
                        ticker,
                    )
                )

                if elojeles_mennyiseg == 0:
                    continue

                tranzakcio = {
                    "datum": rekord["datum"],
                    "ticker": ticker,
                    "irany": (
                        "BUY"
                        if elojeles_mennyiseg > 0
                        else "SELL"
                    ),
                    "mennyiseg": abs(
                        elojeles_mennyiseg
                    ),
                    "elojeles_mennyiseg": (
                        elojeles_mennyiseg
                    ),
                    "ar": szam_atalakitasa(
                        rekord["ar"],
                        "ügyleti ár",
                        ticker,
                    ),
                    "jutalek": szam_atalakitasa(
                        rekord["jutalek"],
                        "jutalék",
                        ticker,
                        alapertelmezett=0.0,
                    ),
                    "deviza": rekord["deviza"],
                    "realizalt_pl": (
                        szam_atalakitasa(
                            rekord[
                                "realizalt_pl"
                            ],
                            "realizált P/L",
                            ticker,
                            alapertelmezett=0.0,
                        )
                    ),
                }

                tranzakciok.append(
                    tranzakcio
                )

    except UnicodeDecodeError as hiba:
        raise IBKRImportHiba(
            "A CSV karakterkódolása nem megfelelő. "
            "IBKR-ből közvetlenül exportált "
            "UTF-8 CSV szükséges."
        ) from hiba

    except csv.Error as hiba:
        raise IBKRImportHiba(
            "A CSV szerkezete hibás vagy sérült."
        ) from hiba

    if not ugylet_szekcio_megtalalva:
        raise IBKRImportHiba(
            "Ez nem támogatott IBKR "
            "Tevékenységkimutatás. "
            "Nem található benne az "
            "Ügyletek vagy Trades szekció."
        )

    # A kimutatás megfelelő, de nem tartalmaz
    # részvény- vagy ETF-tranzakciókat.
    if not tranzakciok:
        return pd.DataFrame(
            columns=KIMENETI_OSZLOPOK
        )

    tranzakciok_df = pd.DataFrame(
        tranzakciok
    )

    tranzakciok_df["datum"] = pd.to_datetime(
        tranzakciok_df["datum"],
        errors="coerce",
    )

    hibas_datumok = (
        tranzakciok_df["datum"].isna()
    )

    if hibas_datumok.any():
        hibas_ticker = tranzakciok_df.loc[
            hibas_datumok,
            "ticker",
        ].iloc[0]

        raise IBKRImportHiba(
            "Hibás vagy nem felismerhető dátum "
            f"a(z) {hibas_ticker} "
            "instrumentumnál."
        )

    tranzakciok_df = (
        tranzakciok_df
        .sort_values("datum")
        .reset_index(drop=True)
    )

    return tranzakciok_df[
        KIMENETI_OSZLOPOK
    ]


# --------------------------------------------------
# KÖZVETLEN TESZTELÉS
# --------------------------------------------------

if __name__ == "__main__":
    argumentumok = argparse.ArgumentParser(
        description=(
            "Magyar vagy angol IBKR Activity "
            "Statement CSV feldolgozása"
        )
    )

    argumentumok.add_argument(
        "csv_utvonal",
        help=(
            "Az IBKR CSV-fájl elérési útja"
        ),
    )

    beallitasok = argumentumok.parse_args()

    idoszak = kimutatas_idoszak_lekerese(
        beallitasok.csv_utvonal
    )

    tranzakciok_df = (
        ibkr_tranzakciok_betoltese(
            beallitasok.csv_utvonal
        )
    )

    print(
        f"Vizsgált időszak: {idoszak}"
    )

    print()

    if tranzakciok_df.empty:
        print(
            "A kimutatás nem tartalmaz "
            "részvény- vagy ETF-tranzakciót."
        )

    else:
        print(
            tranzakciok_df.head(10)
        )

        print()

        print(
            f"Feldolgozott tranzakciók száma: "
            f"{len(tranzakciok_df)}"
        )