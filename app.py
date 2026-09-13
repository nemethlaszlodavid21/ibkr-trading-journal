import tempfile
from html import escape
from pathlib import Path

import plotly.express as px
import streamlit as st

from ibkr_parser import (
    ibkr_tranzakciok_betoltese,
    kimutatas_idoszak_lekerese,
)
from metrics import teljesitmeny_mutatok_szamitasa
from position_engine import poziciok_rekonstrualasa
from trade_engine import lezart_tradek_letrehozasa


st.set_page_config(
    page_title="IBKR Trading Journal",
    page_icon="📈",
    layout="wide",
)


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
    margin-bottom: 1.4rem;
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

.period-card {
    padding: 0.85rem 1rem;
    margin-bottom: 1.3rem;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    background: #eff6ff;
    color: #1e3a5f;
    font-size: 0.92rem;
}

.period-label {
    margin-right: 0.35rem;
    color: #64748b;
    font-weight: 600;
}

.period-value {
    color: #1e3a5f;
    font-weight: 700;
}

.explanation-box {
    padding: 0.9rem 1rem;
    margin-bottom: 1.2rem;
    border-left: 4px solid #2563eb;
    border-radius: 8px;
    background: #ffffff;
    color: #475569;
    font-size: 0.9rem;
}

div[data-testid="stMetric"] {
    min-height: 112px;
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

button[data-baseweb="tab"] {
    font-size: 0.95rem;
    font-weight: 650;
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


@st.cache_data
def adatok_betoltese(csv_tartalom):
    with tempfile.TemporaryDirectory() as ideiglenes_mappa:
        csv_utvonal = Path(ideiglenes_mappa) / "ibkr_export.csv"
        csv_utvonal.write_bytes(csv_tartalom)

        kimutatas_idoszak = kimutatas_idoszak_lekerese(
            csv_utvonal
        )

        tranzakciok = ibkr_tranzakciok_betoltese(
            csv_utvonal
        )

        lezaro_tranzakciok = lezart_tradek_letrehozasa(
            tranzakciok
        )

        (
            lezart_poziciok,
            nyitott_poziciok,
        ) = poziciok_rekonstrualasa(
            tranzakciok
        )

    return (
        tranzakciok,
        lezaro_tranzakciok,
        lezart_poziciok,
        nyitott_poziciok,
        kimutatas_idoszak,
    )


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


st.sidebar.header("📂 Adatimport")

st.sidebar.caption(
    "Tölts fel egy magyar vagy angol "
    "IBKR Activity Statement CSV-kimutatást."
)

feltoltott_fajl = st.sidebar.file_uploader(
    "IBKR CSV kiválasztása",
    type=["csv"],
)

if feltoltott_fajl is None:
    st.info(
        "A dashboard megjelenítéséhez tölts fel "
        "egy IBKR Activity Statement CSV-fájlt."
    )
    st.stop()


try:
    (
        tranzakciok_df,
        lezaro_tranzakciok_df,
        lezart_poziciok_df,
        nyitott_poziciok_df,
        kimutatas_idoszak,
    ) = adatok_betoltese(
        feltoltott_fajl.getvalue()
    )

except Exception as hiba:
    st.error(
        f"A CSV-fájl feldolgozása nem sikerült: "
        f"{hiba}"
    )
    st.stop()


if tranzakciok_df.empty:
    st.warning(
        "A kimutatás nem tartalmaz feldolgozható "
        "részvény- vagy ETF-tranzakciót."
    )
    st.stop()


if lezaro_tranzakciok_df.empty:
    st.warning(
        "A kimutatás tartalmaz tranzakciókat, "
        "de nincs benne lezáró eladás."
    )
    st.stop()


st.sidebar.success(
    f"{len(tranzakciok_df)} végrehajtás betöltve"
)

st.sidebar.caption(
    f"Fájl: {feltoltott_fajl.name}"
)

st.sidebar.markdown("### Vizsgált időszak")

st.sidebar.info(
    kimutatas_idoszak
)


biztonsagos_idoszak = escape(
    str(kimutatas_idoszak)
)

st.markdown(
    f"""
<div class="period-card">
<span class="period-label">Vizsgált időszak:</span>
<span class="period-value">{biztonsagos_idoszak}</span>
</div>
    """,
    unsafe_allow_html=True,
)


st.subheader("Adatösszefoglaló")

elso, masodik, harmadik, negyedik = st.columns(4)

elso.metric(
    "Végrehajtások",
    len(tranzakciok_df),
    help="Minden IBKR BUY és SELL végrehajtás.",
)

masodik.metric(
    "Kiszállások",
    len(lezaro_tranzakciok_df),
    help="Minden különálló SELL tranzakció.",
)

harmadik.metric(
    "Lezárt pozíciók",
    len(lezart_poziciok_df),
    help=(
        "A részleges kiszállásokat összevonó "
        "teljes pozícióciklusok."
    ),
)

negyedik.metric(
    "Nyitott pozíciók",
    len(nyitott_poziciok_df),
    help=(
        "A kimutatási időszak végén még "
        "nyitva lévő pozíciók."
    ),
)


st.markdown(
    """
<div class="explanation-box">
Egy pozíció több vételből és több részleges kiszállásból is állhat.
Ezért a végrehajtások, kiszállások és lezárt pozíciók száma eltérhet.
</div>
    """,
    unsafe_allow_html=True,
)


valaszthato_devizak = sorted(
    lezaro_tranzakciok_df["deviza"].unique()
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


kiszallas_tab, pozicio_tab = st.tabs(
    [
        "Realizált teljesítmény",
        "Pozíciók és holding",
    ]
)


# ==================================================
# REALIZÁLT TELJESÍTMÉNY
# ==================================================

with kiszallas_tab:
    st.caption(
        "Az egyes eladási tranzakciók realizált "
        "eredménye és időbeli alakulása."
    )

    (
        kiszallasi_alap_mutatok,
        deviza_mutatok_df,
    ) = teljesitmeny_mutatok_szamitasa(
        lezaro_tranzakciok_df
    )

    szurt_kiszallasok_df = lezaro_tranzakciok_df[
        lezaro_tranzakciok_df["deviza"]
        == kivalasztott_deviza
    ].copy()

    deviza_sor = deviza_mutatok_df[
        deviza_mutatok_df["deviza"]
        == kivalasztott_deviza
    ].iloc[0]

    szurt_kiszallasok_df = (
        szurt_kiszallasok_df
        .sort_values("zaras_datuma")
        .reset_index(drop=True)
    )

    kiszallasok_szama = len(
        szurt_kiszallasok_df
    )

    nyereseges_kiszallasok = len(
        szurt_kiszallasok_df[
            szurt_kiszallasok_df["realizalt_pl"] > 0
        ]
    )

    veszteseges_kiszallasok = len(
        szurt_kiszallasok_df[
            szurt_kiszallasok_df["realizalt_pl"] < 0
        ]
    )

    kiszallasi_win_rate = (
        nyereseges_kiszallasok
        / kiszallasok_szama
        * 100
        if kiszallasok_szama > 0
        else 0
    )

    profit_factor = deviza_sor["profit_factor"]

    if profit_factor == float("inf"):
        profit_factor_szoveg = "N/A"
    else:
        profit_factor_szoveg = (
            f"{profit_factor:.2f}"
        )

    elso, masodik, harmadik, negyedik = st.columns(4)

    elso.metric(
        "Realizált P/L",
        (
            f"{deviza_sor['realizalt_pl']:,.2f} "
            f"{kivalasztott_deviza}"
        ),
    )

    masodik.metric(
        "Kiszállási win rate",
        f"{kiszallasi_win_rate:.2f}%",
    )

    harmadik.metric(
        "Profit factor",
        profit_factor_szoveg,
    )

    negyedik.metric(
        "Veszteséges kiszállások",
        veszteseges_kiszallasok,
    )


    szurt_kiszallasok_df["kumulalt_pl"] = (
        szurt_kiszallasok_df[
            "realizalt_pl"
        ].cumsum()
    )

    szurt_kiszallasok_df["korabbi_csucs"] = (
        szurt_kiszallasok_df[
            "kumulalt_pl"
        ]
        .cummax()
        .clip(lower=0)
    )

    szurt_kiszallasok_df["drawdown"] = (
        szurt_kiszallasok_df["kumulalt_pl"]
        - szurt_kiszallasok_df["korabbi_csucs"]
    )

    maximum_drawdown = abs(
        szurt_kiszallasok_df["drawdown"].min()
    )

    aktualis_drawdown = abs(
        szurt_kiszallasok_df[
            "drawdown"
        ].iloc[-1]
    )

    elso, masodik, harmadik, negyedik = st.columns(4)

    elso.metric(
        "Nyereséges kiszállások",
        nyereseges_kiszallasok,
    )

    masodik.metric(
        "Legjobb kiszállás",
        (
            f"{deviza_sor['legjobb_trade']:,.2f} "
            f"{kivalasztott_deviza}"
        ),
    )

    harmadik.metric(
        "Legrosszabb kiszállás",
        (
            f"{deviza_sor['legrosszabb_trade']:,.2f} "
            f"{kivalasztott_deviza}"
        ),
    )

    negyedik.metric(
        "Maximum drawdown",
        (
            f"-{maximum_drawdown:,.2f} "
            f"{kivalasztott_deviza}"
        ),
        help=(
            "A kumulált realizált P/L korábbi "
            "csúcsához képest mért legnagyobb visszaesés."
        ),
    )


    bal_grafikon, jobb_grafikon = st.columns(
        [1.55, 1]
    )

    with bal_grafikon:
        kumulalt_grafikon = px.line(
            szurt_kiszallasok_df,
            x="zaras_datuma",
            y="kumulalt_pl",
            markers=True,
            title="Kumulált realizált P/L",
            labels={
                "zaras_datuma": "Kiszállás dátuma",
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
            szurt_kiszallasok_df,
            x="zaras_datuma",
            y="drawdown",
            title="Drawdown",
            labels={
                "zaras_datuma": "Kiszállás dátuma",
                "drawdown": (
                    f"Drawdown "
                    f"({kivalasztott_deviza})"
                ),
            },
        )

        drawdown_grafikon.update_traces(
            line_color="#dc2626",
            fillcolor=(
                "rgba(220, 38, 38, 0.18)"
            ),
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


    szurt_kiszallasok_df["honap"] = (
        szurt_kiszallasok_df[
            "zaras_datuma"
        ]
        .dt.to_period("M")
        .astype(str)
    )

    havi_eredmeny_df = (
        szurt_kiszallasok_df
        .groupby(
            "honap",
            as_index=False,
        )["realizalt_pl"]
        .sum()
    )

    havi_eredmeny_df["eredmeny_tipusa"] = (
        havi_eredmeny_df[
            "realizalt_pl"
        ].apply(
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
                    f"P/L "
                    f"({kivalasztott_deviza})"
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
                        (
                            f"P/L "
                            f"({kivalasztott_deviza})"
                        ),
                        format="%.2f",
                    )
                ),
            },
            use_container_width=True,
            hide_index=True,
            height=315,
        )


    st.subheader("Instrumentumok")

    instrumentum_eredmeny = (
        szurt_kiszallasok_df
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


    st.subheader("Kiszállási tranzakciók")

    st.dataframe(
        szurt_kiszallasok_df[
            [
                "trade_id",
                "ticker",
                "zaras_datuma",
                "mennyiseg",
                "zarasi_ar",
                "realizalt_pl",
                "eredmeny",
            ]
        ],
        column_config={
            "trade_id": "Kiszállás ID",
            "ticker": "Ticker",
            "zaras_datuma": "Kiszállás dátuma",
            "mennyiseg": (
                st.column_config.NumberColumn(
                    "Mennyiség",
                    format="%.4f",
                )
            ),
            "zarasi_ar": (
                st.column_config.NumberColumn(
                    "Eladási ár",
                    format="%.4f",
                )
            ),
            "realizalt_pl": (
                st.column_config.NumberColumn(
                    (
                        f"P/L "
                        f"({kivalasztott_deviza})"
                    ),
                    format="%.2f",
                )
            ),
            "eredmeny": "Eredmény",
        },
        use_container_width=True,
        hide_index=True,
    )


# ==================================================
# POZÍCIÓK ÉS HOLDING
# ==================================================

with pozicio_tab:
    st.caption(
        "A több vételből és részleges kiszállásból "
        "álló teljes pozícióciklusok elemzése."
    )

    szurt_poziciok_df = lezart_poziciok_df[
        lezart_poziciok_df["deviza"]
        == kivalasztott_deviza
    ].copy()

    szurt_nyitott_df = nyitott_poziciok_df[
        nyitott_poziciok_df["deviza"]
        == kivalasztott_deviza
    ].copy()

    poziciok_szama = len(
        szurt_poziciok_df
    )

    nyereseges_poziciok = len(
        szurt_poziciok_df[
            szurt_poziciok_df["realizalt_pl"] > 0
        ]
    )

    veszteseges_poziciok = len(
        szurt_poziciok_df[
            szurt_poziciok_df["realizalt_pl"] < 0
        ]
    )

    pozicio_win_rate = (
        nyereseges_poziciok
        / poziciok_szama
        * 100
        if poziciok_szama > 0
        else 0
    )

    holding_adatok = szurt_poziciok_df[
        "holding_napok"
    ].dropna()

    if holding_adatok.empty:
        holding_szoveg = "Nincs adat"
    else:
        holding_szoveg = (
            f"{holding_adatok.mean():.1f} nap"
        )

    hianyos_elozmenyek = len(
        szurt_poziciok_df[
            szurt_poziciok_df["adatminoseg"]
            != "Teljes előzmény"
        ]
    )

    elso, masodik, harmadik, negyedik = st.columns(4)

    elso.metric(
        "Lezárt pozíciók",
        poziciok_szama,
    )

    masodik.metric(
        "Pozíció win rate",
        f"{pozicio_win_rate:.2f}%",
    )

    harmadik.metric(
        "Átlagos holding",
        holding_szoveg,
    )

    negyedik.metric(
        "Hiányos előzmények",
        hianyos_elozmenyek,
    )

    elso, masodik, harmadik = st.columns(3)

    elso.metric(
        "Nyereséges pozíciók",
        nyereseges_poziciok,
    )

    masodik.metric(
        "Veszteséges pozíciók",
        veszteseges_poziciok,
    )

    harmadik.metric(
        "Nyitott pozíciók",
        len(szurt_nyitott_df),
    )


    st.subheader("Lezárt pozíciók")

    if szurt_poziciok_df.empty:
        st.info(
            "Ebben a devizában nincs "
            "lezárt pozíció."
        )

    else:
        st.dataframe(
            szurt_poziciok_df[
                [
                    "trade_id",
                    "ticker",
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
            ],
            column_config={
                "trade_id": "Trade ID",
                "ticker": "Ticker",
                "nyitas_datuma": "Nyitás",
                "zaras_datuma": "Zárás",
                "mennyiseg": (
                    st.column_config.NumberColumn(
                        "Mennyiség",
                        format="%.4f",
                    )
                ),
                "atlagos_veteli_ar": (
                    st.column_config.NumberColumn(
                        "Átlagos vételi ár",
                        format="%.4f",
                    )
                ),
                "atlagos_eladasi_ar": (
                    st.column_config.NumberColumn(
                        "Átlagos eladási ár",
                        format="%.4f",
                    )
                ),
                "realizalt_pl": (
                    st.column_config.NumberColumn(
                        (
                            f"P/L "
                            f"({kivalasztott_deviza})"
                        ),
                        format="%.2f",
                    )
                ),
                "holding_napok": (
                    st.column_config.NumberColumn(
                        "Holding napok",
                        format="%.1f",
                    )
                ),
                "reszleges_kiszallasok": (
                    "Részleges kiszállások"
                ),
                "eredmeny": "Eredmény",
                "adatminoseg": "Adatminőség",
            },
            use_container_width=True,
            hide_index=True,
        )


    st.subheader("Nyitott pozíciók")

    if szurt_nyitott_df.empty:
        st.info(
            "Ebben a devizában nincs "
            "nyitott pozíció."
        )

    else:
        st.dataframe(
            szurt_nyitott_df,
            column_config={
                "ticker": "Ticker",
                "deviza": "Deviza",
                "nyitas_datuma": "Nyitás",
                "nyitott_mennyiseg": (
                    st.column_config.NumberColumn(
                        "Nyitott mennyiség",
                        format="%.4f",
                    )
                ),
                "atlagos_veteli_ar": (
                    st.column_config.NumberColumn(
                        "Átlagos vételi ár",
                        format="%.4f",
                    )
                ),
                "reszleges_kiszallasok": (
                    "Részleges kiszállások"
                ),
                "eddigi_realizalt_pl": (
                    st.column_config.NumberColumn(
                        "Eddigi realizált P/L",
                        format="%.2f",
                    )
                ),
                "statusz": "Státusz",
            },
            use_container_width=True,
            hide_index=True,
        )