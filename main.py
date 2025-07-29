from fastapi import FastAPI
from datetime import datetime
import yfinance as yf

app = FastAPI()

TICKERS = [
    "DANHOS13.MX",
    "FIBRAMQ12.MX",
    "FNOVA17.MX",
    "FMTY14.MX",
    "FCFE18.MX",
    "FIBRAPL14.MX",
    "FSITES20.MX",
    "FSHOP13.MX"
]

def calcular_datos_clave(ticker: str):
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        precio = info.get("regularMarketPrice")
        nombre = info.get("shortName", ticker)

        dividendos = yf_ticker.dividends[-6:]
        fechas = dividendos.index.to_list()

        if len(fechas) >= 2:
            intervalos = [(fechas[i] - fechas[i - 1]).days for i in range(1, len(fechas))]
            promedio_intervalo = sum(intervalos) / len(intervalos)
            tipo_pago = "Mensual" if promedio_intervalo < 45 else "Trimestral"
            frecuencia_anual = 12 if tipo_pago == "Mensual" else 4
        else:
            tipo_pago = "Desconocido"
            frecuencia_anual = 4

        dividendo_reciente = round(dividendos[-1], 4) if not dividendos.empty else None
        dy = round((dividendo_reciente * frecuencia_anual / precio) * 100, 2) if (precio and dividendo_reciente) else None

        return {
            "FIBRA": nombre,
            "Ticker": ticker,
            "Precio actual (MXN)": round(precio, 2) if precio else None,
            "Último dividendo registrado": dividendo_reciente,
            "Frecuencia de pago": tipo_pago,
            "Dividend Yield Anualizado (%)": dy,
            "Fecha": datetime.today().strftime("%Y-%m-%d")
        }
    except Exception as e:
        return {
            "Ticker": ticker,
            "Error": str(e)
        }

@app.get("/fibras")
def get_todas_las_fibras():
    return {"fibras": [calcular_datos_clave(t) for t in TICKERS]}

@app.get("/ticker-info/{ticker}")
def get_info_completa_de_ticker(ticker: str):
    try:
        yf_ticker = yf.Ticker(ticker.upper())
        return yf_ticker.info  # Devuelve todas las propiedades
    except Exception as e:
        return {"error": str(e)}
