import tempfile
from pathlib import Path

import plotly.express as px
import streamlit as st

from ibkr_parser import ibkr_tranzakciok_betoltese
from metrics import teljesitmeny_mutatok_szamitasa
from trade_engine import lezart_tradek_letrehozasa


# --------------------------------------------------
# OLDALBEÁLLÍTÁS
# --------------------------------------------------

st.set_page_config(
    page_title="IBKR Trading Journal",
    page_icon="📈",
    layout="wide",
)


# --------------------------------------------------
# EGYEDI MEGJELENÉS
# --------------------------------------------------

st.markdown(
    """
<style>
.stApp {
    background-color: #f4f7fb;
    color: #172033;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.dashboard-header {
    padding: 1.5rem 1.7rem;
    margin-bottom: 1.5rem;
    border: 1px solid #dce3ed;
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        #ffffff 0%,
        #edf4ff 100%
    );
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.dashboard-title {
    margin: 0;
    color: #14213d;
    font-size: 2rem;
    font-weight: 750;
    letter-spacing: -0.03em;
}

.dashboard-subtitle {
    margin-top: 0.4rem;
    margin-bottom: 0;
    color: #64748b;
    font-size: 0.95rem;
}

.status-badge {
    display: inline-block;
    padding: 0.28rem 0.65rem;
    margin-bottom: 0.8rem;
    border: 1px solid #bfdbfe;
    border-radius: 999px;
    background: #eff6ff;
    color: #2563eb;
    font-size: 0.75rem;
    font-weight: 700;
}

div[data-testid="stMetric"] {
    min-height: 115px;
    padding: 1rem 1.1rem;
    border: 1px solid #dce3ed;
    border-radius: 14px;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

div[data-testid="stMetricLabel"] {
    color: #64748b;
}

div[data-testid="stMetricValue"] {
    color: #14213d;
}

div[data-testid="stSelectbox"] {
    max-width: 320px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #dce3ed;
    border-radius: 12px;
    overflow: hidden;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #dce3ed;
}

h1, h2, h3 {
    color: #14213d;
}

hr {
    border-color: #dce3ed;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}
</style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SEGÉDFÜGGVÉNYEK
# --------------------------------------------------

@st.cache_data
def adatok_betoltese(csv_tartalom):
    with tempfile.TemporaryDirectory() as ideiglenes_mappa:
        csv_utvonal = Path(ideiglenes_mappa) / "ibkr_export.csv"
        csv_utvonal.write_bytes(csv_tartalom)

        tranzakciok = ibkr_tranzakciok_betoltese(
            csv_utvonal
        )

        lezart_tradek = lezart_tradek_letrehozasa(
            tranzakciok
        )

    return tranzakciok, lezart_tradek


def grafikon_formazasa(grafikon, magassag=390):
    grafikon.update_layout(
        template="plotly_white",
        height=magassag,
        margin=dict(
            l=25,
            r=25,
            t=60,
            b=30,
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            color="#334155",
            family="Arial",
        ),
        title_font=dict(
            color="#14213d",
            size=17,
        ),
        xaxis=dict(
            gridcolor="#e8edf4",
            linecolor="#cbd5e1",
            zerolinecolor="#94a3b8",
        ),
        yaxis=dict(
            gridcolor="#e8edf4",
            linecolor="#cbd5e1",
            zerolinecolor="#94a3b8",
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            font_color="#14213d",
            bordercolor="#cbd5e1",
        ),
    )

    return grafikon


# --------------------------------------------------
# FEJLÉC
# --------------------------------------------------

st.markdown(
    """
<div class="dashboard-header">
<div class="status-badge">TRADE ANALYTICS</div>
<h1 class="dashboard-title">IBKR Trading Journal</h1>
<p class="dashboard-subtitle">Interaktív kereskedési teljesítmény- és kockázatelemző dashboard</p>
</div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# CSV-FELTÖLTÉS
# --------------------------------------------------

st.sidebar.header("📂 Adatimport")

st.sidebar.caption(
    "Tölts fel egy IBKR Activity Statement "
    "CSV-kimutatást."
)

feltoltott_fajl = st.sidebar.file_uploader(
    "IBKR CSV kiválasztása",
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
    f"{len(tranzakciok_df)} tranzakció betöltve"
)

st.sidebar.caption(
    f"Fájl: {feltoltott_fajl.name}"
)


if lezart_tradek_df.empty:
    st.warning(
        "A feltöltött kimutatásban nincs "
        "lezáró tranzakció."
    )
    st.stop()


# --------------------------------------------------
# TELJESÍTMÉNYMUTATÓK
# --------------------------------------------------

alap_mutatok, deviza_mutatok_df = (
    teljesitmeny_mutatok_szamitasa(
        lezart_tradek_df
    )
)


st.subheader("Áttekintés")

elso, masodik, harmadik, negyedik = st.columns(4)

elso.metric(
    "Lezáró tranzakciók",
    alap_mutatok["trade_szam"],
)

masodik.metric(
    "Win rate",
    f"{alap_mutatok['win_rate']:.2f}%",
)

harmadik.metric(
    "Nyerő lezárások",
    alap_mutatok["nyero_trade_szam"],
)

negyedik.metric(
    "Vesztes lezárások",
    alap_mutatok["vesztes_trade_szam"],
)


# --------------------------------------------------
# DEVIZAVÁLASZTÁS
# --------------------------------------------------

st.divider()

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
# KUMULÁLT P/L ÉS DRAWDOWN
# --------------------------------------------------

szurt_tradek_df = (
    szurt_tradek_df
    .sort_values("zaras_datuma")
    .reset_index(drop=True)
)

szurt_tradek_df["kumulalt_pl"] = (
    szurt_tradek_df["realizalt_pl"].cumsum()
)

szurt_tradek_df["korabbi_csucs"] = (
    szurt_tradek_df["kumulalt_pl"]
    .cummax()
    .clip(lower=0)
)

szurt_tradek_df["drawdown"] = (
    szurt_tradek_df["kumulalt_pl"]
    - szurt_tradek_df["korabbi_csucs"]
)

maximum_drawdown = abs(
    szurt_tradek_df["drawdown"].min()
)

aktualis_drawdown = abs(
    szurt_tradek_df["drawdown"].iloc[-1]
)


# --------------------------------------------------
# DEVIZAMUTATÓK
# --------------------------------------------------

st.subheader(
    f"{kivalasztott_deviza} teljesítmény"
)

elso, masodik, harmadik, negyedik = st.columns(4)

elso.metric(
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


masodik.metric(
    "Profit factor",
    profit_factor_szoveg,
)

harmadik.metric(
    "Legjobb lezárás",
    (
        f"{deviza_sor['legjobb_trade']:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)

negyedik.metric(
    "Legrosszabb lezárás",
    (
        f"{deviza_sor['legrosszabb_trade']:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)


otodik, hatodik = st.columns(2)

otodik.metric(
    "Maximum drawdown",
    (
        f"-{maximum_drawdown:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)

hatodik.metric(
    "Aktuális drawdown",
    (
        f"-{aktualis_drawdown:,.2f} "
        f"{kivalasztott_deviza}"
    ),
)


# --------------------------------------------------
# KUMULÁLT P/L ÉS DRAWDOWN GRAFIKON
# --------------------------------------------------

bal_grafikon, jobb_grafikon = st.columns(
    [1.55, 1]
)


with bal_grafikon:
    kumulalt_grafikon = px.line(
        szurt_tradek_df,
        x="zaras_datuma",
        y="kumulalt_pl",
        markers=True,
        title="Kumulált realizált P/L",
        labels={
            "zaras_datuma": "Zárás dátuma",
            "kumulalt_pl": (
                f"P/L ({kivalasztott_deviza})"
            ),
        },
    )

    kumulalt_grafikon.update_traces(
        line_color="#16a34a",
        line_width=3,
        marker_size=7,
    )

    kumulalt_grafikon.update_layout(
        hovermode="x unified"
    )

    kumulalt_grafikon.add_hline(
        y=0,
        line_dash="dash",
        line_color="#94a3b8",
    )

    grafikon_formazasa(
        kumulalt_grafikon,
        magassag=400,
    )

    st.plotly_chart(
        kumulalt_grafikon,
        use_container_width=True,
    )


with jobb_grafikon:
    drawdown_grafikon = px.area(
        szurt_tradek_df,
        x="zaras_datuma",
        y="drawdown",
        title="Drawdown",
        labels={
            "zaras_datuma": "Zárás dátuma",
            "drawdown": (
                f"Drawdown ({kivalasztott_deviza})"
            ),
        },
    )

    drawdown_grafikon.update_traces(
        line_color="#dc2626",
        fillcolor="rgba(220, 38, 38, 0.18)",
    )

    drawdown_grafikon.update_layout(
        hovermode="x unified"
    )

    drawdown_grafikon.add_hline(
        y=0,
        line_dash="dash",
        line_color="#94a3b8",
    )

    grafikon_formazasa(
        drawdown_grafikon,
        magassag=400,
    )

    st.plotly_chart(
        drawdown_grafikon,
        use_container_width=True,
    )


# --------------------------------------------------
# HAVI EREDMÉNY
# --------------------------------------------------

szurt_tradek_df["honap"] = (
    szurt_tradek_df["zaras_datuma"]
    .dt.to_period("M")
    .astype(str)
)

havi_eredmeny_df = (
    szurt_tradek_df
    .groupby(
        "honap",
        as_index=False,
    )["realizalt_pl"]
    .sum()
)

havi_eredmeny_df["eredmeny_tipusa"] = (
    havi_eredmeny_df["realizalt_pl"].apply(
        lambda eredmeny: (
            "Nyereség"
            if eredmeny >= 0
            else "Veszteség"
        )
    )
)


st.subheader("Havi teljesítmény")

havi_bal, havi_jobb = st.columns(
    [1.65, 1]
)


with havi_bal:
    havi_grafikon = px.bar(
        havi_eredmeny_df,
        x="honap",
        y="realizalt_pl",
        color="eredmeny_tipusa",
        color_discrete_map={
            "Nyereség": "#16a34a",
            "Veszteség": "#dc2626",
        },
        text_auto=".2f",
        title="Havi realizált P/L",
        labels={
            "honap": "Hónap",
            "realizalt_pl": (
                f"P/L ({kivalasztott_deviza})"
            ),
            "eredmeny_tipusa": "Eredmény",
        },
    )

    havi_grafikon.update_layout(
        showlegend=False
    )

    havi_grafikon.update_traces(
        textposition="outside"
    )

    grafikon_formazasa(
        havi_grafikon,
        magassag=350,
    )

    st.plotly_chart(
        havi_grafikon,
        use_container_width=True,
    )


with havi_jobb:
    st.caption("Havi bontás")

    st.dataframe(
        havi_eredmeny_df[
            [
                "honap",
                "realizalt_pl",
            ]
        ],
        column_config={
            "honap": "Hónap",
            "realizalt_pl": (
                st.column_config.NumberColumn(
                    f"P/L ({kivalasztott_deviza})",
                    format="%.2f",
                )
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=315,
    )


# --------------------------------------------------
# INSTRUMENTUMONKÉNTI EREDMÉNY
# --------------------------------------------------

st.subheader("Instrumentumok")

instrumentum_eredmeny = (
    szurt_tradek_df
    .groupby(
        "ticker",
        as_index=False,
    )["realizalt_pl"]
    .sum()
    .sort_values(
        "realizalt_pl",
        ascending=True,
    )
)


instrumentum_grafikon = px.bar(
    instrumentum_eredmeny,
    x="realizalt_pl",
    y="ticker",
    orientation="h",
    color="realizalt_pl",
    color_continuous_scale=[
        "#dc2626",
        "#f1f5f9",
        "#16a34a",
    ],
    title="Instrumentumonkénti realizált P/L",
    labels={
        "ticker": "Instrumentum",
        "realizalt_pl": (
            f"P/L ({kivalasztott_deviza})"
        ),
    },
)

instrumentum_grafikon.update_layout(
    coloraxis_showscale=False
)

grafikon_formazasa(
    instrumentum_grafikon,
    magassag=420,
)

st.plotly_chart(
    instrumentum_grafikon,
    use_container_width=True,
)


# --------------------------------------------------
# TRANZAKCIÓS TÁBLÁZAT
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
    column_config={
        "trade_id": "Trade ID",
        "ticker": "Ticker",
        "zaras_datuma": "Zárás dátuma",
        "mennyiseg": (
            st.column_config.NumberColumn(
                "Mennyiség",
                format="%.4f",
            )
        ),
        "zarasi_ar": (
            st.column_config.NumberColumn(
                "Zárási ár",
                format="%.4f",
            )
        ),
        "realizalt_pl": (
            st.column_config.NumberColumn(
                f"P/L ({kivalasztott_deviza})",
                format="%.2f",
            )
        ),
        "eredmeny": "Eredmény",
    },
    use_container_width=True,
    hide_index=True,
)