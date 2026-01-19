import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")
st.title("🏦 Dashboard Private Banker & Risk Manager")

st.markdown("Analisi multi-asset, rischio, benchmark e valutazione MIFID-style")

# =========================
# INPUT
# =========================
st.sidebar.header("📌 Configurazione")

tickers = st.sidebar.text_input(
    "Asset (separati da virgola)",
    value="AAPL,SPY,GLD"
)

benchmark = st.sidebar.selectbox(
    "Benchmark di riferimento",
    ["^GSPC", "MSCI World", "GLD"]
)

profilo = st.sidebar.selectbox(
    "Profilo di rischio cliente (MIFID)",
    ["Conservativo", "Bilanciato", "Dinamico"]
)

analyze = st.sidebar.button("🔍 Analizza")

# =========================
# FUNZIONI
# =========================
def compute_metrics(df):
    df["ret"] = df["Close"].pct_change()
    sharpe = (df["ret"].mean() * 252) / (df["ret"].std() * np.sqrt(252))
    max_dd = (df["Close"] / df["Close"].cummax() - 1).min()
    vol = df["ret"].rolling(30).std() * np.sqrt(252)
    return sharpe, max_dd, vol.iloc[-1]

def rating(sharpe, max_dd):
    score = 0
    if sharpe > 1: score += 2
    elif sharpe > 0.5: score += 1

    if max_dd > -0.20: score += 2
    elif max_dd > -0.35: score += 1

    return min(score + 1, 5)

# =========================
# ANALISI
# =========================
if analyze:
    asset_list = [t.strip().upper() for t in tickers.split(",")]

    prices = {}
    metrics = {}

    for t in asset_list:
        df = yf.download(t, period="2y")
        if not df.empty:
            prices[t] = df
            sharpe, max_dd, vol = compute_metrics(df)
            metrics[t] = {
                "Sharpe": sharpe,
                "MaxDD": max_dd,
                "Volatilità": vol,
                "Rating": rating(sharpe, max_dd)
            }

    # =========================
    # GRAFICO PREZZI
    # =========================
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        subplot_titles=("Prezzi Asset", "Benchmark")
    )

    for t, df in prices.items():
        fig.add_trace(
            go.Scatter(x=df.index, y=df["Close"], name=t),
            row=1, col=1
        )

    bench_df = yf.download("^GSPC", period="2y")
    fig.add_trace(
        go.Scatter(x=bench_df.index, y=bench_df["Close"],
                   name="Benchmark", line=dict(dash="dash")),
        row=2, col=1
    )

    fig.update_layout(height=800)
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # METRICHE
    # =========================
    st.subheader("📊 Metriche di Rischio e Performance")

    table = pd.DataFrame(metrics).T
    st.dataframe(table.style.format({
        "Sharpe": "{:.2f}",
        "MaxDD": "{:.1%}",
        "Volatilità": "{:.1%}",
        "Rating": "{:.0f}"
    }))

    # =========================
    # MIFID CHECK
    # =========================
    st.subheader("🏛️ Valutazione MIFID")

    for t, m in metrics.items():
        if profilo == "Conservativo" and m["MaxDD"] < -0.25:
            st.error(f"⚠️ {t}: NON coerente con profilo Conservativo")
        elif profilo == "Bilanciato" and m["MaxDD"] < -0.40:
            st.warning(f"⚠️ {t}: Rischio elevato per profilo Bilanciato")
        else:
            st.success(f"✅ {t}: Coerente con profilo {profilo}")

    st.markdown("### 🧠 Giudizio sintetico")
    st.info("Valutazione basata su volatilità, drawdown e rendimento corretto per il rischio.")
