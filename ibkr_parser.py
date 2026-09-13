import csv
from pathlib import Path

import pandas as pd


def kimutatas_idoszak_lekerese(csv_utvonal):
    csv_fajl = Path(csv_utvonal)

    with csv_fajl.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fajl:

        csv_olvaso = csv.reader(fajl)

        for sor in csv_olvaso:
            if (
                len(sor) >= 4
                and sor[0] == "Statement"
                and sor[1] == "Data"
                and sor[2] == "Period"
            ):
                return sor[3]

    return "Ismeretlen időszak"


def ibkr_tranzakciok_betoltese(csv_utvonal):
    csv_fajl = Path(csv_utvonal)
    tranzakciok = []

    with csv_fajl.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fajl:

        csv_olvaso = csv.reader(fajl)

        for sor in csv_olvaso:

            if (
                len(sor) >= 16
                and sor[0] == "Ügyletek"
                and sor[1] == "Data"
                and sor[2] == "Order"
                and sor[3] == "Részvények"
            ):
                elojeles_mennyiseg = float(sor[7])

                tranzakcio = {
                    "datum": sor[6],
                    "ticker": sor[5],
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
                    "ar": float(sor[8]),
                    "jutalek": float(sor[11]),
                    "deviza": sor[4],
                    "realizalt_pl": float(sor[13]),
                }

                tranzakciok.append(
                    tranzakcio
                )

    tranzakciok_df = pd.DataFrame(
        tranzakciok
    )

    if tranzakciok_df.empty:
        return tranzakciok_df

    tranzakciok_df["datum"] = pd.to_datetime(
        tranzakciok_df["datum"]
    )

    tranzakciok_df = (
        tranzakciok_df
        .sort_values("datum")
        .reset_index(drop=True)
    )

    return tranzakciok_df


if __name__ == "__main__":
    csv_utvonal = (
        "data/ibkr_activity_statement.csv"
    )

    kimutatas_idoszak = (
        kimutatas_idoszak_lekerese(
            csv_utvonal
        )
    )

    tranzakciok_df = (
        ibkr_tranzakciok_betoltese(
            csv_utvonal
        )
    )

    print(
        f"Vizsgált időszak: "
        f"{kimutatas_idoszak}"
    )

    print()

    print(
        tranzakciok_df.head(10)
    )

    print()

    print(
        f"Feldolgozott tranzakciók száma: "
        f"{len(tranzakciok_df)}"
    )