from ibkr_parser import ibkr_tranzakciok_betoltese


def lezart_tradek_letrehozasa(tranzakciok_df):
    lezart_tradek_df = tranzakciok_df[
        tranzakciok_df["irany"] == "SELL"
    ].copy()

    lezart_tradek_df["eredmeny"] = lezart_tradek_df[
        "realizalt_pl"
    ].apply(
        lambda pl: "WIN"
        if pl > 0
        else "LOSS"
        if pl < 0
        else "BREAK EVEN"
    )

    lezart_tradek_df = lezart_tradek_df.rename(
        columns={
            "datum": "zaras_datuma",
            "ar": "zarasi_ar",
        }
    )

    lezart_tradek_df = lezart_tradek_df.reset_index(drop=True)

    lezart_tradek_df["trade_id"] = (
        lezart_tradek_df.index + 1
    )

    return lezart_tradek_df[
        [
            "trade_id",
            "ticker",
            "zaras_datuma",
            "mennyiseg",
            "zarasi_ar",
            "jutalek",
            "deviza",
            "realizalt_pl",
            "eredmeny",
        ]
    ]


if __name__ == "__main__":
    tranzakciok_df = ibkr_tranzakciok_betoltese(
        "data/ibkr_activity_statement.csv"
    )

    lezart_tradek_df = lezart_tradek_letrehozasa(
        tranzakciok_df
    )

    print(lezart_tradek_df)
    print()
    print(
        f"Lezáró tranzakciók száma: "
        f"{len(lezart_tradek_df)}"
    )