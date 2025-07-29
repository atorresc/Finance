from fastapi import FastAPI
from datetime import datetime
import yfinance as yf
import pandas as pd

app = FastAPI()

# Lista de tickers de FIBRAs
TICKERS = [
    "DANHOS13.MX",
    "FIBRAMQ12.MX",
    "FNOVA17.MX",
    "FMTY14.MX"
]

@app.get("/dividend-yield")
def get_dividend_yield():
    resultados = []

    for ticker in TICKERS:
        try:
            yf_ticker = yf.Ticker(ticker)
            precio = yf_ticker.info.get("regularMarketPrice")
            nombre = yf_ticker.info.get("shortName", ticker)
            market_cap = yf_ticker.info.get("marketCap")
            pe_ratio = yf_ticker.info.get("trailingPE")
            volume = yf_ticker.info.get("volume")
            week_high = yf_ticker.info.get("fiftyTwoWeekHigh")
            week_low = yf_ticker.info.get("fiftyTwoWeekLow")
            summary = yf_ticker.info.get("longBusinessSummary")
    
            dividendos = yf_ticker.dividends[-6:]  # Últimos 6 dividendos
            fechas = dividendos.index.to_list()

            # Determinar frecuencia de pago (por intervalo de fechas)
            if len(fechas) >= 2:
                intervalos = [(fechas[i] - fechas[i - 1]).days for i in range(1, len(fechas))]
                promedio_intervalo = sum(intervalos) / len(intervalos)
                if promedio_intervalo < 45:
                    frecuencia_anual = 12
                    tipo_pago = "Mensual"
                else:
                    frecuencia_anual = 4
                    tipo_pago = "Trimestral"
            else:
                frecuencia_anual = 4
                tipo_pago = "Desconocido"

            dividendo_reciente = round(dividendos[-1], 4) if not dividendos.empty else None

            if precio and dividendo_reciente:
                dy = round((dividendo_reciente * frecuencia_anual / precio) * 100, 2)
                resultados.append({
                    "FIBRA": nombre,
                    "Ticker": ticker,
                    "Precio actual (MXN)": round(precio, 2),
                    "Último dividendo registrado": dividendo_reciente,
                    "Frecuencia de pago": tipo_pago,
                    "Dividend Yield Anualizado (%)": dy,
                    "Market Cap": market_cap,
                    "P/E Ratio": pe_ratio,
                    "Volumen actual": volume,
                    "52w Alto / Bajo": f"{week_high} / {week_low}",
                    # "Resumen": summary[:200],  # solo una parte del texto largo
                    "Fecha": datetime.today().strftime("%Y-%m-%d")
                })
            else:
                resultados.append({
                    "FIBRA": nombre,
                    "Ticker": ticker,
                    "Error": "No se encontró precio o dividendo reciente"
                })

        except Exception as e:
            resultados.append({
                "Ticker": ticker,
                "Error": str(e)
            })

    return {"fibras": resultados}
