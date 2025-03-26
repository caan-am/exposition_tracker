import pandas as pd
from calc_exposure import *
from calc_other_inputs import *
from get_portfolio import *

# Leer datos y tratarlos un poco
positions_ibkr = get_current_portfolio()
positions_quintet = pd.read_excel("input/positions_quintet.xlsx")

currencies = ["USD", "EUR"]
fx_exchange = currency_to_eur(currencies)

positions = pd.concat([positions_quintet, positions_ibkr], ignore_index=True)
positions["UnderlyingSymbol"].replace("HEIA", "HEIA.AS", inplace=True)
positions["UnderlyingSymbol"].replace("BRK B", "BRK-B", inplace=True)
positions["UnderlyingSymbol"].replace("MES", "ES=F", inplace=True)
positions["UnderlyingSymbol"].replace("ESM5", "ES=F", inplace=True)
positions["UnderlyingSymbol"].replace("MC", "MC.PA", inplace=True)
positions["UnderlyingSymbol"].replace("SOI", "SOI.PA", inplace=True)
# Juntar posiciones deL mismo producto 
positions = (
    positions.groupby(by=["Description"])
    .agg(
        {
            "Symbol": "first",
            "CurrencyPrimary": "first",
            "AssetClass": "first",
            "Quantity": "sum",
            "MarkPrice": "first",
            "Multiplier": "first",
            "UnderlyingSymbol":"first",
        }
    )
    .reset_index()
)

# Añadir Market Price ultimo
positions = fill_market_price(positions)

# Añadir beta al portfolio

betas = pd.read_csv("input/betas.csv")
positions = add_beta_to_portfolio(positions, betas)

# Añadir fx al portfolio
positions = positions.merge(fx_exchange, on="CurrencyPrimary", how="left")

# Añadir deltas To-do. Hacer función fill_deltas
dict_deltas_temporal = {'ALPHABET INC-CL A': None,
                        'AMAZON.COM INC': None, 
                        'BRK B 28MAR25 515 P': -0.038, 
                        'CORE NATURAL RESOURCES INC': None, 
                        'CRESUD S.A.-SPONS ADR': None, 
                        'ES 17APR25 5480 P': -0.153,
                        'ES 17APR25 5670 P': -0.346,
                        'GOOGL 28MAR25 157.5 P': -0.041, 
                        'HEINEKEN NV': None,
                        'HOWARD HUGHES HOLDINGS INC': None,
                        'INTEL CORP': None, 
                        'LVMH MOET HENNESSY LOUIS VUI': None,
                        'MES 20JUN25': None, 
                        'MSFT 28MAR25 375 P': -0.036, 
                        'NOVO-NORDISK A/S-SPONS ADR': None, 
                        'NVO 28MAR25 73 P': -0.614, 
                        'PAYPAL HOLDINGS INC': None, 
                        'VET 20JUN25 10 P': -0.836,
                        'HEIA 28MAR25 74 P': -0.304,
                        'SOI 17APR25 57 P': -0.593}

deltas_temp = pd.DataFrame(list(dict_deltas_temporal.items()), columns=['Description', 'Delta'])
positions = positions.merge(deltas_temp, on="Description", how="left")

# Calcular la exposición de la cartera

individual_exposures, total_exposure = portfolio_exposure(positions)

# Exposición en términos de MES
data = yf.Ticker("ES=F")
current_price_fut = data.history(period="1d")["Close"].iloc[-1]
beta = float(betas[betas["UnderlyingSymbol"] == "ES=F"]["Beta"])
fx_exchange = float(fx_exchange[fx_exchange["CurrencyPrimary"] == "USD"]["FX_Exchange"])
MES_exposure =  current_price_fut * fx_exchange * 5 * beta

# % Long and short
total_absolute_exposure = individual_exposures["Exposure"].abs().sum()
grouped_by_direction = individual_exposures.groupby(by="Direction").sum().reset_index()
long_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Long"]["Exposure"]))
short_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Short"]["Exposure"]))
pct_short = 100* short_absolute/total_absolute_exposure
pct_long = 100* long_absolute/total_absolute_exposure

print("Total exposure: " + str(total_exposure) + " EUR")
print("Total exposure in MES: " + str(total_exposure/float(MES_exposure)) + " MES")
print("Position short: " + str(pct_short) + " %")
print("Position long: " + str(pct_long) + " %")