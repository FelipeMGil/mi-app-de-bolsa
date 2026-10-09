import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Definir el activo (el IBEX 35)
ticker = "^IBEX" 

try:
    # progress=False evita que el servidor se quede colgado leyendo barras de carga
    data = yf.download(ticker, period="1mo", interval="1d", progress=False, timeout=15)
    
    if data is None or data.empty:
        print("Error: No se recibieron datos.")
        sys.exit(0)
        
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    df = data[['Close']].copy()

    # Calcular Medias Móviles de forma segura
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()

    # Últimos valores calculados (hoy)
    precio_hoy = float(df['Close'].iloc[-1])
    ma20_hoy = float(df['MA20'].iloc[-1])
    ma50_hoy = float(df['MA50'].iloc[-1])
    ma200_hoy = float(df['MA200'].iloc[-1])

    # Comprobar condiciones de tendencia
    cruce_20_50 = "ALZA (Alcista)" if ma20_hoy > ma50_hoy else "BAJA (Bajista)"
    cruce_50_200 = "ALZA (Alcista)" if ma50_hoy > ma200_hoy else "BAJA (Bajista)"

    # Redactar el informe diario
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M')
    informe = f"""# 🤖 Informe Automático Cuantitativo ({fecha_actual})
* **Activo Analizado:** {ticker}
* **Precio de Cierre de Hoy:** {precio_hoy:.2f}

## 📊 Estado de las Estrategias de Tendencia:
* **Cruce 20/50 (Corto/Medio plazo):** El mercado se encuentra en fase de **{cruce_20_50}**.
* **Cruce 50/200 (Largo plazo / Cruz Dorada):** El mercado se encuentra en fase de **{cruce_50_200}**.

---
*Este informe ha sido generado automáticamente por el robot de GitHub Actions sin intervención humana.*
"""

    # Guardar el informe en un archivo de texto
    with open("DIARIO_TRADING.md", "w", encoding="utf-8") as f:
        f.write(informe)

    print("Informe generado con éxito.")

except Exception as e:
    print(f"Error crítico durante la ejecución: {e}")
    sys.exit(0)
