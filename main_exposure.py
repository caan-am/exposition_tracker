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
                        'BRK B 28MAR25 515 P': -0.034, 
                        'CORE NATURAL RESOURCES INC': None, 
                        'CRESUD S.A.-SPONS ADR': None, 
                        'ES 17APR25 5480 P': -0.126,
                        'ES 17APR25 5670 P': -0.297,
                        'GOOGL 28MAR25 157.5 P': -0.032, 
                        'HEINEKEN NV': None,
                        'HOWARD HUGHES HOLDINGS INC': None,
                        'INTEL CORP': None, 
                        'LVMH MOET HENNESSY LOUIS VUI': None,
                        'MES 20JUN25': None, 
                        'MSFT 28MAR25 375 P': -0.033, 
                        'NOVO-NORDISK A/S-SPONS ADR': None, 
                        'NVO 28MAR25 73 P': -0.575, 
                        'PAYPAL HOLDINGS INC': None, 
                        'VET 20JUN25 10 P': -0.823,
                        'HEIA 28MAR25 74 P': -0.313,
                        'SOI 17APR25 57 P': -0.568}

deltas_temp = pd.DataFrame(list(dict_deltas_temporal.items()), columns=['Description', 'Delta'])
positions = positions.merge(deltas_temp, on="Description", how="left")

# Calcular la exposición de la cartera

individual_exposures, total_exposure = portfolio_exposure(positions)



print("Hello")