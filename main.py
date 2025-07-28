from fastapi import FastAPI
from datetime import datetime
import yfinance as yf
import pandas as pd

app = FastAPI()

# Diccionario de FIBRAs y dividendos trimestrales por CBFI
FIBRAS = {
    "DANHOS13.MX": 0.46,
    "FIBRAMQ12.MX": 0.6125,
    "FNOVA17.MX": 0.5749,
    "FMTY14.MX": 0.259
}

@app.get("/dividend-yield")
def get_dividend_yield():
    resultados = []
    for ticker, dividendo in FIBRAS.items():
        ticker_info = yf.Ticker(ticker)
        precio = ticker_info.info.get("regularMarketPrice")
        nombre = ticker_info.info.get("shortName", ticker)

        if precio:
            dy = round((dividendo * 4 / precio) * 100, 2)
            resultados.append({
                "FIBRA": nombre,
                "Ticker": ticker,
                "Precio_actual_MXN": round(precio, 2),
                "Dividendo_trimestral": dividendo,
                "Dividend_Yield_Anualizado_pct": dy,
                "Fecha": datetime.today().strftime("%Y-%m-%d")
            })
    return {"fibras": resultados}
