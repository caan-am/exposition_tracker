import pandas as pd
from plot_results import *
from calc_profile import *
from calc_other_inputs import *
from utils import *

# Leer datos y tratarlos un poco
positions_ibkr = pd.read_csv("input/positions_ibkr.csv")
positions_quintet = pd.read_excel("input/positions_quintet.xlsx")

currencies = ["USD", "EUR"]
fx_exchange = currency_to_eur(currencies)

positions = pd.concat([positions_quintet, positions_ibkr], ignore_index=True)
positions["UnderlyingSymbol"].replace("HEIA", "HEIA.AS", inplace=True)
positions["UnderlyingSymbol"].replace("MES", "ES=F", inplace=True)

# Añadir Market Price ultimo
positions_equity = positions[(positions.AssetClass == "STK") | (positions.AssetClass == "FUT")]
positions_equity = fill_market_price(positions_equity)

# Añadir beta al portfolio

betas = pd.read_csv("input/betas.csv")
positions_equity = add_beta_to_portfolio(positions_equity, betas)

# Añadir fx al portfolio
positions_equity = positions_equity.merge(fx_exchange, on="CurrencyPrimary", how="left")

# Juntar posiciones de la misma accion 
positions_equity = (
    positions_equity.groupby(by=["Description"])
    .agg(
        {
            "Symbol": "first",
            "CurrencyPrimary": "first",
            "AssetClass": "first",
            "Quantity": "sum",
            "MarkPrice": "first",
            "Multiplier": "first",
            "FX_Exchange": "first",
            "Beta": "first",
            "UnderlyingSymbol":"first",
        }
    )
    .reset_index()
)

# Calcular el perfil de la cartera
shocks = [-5, -2, -1, 0, 1, 2, 5]
perfiles_individuales, perfil_total = portfolio_profile(positions_equity, shocks=shocks)

spx_ticker = yf.Ticker("^GSPC")
last_price_spx = float(spx_ticker.history(period="1d")["Close"].iloc[-1])

# Graficar los perfiles
plot_portfolio_profiles(perfiles_individuales, perfil_total, last_price_spx, shocks=shocks)

variations_table = generate_variation_table(perfil_total, shocks=shocks)
print(variations_table)
