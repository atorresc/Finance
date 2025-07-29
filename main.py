from fastapi import FastAPI
from datetime import datetime
import yfinance as yf
import asyncio
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache, cached

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

executor = ThreadPoolExecutor()

# Cache con TTL de 15 minutos (900 segundos)
ticker_cache = TTLCache(maxsize=100, ttl=900)

#@cached(ticker_cache)
def get_info(ticker):
    return yf.Ticker(ticker).info

#@cached(ticker_cache)
def get_balance_sheet(ticker):
    return yf.Ticker(ticker).balance_sheet

#@cached(ticker_cache)
def get_dividends(ticker):
    return yf.Ticker(ticker).dividends[-6:]
    
    
@cached(ticker_cache)
def get_ticker_data(ticker: str):
    t = yf.Ticker(ticker)
    return {
        "info": t.info,
        "dividends": t.dividends[-6:],
        "balance": t.balance_sheet
    } 

async def calcular_datos_clave_async(ticker: str):
    try:
        #loop = asyncio.get_event_loop()
        #info, dividends, balance = await asyncio.gather(
        #    loop.run_in_executor(executor, get_info, ticker),
        #    loop.run_in_executor(executor, get_dividends, ticker),
        #    loop.run_in_executor(executor, get_balance_sheet, ticker),
        #)
        
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, get_ticker_data, ticker)
        
        info = data["info"]
        dividends = data["dividends"]
        balance = data["balance"]

        precio = info.get("regularMarketPrice")
        nombre = info.get("longName", ticker)
        fechas = dividends.index.to_list() if dividends is not None else []

        if len(fechas) >= 2:
            intervalos = [(fechas[i] - fechas[i - 1]).days for i in range(1, len(fechas))]
            promedio_intervalo = sum(intervalos) / len(intervalos)
            tipo_pago = "Mensual" if promedio_intervalo < 45 else "Trimestral"
            frecuencia_anual = 12 if tipo_pago == "Mensual" else 4
        else:
            tipo_pago = "Desconocido"
            frecuencia_anual = 4

        dividendo_reciente = round(dividends[-1], 4) if dividends is not None and not dividends.empty else None
        dy = round((dividendo_reciente * frecuencia_anual / precio) * 100, 2) if (precio and dividendo_reciente) else None

        affo_aproximado = info.get("freeCashflow")
        deuda_total = info.get("totalDebt")
        activos_totales = balance.loc["Total Assets"][0] if balance is not None and "Total Assets" in balance.index else None
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
        return {"Ticker": ticker, "Error": str(e)}

@app.get("/fibras")
async def get_todas_las_fibras():
    resultados = await asyncio.gather(*(calcular_datos_clave_async(t) for t in TICKERS))
    return {"fibras": resultados}

@app.get("/ticker-info/{ticker}")
def get_info_completa_de_ticker(ticker: str):
    try:
        return get_info(ticker.upper())
    except Exception as e:
        return {"error": str(e)}