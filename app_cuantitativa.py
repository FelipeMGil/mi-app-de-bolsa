import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Análisis Cuantitativo", layout="wide")

st.title("📊 Aplicación de Análisis Cuantitativo de Mercados")
st.caption("Herramienta fiable, comprensible y verificable. Sin predicciones ni garantías de beneficio.")

# Sidebar - Parámetros de entrada
st.sidebar.header("⚙️ Configuración del Análisis")
ticker = st.sidebar.text_input("Introduce el Ticker de Yahoo Finance (ej. AAPL, MSFT, ^IBEX):", value="AAPL")
start_date = st.sidebar.date_input("Fecha de inicio:", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Fecha de fin:", pd.to_datetime("today"))

estrategia = st.sidebar.selectbox(
    "Selecciona la Estrategia a evaluar:",
    [
        "Cruce de medias móviles 20/50 (Tendencia)",
        "Cruce de medias móviles 50/200 (Tendencia)",
        "Ruptura de máximos y mínimos (Ruptura)",
        "Momentum (Persistencia del movimiento)",
        "Reversión a la media (Bandas Bollinger)"
    ]
)

# Carga de datos
@st.cache_data
def load_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

data = load_data(ticker, start_date, end_date)

if data is None or len(data) == 0:
    st.error("No se han podido descargar datos para el ticker introducido. Por favor, verifica el símbolo en Yahoo Finance.")
else:
    df = data[['Close']].copy()
    df['Returns'] = df['Close'].pct_change()
    df['Signal'] = 0
    
    if "Cruce de medias móviles 20/50" in estrategia:
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['Signal'] = np.where(df['MA20'] > df['MA50'], 1, 0)
        
    elif "Cruce de medias móviles 50/200" in estrategia:
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        df['Signal'] = np.where(df['MA50'] > df['MA200'], 1, 0)
        
    elif "Ruptura de máximos y mínimos" in estrategia:
        df['Max20'] = df['Close'].shift(1).rolling(window=20).max()
        df['Min20'] = df['Close'].shift(1).rolling(window=20).min()
        sig = 0
        signals = []
        for i in range(len(df)):
            close = df['Close'].iloc[i]
            max_val = df['Max20'].iloc[i]
            min_val = df['Min20'].iloc[i]
            if pd.isna(max_val) or pd.isna(min_val):
                signals.append(0)
                continue
            if close > max_val:
                sig = 1
            elif close < min_val:
                sig = 0
            signals.append(sig)
        df['Signal'] = signals

    elif "Momentum" in estrategia:
        df['Momentum'] = df['Close'].pct_change(periods=12)
        df['Signal'] = np.where(df['Momentum'] > 0, 1, 0)
        
    elif "Reversión a la media" in estrategia:
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD20'] = df['Close'].rolling(window=20).std()
        df['Lower'] = df['MA20'] - (2 * df['STD20'])
        df['Upper'] = df['MA20'] + (2 * df['STD20'])
        sig = 0
        signals = []
        for i in range(len(df)):
            close = df['Close'].iloc[i]
            lower = df['Lower'].iloc[i]
            upper = df['Upper'].iloc[i]
            ma = df['MA20'].iloc[i]
            if pd.isna(lower) or pd.isna(upper):
                signals.append(0)
                continue
            if close < lower:
                sig = 1
            elif close > ma and sig == 1:
                sig = 0
            signals.append(sig)
        df['Signal'] = signals

    df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
    df['Cum_BuyHold'] = (1 + df['Returns'].fillna(0)).cumprod() - 1
    df['Cum_Strategy'] = (1 + df['Strategy_Returns'].fillna(0)).cumprod() - 1
    
    def calc_max_drawdown(cum_returns):
        wealth_index = 1 + cum_returns
        previous_peaks = wealth_index.cummax()
        drawdowns = (wealth_index - previous_peaks) / previous_peaks
        return drawdowns.min()

    max_dd_strat = calc_max_drawdown(df['Cum_Strategy'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Retorno Acumulado Estrategia", f"{df['Cum_Strategy'].iloc[-1]*100:.2f}%")
    with col2:
        st.metric("Retorno Acumulado Mercado (Buy & Hold)", f"{df['Cum_BuyHold'].iloc[-1]*100:.2f}%")
    with col3:
        st.metric("Peor Racha Estrategia (Max Drawdown)", f"{max_dd_strat*100:.2f}%")

    st.subheader("📈 Evolución Temporal del Rendimiento")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Cum_Strategy']*100, name="Estrategia", line=dict(color='emerald', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['Cum_BuyHold']*100, name="Mercado (Comprar y Mantener)", line=dict(color='gray', width=1.5, dash='dash')))
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Rendimiento Acumulado (%)",
        hovermode="x unified",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🔍 Verificación de Datos e Información")
    with st.expander("Ver tabla completa de cálculos históricos"):
        st.dataframe(df[['Close', 'Returns', 'Signal', 'Strategy_Returns', 'Cum_Strategy']])
        st.caption("Fuente de datos crudos: Yahoo Finance (yfinance). Cálculos matemáticos basados en retornos aritméticos diarios.")
