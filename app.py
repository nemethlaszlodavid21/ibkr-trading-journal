import tempfile
from pathlib import Path

import plotly.express as px
import streamlit as st

from ibkr_parser import ibkr_tranzakciok_betoltese
from metrics import teljesitmeny_mutatok_szamitasa
from trade_engine import lezart_tradek_letrehozasa


st.set_page_config(
    page_title="IBKR Trading Journal",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def adatok_betoltese(csv_tartalom):
    with tempfile.TemporaryDirectory() as ideiglenes_mappa:
        csv_utvonal = (
            Path(ideiglenes_mappa) / "ibkr_export.csv"
        )

        csv_utvonal.write_bytes(csv_tartalom)

        tranzakciok = ibkr_tranzakciok_betoltese(
            csv_utvonal
        )

        lezart_tradek = lezart_tradek_letrehozasa(
            tranzakciok
        )

    return tranzakciok, lezart_tradek


st.title("📈 IBKR Trading Journal")

st.caption(
    "Saját IBKR kereskedési teljesítmény elemzése"
)


# --------------------------------------------------
# CSV-FELTÖLTÉS
# --------------------------------------------------

st.sidebar.header("Adatimport")

feltoltott_fajl = st.sidebar.file_uploader(
    "IBKR Tevékenységkimutatás feltöltése",
    type=["csv"],
)

if feltoltott_fajl is None:
    st.info(
        "A dashboard megjelenítéséhez tölts fel "
        "egy IBKR Tevékenységkimutatás CSV-fájlt."
    )

    st.stop()


try:
    tranzakciok_df, lezart_tradek_df = adatok_betoltese(
        feltoltott_fajl.getvalue()
    )

except Exception as hiba:
    st.error(
        "A CSV-fájl feldolgozása nem sikerült."
    )

    st.exception(hiba)
    st.stop()


st.sidebar.success(
    f"{len(tranzakciok_df)} tranzakció "
    "sikeresen betöltve."
)


# --------------------------------------------------
# TELJESÍTMÉNYMUTATÓK
# --------------------------------------------------

alap_mutatok, deviza_mutatok_df = (
    teljesitmeny_mutatok_szamitasa(
        lezart_tradek_df
    )
)


elso_oszlop, masodik_oszlop, harmadik_oszlop, negyedik_oszlop = (
    st.columns(4)
)

elso_oszlop.metric(
    "Lezáró tranzakciók",
    alap_mutatok["trade_szam"],
)

masodik_oszlop.metric(
    "Win rate",
    f"{alap_mutatok['win_rate']:.2f}%",
)

harmadik_oszlop.metric(
    "Nyerő trade-ek",
    alap_mutatok["nyero_trade_szam"],
)

negyedik_oszlop.metric(
    "Vesztes trade-ek",
    alap_mutatok["vesztes_trade_szam"],
)


st.divider()


# --------------------------------------------------
# DEVIZAVÁLASZTÁS
# --------------------------------------------------

valaszthato_devizak = sorted(
    lezart_tradek_df["deviza"].unique()
)

kivalasztott_deviza = st.selectbox(
    "Elemzés devizája",
    valaszthato_devizak,
    index=(
        valaszthato_devizak.index("USD")
        if "USD" in valaszthato_devizak
        else 0
    ),
)


szurt_tradek_df = lezart_tradek_df[
    lezart_tradek_df["deviza"] == kivalasztott_deviza
].copy()


deviza_sor = deviza_mutatok_df[
    deviza_mutatok_df["deviza"] == kivalasztott_deviza
].iloc[0]


# --------------------------------------------------
# DEVIZÁNKÉNTI MUTATÓK
# --------------------------------------------------

st.subheader(
    f"{kivalasztott_deviza} teljesítmény"
)

pl_oszlop, profit_oszlop, legjobb_oszlop, legrosszabb_oszlop = (
    st.columns(4)
)

pl_oszlop.metric(
    "Realizált P/L",
    (
        f"{deviza_sor['realizalt_pl']:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)


profit_factor = deviza_sor["profit_factor"]

if profit_factor == float("inf"):
    profit_factor_szoveg = "∞"
else:
    profit_factor_szoveg = f"{profit_factor:.2f}"

profit_oszlop.metric(
    "Profit factor",
    profit_factor_szoveg,
)


legjobb_oszlop.metric(
    "Legjobb lezárás",
    (
        f"{deviza_sor['legjobb_trade']:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)


legrosszabb_oszlop.metric(
    "Legrosszabb lezárás",
    (
        f"{deviza_sor['legrosszabb_trade']:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)


# --------------------------------------------------
# KUMULÁLT P/L
# --------------------------------------------------

szurt_tradek_df = szurt_tradek_df.sort_values(
    "zaras_datuma"
)

szurt_tradek_df["kumulalt_pl"] = szurt_tradek_df[
    "realizalt_pl"
].cumsum()


kumulalt_grafikon = px.line(
    szurt_tradek_df,
    x="zaras_datuma",
    y="kumulalt_pl",
    markers=True,
    title=(
        f"Kumulált realizált P/L – "
        f"{kivalasztott_deviza}"
    ),
    labels={
        "zaras_datuma": "Zárás dátuma",
        "kumulalt_pl": (
            f"Kumulált P/L "
            f"({kivalasztott_deviza})"
        ),
    },
)

kumulalt_grafikon.update_traces(
    line_color="#16a34a",
    line_width=3,
    marker_size=8,
)

kumulalt_grafikon.update_layout(
    hovermode="x unified"
)

st.plotly_chart(
    kumulalt_grafikon,
    use_container_width=True,
)


# --------------------------------------------------
# INSTRUMENTUMONKÉNTI EREDMÉNY
# --------------------------------------------------

instrumentum_eredmeny = (
    szurt_tradek_df
    .groupby(
        "ticker",
        as_index=False
    )["realizalt_pl"]
    .sum()
    .sort_values(
        "realizalt_pl",
        ascending=False
    )
)


instrumentum_grafikon = px.bar(
    instrumentum_eredmeny,
    x="ticker",
    y="realizalt_pl",
    color="realizalt_pl",
    color_continuous_scale=[
        "#dc2626",
        "#f8fafc",
        "#16a34a",
    ],
    title=(
        f"Instrumentumonkénti eredmény – "
        f"{kivalasztott_deviza}"
    ),
    labels={
        "ticker": "Instrumentum",
        "realizalt_pl": (
            f"Realizált P/L "
            f"({kivalasztott_deviza})"
        ),
    },
)

st.plotly_chart(
    instrumentum_grafikon,
    use_container_width=True,
)


# --------------------------------------------------
# LEZÁRT TRANZAKCIÓK TÁBLÁZATA
# --------------------------------------------------

st.subheader("Lezárt tranzakciók")

megjelenitendo_oszlopok = [
    "trade_id",
    "ticker",
    "zaras_datuma",
    "mennyiseg",
    "zarasi_ar",
    "realizalt_pl",
    "eredmeny",
]


st.dataframe(
    szurt_tradek_df[
        megjelenitendo_oszlopok
    ],
    use_container_width=True,
    hide_index=True,
)