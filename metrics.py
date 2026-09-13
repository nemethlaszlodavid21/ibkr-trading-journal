import pandas as pd

from ibkr_parser import ibkr_tranzakciok_betoltese
from trade_engine import lezart_tradek_letrehozasa


def teljesitmeny_mutatok_szamitasa(lezart_tradek_df):
    trade_szam = len(lezart_tradek_df)

    nyero_tradek = lezart_tradek_df[
        lezart_tradek_df["realizalt_pl"] > 0
    ]

    vesztes_tradek = lezart_tradek_df[
        lezart_tradek_df["realizalt_pl"] < 0
    ]

    nyero_trade_szam = len(nyero_tradek)
    vesztes_trade_szam = len(vesztes_tradek)

    win_rate = (
        nyero_trade_szam / trade_szam * 100
        if trade_szam > 0
        else 0
    )

    alap_mutatok = {
        "trade_szam": trade_szam,
        "nyero_trade_szam": nyero_trade_szam,
        "vesztes_trade_szam": vesztes_trade_szam,
        "win_rate": win_rate,
    }

    deviza_mutatok = []

    for deviza, csoport in lezart_tradek_df.groupby("deviza"):
        nyereseges = csoport[csoport["realizalt_pl"] > 0]
        veszteseges = csoport[csoport["realizalt_pl"] < 0]

        brutto_nyereseg = nyereseges["realizalt_pl"].sum()
        brutto_veszteseg = abs(
            veszteseges["realizalt_pl"].sum()
        )

        profit_factor = (
            brutto_nyereseg / brutto_veszteseg
            if brutto_veszteseg > 0
            else float("inf")
        )

        deviza_mutatok.append(
            {
                "deviza": deviza,
                "realizalt_pl": csoport["realizalt_pl"].sum(),
                "atlagos_nyereseg": nyereseges[
                    "realizalt_pl"
                ].mean(),
                "atlagos_veszteseg": veszteseges[
                    "realizalt_pl"
                ].mean(),
                "profit_factor": profit_factor,
                "legjobb_trade": csoport["realizalt_pl"].max(),
                "legrosszabb_trade": csoport["realizalt_pl"].min(),
            }
        )

    deviza_mutatok_df = pd.DataFrame(deviza_mutatok)

    return alap_mutatok, deviza_mutatok_df


if __name__ == "__main__":
    tranzakciok_df = ibkr_tranzakciok_betoltese(
        "data/U23185815_20260101_20260911.csv"
    )

    lezart_tradek_df = lezart_tradek_letrehozasa(
        tranzakciok_df
    )

    alap_mutatok, deviza_mutatok_df = (
        teljesitmeny_mutatok_szamitasa(
            lezart_tradek_df
        )
    )

    print("TRADING TELJESÍTMÉNY")
    print("--------------------")
    print(f"Trade-ek száma: {alap_mutatok['trade_szam']}")
    print(
        f"Nyerő trade-ek: "
        f"{alap_mutatok['nyero_trade_szam']}"
    )
    print(
        f"Vesztes trade-ek: "
        f"{alap_mutatok['vesztes_trade_szam']}"
    )
    print(f"Win rate: {alap_mutatok['win_rate']:.2f}%")

    print()
    print("DEVIZÁNKÉNTI EREDMÉNY")
    print(deviza_mutatok_df)