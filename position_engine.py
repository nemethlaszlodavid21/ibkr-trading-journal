import argparse

import pandas as pd

from ibkr_parser import ibkr_tranzakciok_betoltese


TURES = 0.00000001


LEZART_OSZLOPOK = [
    "trade_id",
    "ticker",
    "deviza",
    "nyitas_datuma",
    "zaras_datuma",
    "mennyiseg",
    "atlagos_veteli_ar",
    "atlagos_eladasi_ar",
    "realizalt_pl",
    "holding_napok",
    "reszleges_kiszallasok",
    "eredmeny",
    "adatminoseg",
]


NYITOTT_OSZLOPOK = [
    "ticker",
    "deviza",
    "nyitas_datuma",
    "nyitott_mennyiseg",
    "atlagos_veteli_ar",
    "reszleges_kiszallasok",
    "eddigi_realizalt_pl",
    "statusz",
]


def eredmeny_meghatarozasa(realizalt_pl):
    if realizalt_pl > 0:
        return "WIN"

    if realizalt_pl < 0:
        return "LOSS"

    return "BREAK EVEN"


def poziciok_rekonstrualasa(tranzakciok_df):
    lezart_tradek = []
    nyitott_poziciok = []

    rendezett_tranzakciok = (
        tranzakciok_df
        .sort_values("datum")
        .reset_index(drop=True)
    )

    csoportok = rendezett_tranzakciok.groupby(
        [
            "deviza",
            "ticker",
        ],
        sort=False,
    )

    for (
        deviza,
        ticker,
    ), ticker_tranzakciok in csoportok:

        pozicio_mennyiseg = 0.0
        nyitas_datuma = None

        osszes_veteli_mennyiseg = 0.0
        osszes_veteli_ertek = 0.0

        osszes_eladott_mennyiseg = 0.0
        osszes_eladasi_ertek = 0.0

        reszleges_kiszallasok = 0
        ciklus_realizalt_pl = 0.0

        ticker_tranzakciok = (
            ticker_tranzakciok
            .sort_values("datum")
            .reset_index(drop=True)
        )

        for _, tranzakcio in ticker_tranzakciok.iterrows():
            irany = tranzakcio["irany"]
            mennyiseg = float(
                tranzakcio["mennyiseg"]
            )
            ar = float(
                tranzakcio["ar"]
            )
            jutalek = float(
                tranzakcio["jutalek"]
            )
            datum = tranzakcio["datum"]
            realizalt_pl = float(
                tranzakcio["realizalt_pl"]
            )

            if irany == "BUY":
                if pozicio_mennyiseg <= TURES:
                    nyitas_datuma = datum

                    osszes_veteli_mennyiseg = 0.0
                    osszes_veteli_ertek = 0.0

                    osszes_eladott_mennyiseg = 0.0
                    osszes_eladasi_ertek = 0.0

                    reszleges_kiszallasok = 0
                    ciklus_realizalt_pl = 0.0

                pozicio_mennyiseg += mennyiseg

                osszes_veteli_mennyiseg += mennyiseg

                osszes_veteli_ertek += (
                    mennyiseg * ar
                    + abs(jutalek)
                )

                continue

            if irany != "SELL":
                continue

            # Nincs korábbi vétel a kimutatásban
            if pozicio_mennyiseg <= TURES:
                lezart_tradek.append(
                    {
                        "ticker": ticker,
                        "deviza": deviza,
                        "nyitas_datuma": pd.NaT,
                        "zaras_datuma": datum,
                        "mennyiseg": mennyiseg,
                        "atlagos_veteli_ar": pd.NA,
                        "atlagos_eladasi_ar": ar,
                        "realizalt_pl": realizalt_pl,
                        "holding_napok": pd.NA,
                        "reszleges_kiszallasok": 1,
                        "eredmeny": (
                            eredmeny_meghatarozasa(
                                realizalt_pl
                            )
                        ),
                        "adatminoseg": (
                            "Nyitás a vizsgált időszak előtt"
                        ),
                    }
                )

                continue

            # Többet adtunk el, mint amennyi vétel
            # a kimutatási időszakban látható
            if mennyiseg > pozicio_mennyiseg + TURES:
                lezart_tradek.append(
                    {
                        "ticker": ticker,
                        "deviza": deviza,
                        "nyitas_datuma": pd.NaT,
                        "zaras_datuma": datum,
                        "mennyiseg": mennyiseg,
                        "atlagos_veteli_ar": pd.NA,
                        "atlagos_eladasi_ar": ar,
                        "realizalt_pl": realizalt_pl,
                        "holding_napok": pd.NA,
                        "reszleges_kiszallasok": 1,
                        "eredmeny": (
                            eredmeny_meghatarozasa(
                                realizalt_pl
                            )
                        ),
                        "adatminoseg": (
                            "Részben a vizsgált időszak "
                            "előtt nyitott pozíció"
                        ),
                    }
                )

                pozicio_mennyiseg = 0.0
                nyitas_datuma = None

                osszes_veteli_mennyiseg = 0.0
                osszes_veteli_ertek = 0.0

                osszes_eladott_mennyiseg = 0.0
                osszes_eladasi_ertek = 0.0

                reszleges_kiszallasok = 0
                ciklus_realizalt_pl = 0.0

                continue

            pozicio_mennyiseg -= mennyiseg

            osszes_eladott_mennyiseg += mennyiseg
            osszes_eladasi_ertek += mennyiseg * ar

            reszleges_kiszallasok += 1
            ciklus_realizalt_pl += realizalt_pl

            # A pozíció teljesen lezárult
            if abs(pozicio_mennyiseg) <= TURES:
                pozicio_mennyiseg = 0.0

                atlagos_veteli_ar = (
                    osszes_veteli_ertek
                    / osszes_veteli_mennyiseg
                )

                atlagos_eladasi_ar = (
                    osszes_eladasi_ertek
                    / osszes_eladott_mennyiseg
                )

                holding_napok = (
                    datum - nyitas_datuma
                ).total_seconds() / 86400

                lezart_tradek.append(
                    {
                        "ticker": ticker,
                        "deviza": deviza,
                        "nyitas_datuma": nyitas_datuma,
                        "zaras_datuma": datum,
                        "mennyiseg": (
                            osszes_eladott_mennyiseg
                        ),
                        "atlagos_veteli_ar": (
                            atlagos_veteli_ar
                        ),
                        "atlagos_eladasi_ar": (
                            atlagos_eladasi_ar
                        ),
                        "realizalt_pl": (
                            ciklus_realizalt_pl
                        ),
                        "holding_napok": round(
                            holding_napok,
                            2,
                        ),
                        "reszleges_kiszallasok": (
                            reszleges_kiszallasok
                        ),
                        "eredmeny": (
                            eredmeny_meghatarozasa(
                                ciklus_realizalt_pl
                            )
                        ),
                        "adatminoseg": "Teljes előzmény",
                    }
                )

                nyitas_datuma = None

                osszes_veteli_mennyiseg = 0.0
                osszes_veteli_ertek = 0.0

                osszes_eladott_mennyiseg = 0.0
                osszes_eladasi_ertek = 0.0

                reszleges_kiszallasok = 0
                ciklus_realizalt_pl = 0.0

        # A kimutatás végén még nyitott pozíció
        if pozicio_mennyiseg > TURES:
            atlagos_veteli_ar = (
                osszes_veteli_ertek
                / osszes_veteli_mennyiseg
            )

            nyitott_poziciok.append(
                {
                    "ticker": ticker,
                    "deviza": deviza,
                    "nyitas_datuma": nyitas_datuma,
                    "nyitott_mennyiseg": (
                        pozicio_mennyiseg
                    ),
                    "atlagos_veteli_ar": (
                        atlagos_veteli_ar
                    ),
                    "reszleges_kiszallasok": (
                        reszleges_kiszallasok
                    ),
                    "eddigi_realizalt_pl": (
                        ciklus_realizalt_pl
                    ),
                    "statusz": "Nyitott",
                }
            )

    lezart_tradek_df = pd.DataFrame(
        lezart_tradek
    )

    nyitott_poziciok_df = pd.DataFrame(
        nyitott_poziciok
    )

    if lezart_tradek_df.empty:
        lezart_tradek_df = pd.DataFrame(
            columns=LEZART_OSZLOPOK
        )

    else:
        lezart_tradek_df = (
            lezart_tradek_df
            .sort_values("zaras_datuma")
            .reset_index(drop=True)
        )

        lezart_tradek_df["trade_id"] = (
            lezart_tradek_df.index + 1
        )

        lezart_tradek_df = lezart_tradek_df[
            LEZART_OSZLOPOK
        ]

    if nyitott_poziciok_df.empty:
        nyitott_poziciok_df = pd.DataFrame(
            columns=NYITOTT_OSZLOPOK
        )

    else:
        nyitott_poziciok_df = (
            nyitott_poziciok_df
            .sort_values("ticker")
            .reset_index(drop=True)
        )

        nyitott_poziciok_df = nyitott_poziciok_df[
            NYITOTT_OSZLOPOK
        ]

    return (
        lezart_tradek_df,
        nyitott_poziciok_df,
    )


if __name__ == "__main__":
    argumentumok = argparse.ArgumentParser(
        description=(
            "IBKR pozíciók rekonstruálása"
        )
    )

    argumentumok.add_argument(
        "csv_utvonal",
        help=(
            "Az IBKR Tevékenységkimutatás "
            "CSV-fájljának elérési útja"
        ),
    )

    beallitasok = argumentumok.parse_args()

    tranzakciok_df = ibkr_tranzakciok_betoltese(
        beallitasok.csv_utvonal
    )

    (
        lezart_tradek_df,
        nyitott_poziciok_df,
    ) = poziciok_rekonstrualasa(
        tranzakciok_df
    )

    print("LEZÁRT TRADE-EK")
    print("----------------")
    print(lezart_tradek_df)

    print()
    print(
        f"Lezárt trade-ek száma: "
        f"{len(lezart_tradek_df)}"
    )

    print()
    print("NYITOTT POZÍCIÓK")
    print("----------------")
    print(nyitott_poziciok_df)

    print()
    print(
        f"Nyitott pozíciók száma: "
        f"{len(nyitott_poziciok_df)}"
    )