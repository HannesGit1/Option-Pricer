from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
import yfinance as yf
import numpy as np
from scipy.stats import norm
import sqlite3
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")
def init_db():
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            strike REAL,
            days INTEGER,
            spot REAL,
            volatility REAL,
            bs_price REAL,
            mc_price REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptionRequest(BaseModel):
    symbol: str
    strikePrice: float
    days: int

def monteCarloGBM(S, T, rf, sigma):
    Z = np.random.standard_normal((10000, T))
    dt = 1/365
    drift = (rf - 0.5 * sigma **2)*dt
    oneDay = sigma * np.sqrt(dt) * Z
    cumulative = np.cumsum(drift + oneDay, axis=1)
    db = S * np.exp(cumulative)
    return db

@app.get("/")
def showForm(request: Request):
    return templates.TemplateResponse(name = "index.html", request = request)

@app.post("/")
def blackScholes(params: OptionRequest):
    if params.strikePrice <= 0:
        raise HTTPException(status_code=400, detail="Strike price must be strictly greater than 0.")
        
    if params.days <= 0:
        raise HTTPException(status_code=400, detail="Days to expiration must be at least 1.")
 
    if params.days > 3650:
        raise HTTPException(status_code=400, detail="Simulation limited to a maximum of 3650 days (10 years) to prevent server overload.")
    stock = yf.Ticker(params.symbol)
    historyDay = stock.history(period="1d")
    if historyDay.empty:
        raise HTTPException(status_code=404, detail=f"Ticker '{params.symbol}' not found or has no current trading data.")
    historyYear = stock.history(period="1y")
    if len(historyYear) < 2:
        raise HTTPException(status_code=400, detail=f"Not enough historical data for '{params.symbol}' to calculate historical volatility.")
    
    S = historyDay['Close'].iloc[-1]
    yields = np.log(historyYear['Close'] / historyYear['Close'].shift(1))
    sigmar = yields.std() * np.sqrt(252)
    if sigmar == 0.0 or np.isnan(sigmar):
         raise HTTPException(status_code=400, detail="Calculated volatility is 0. Cannot perform Black-Scholes calculation.")
    
    K = params.strikePrice
    rf = 0.04
    T = params.days / 365.0
    
    d1 = (np.log(S / K) + (rf + (sigmar ** 2) / 2) * T) / (sigmar * np.sqrt(T))
    d2 = d1 - sigmar * np.sqrt(T)
    
    C = S * norm.cdf(d1) - K * np.exp(-rf * T) * norm.cdf(d2)

    db = monteCarloGBM(S, params.days, rf, sigmar)
    finalPrices = db[:, -1]
    margins = np.maximum(finalPrices - K, 0)
    mean = np.mean(margins)
    callPrice = mean * np.exp(-rf * T)
    chartData = db[:50, :].tolist()

    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''INSERT INTO history (timestamp, symbol, strike, days, spot, volatility, bs_price, mc_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (now, params.symbol.upper(), params.strikePrice, params.days, round(S, 2), round(sigmar, 4), round(C, 2), round(callPrice, 4)
    ))
    conn.commit()
    conn.close()
    
    return {
        "symbol": params.symbol,
        "spotPrice": round(S, 2),  
        "volatility": round(sigmar, 4),
        "bsPrice": round(C, 2),
        "mcPrice": round(callPrice, 4),
        "chartData": chartData,
        "days": params.days
    }
@app.get("/history")
def showHistory(request: Request):
    with sqlite3.connect('history.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY id DESC')
        rows = cursor.fetchall()
    
    return templates.TemplateResponse(
        request=request, 
        name="history.html", 
        context={"history": rows}
    )
    