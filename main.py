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
    "FSHOP13.MX",
    "FVIA16.MX",
    "FINN13.MX",
    "NEXT25.MX",
    "FIHO12.MX",
    "FUNO11.MX",
    "EDUCA18.MX",
    "STORAGE18.MX"
]


def calcular_datos_clave(ticker: str):
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        precio = info.get("regularMarketPrice")
        nombre = info.get("shortName", ticker)

        # Dividendos recientes
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

        # Datos dinámicos
        affo_aproximado = info.get("freeCashflow")  # Proxy del AFFO
        deuda_total = info.get("totalDebt")
        balance = yf_ticker.balance_sheet
        activos_totales = balance.loc["Total Assets"][0] if "Total Assets" in balance.index else None
        cbfis = info.get("sharesOutstanding")

        affo_por_cbfis = round(affo_aproximado / cbfis, 4) if affo_aproximado and cbfis else None
        payout_ratio = round((dividendo_reciente * frecuencia_anual * cbfis / affo_aproximado) * 100, 2) if (affo_aproximado and dividendo_reciente and cbfis) else None
        leverage_ratio = round((deuda_total / activos_totales) * 100, 2) if (deuda_total and activos_totales) else None

        return {
            "FIBRA": nombre,
            "Ticker": ticker,
            "Precio actual (MXN)": round(precio, 2) if precio else None,
            "Último dividendo registrado": dividendo_reciente,
            "Frecuencia de pago": tipo_pago,
            "Dividend Yield Anualizado (%)": dy,
            "AFFO estimado (freeCashflow)": affo_aproximado,
            "CBFIs en circulación (dinámico)": cbfis,
            "AFFO por CBFI": affo_por_cbfis,
            "AFFO Payout Ratio (%)": payout_ratio,
            "Deuda total": deuda_total,
            "Activos totales": activos_totales,
            "Apalancamiento (%)": leverage_ratio,
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
        return yf_ticker.info
    except Exception as e:
        return {"error": str(e)}