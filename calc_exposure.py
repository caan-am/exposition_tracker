import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import pandas as pd


def calc_equity_exposure(current_price, num_shares, fx_exchange, beta_sp500):
    return current_price * num_shares * fx_exchange * beta_sp500


def calc_future_exposure(
    current_price, num_contracts, fx_exchange, beta_sp500, multiplier
):
    return current_price * num_contracts * fx_exchange * multiplier * beta_sp500


def calc_option_exposure(
    current_underlying_price,
    num_contracts,
    delta,
    fx_exchange,
    beta_underlying_sp500,
    multiplier,
):
    """
    Consideramos que tenemos delta*num_acciones de ese subyacente
    """
    return (
        current_underlying_price
        * num_contracts
        * multiplier
        * delta
        * beta_underlying_sp500
        * fx_exchange
    )

def portfolio_exposure(portfolio):
    # Crear un diccionario para guardar los perfiles individuales
    individual_exposure = {}
    total_exposure = 0

    # Iterar sobre el portfolio
    for _, row in portfolio.iterrows():

        fx_exchange = row["FX_Exchange"]
        instrument = row["AssetClass"]
        name = row["Description"]
        multiplier = row["Multiplier"]
        quantity = row["Quantity"]
        current_price = row["MarkPrice"]
        beta_sp500 = row["Beta"]
        delta = row["Delta"]

        # Llamar a la función correspondiente dependiendo del tipo de producto
        if instrument == "STK":
            exposure = calc_equity_exposure(current_price, quantity, fx_exchange, beta_sp500)
        elif (instrument == "OPT"):
            exposure = calc_option_exposure(current_price, quantity, delta, fx_exchange,  beta_sp500,  multiplier)
        elif instrument == "FOP":
            exposure = calc_future_exposure(current_price*delta, quantity, fx_exchange, beta_sp500, multiplier)
        elif instrument == "FUT":
            exposure = calc_future_exposure(current_price, quantity, fx_exchange, beta_sp500, multiplier)
        else:
            raise ValueError(f"Producto {instrument} no reconocido.")

        # Guardar el perfil individual
        individual_exposure[name] = exposure

        # Sumar al perfil total
        total_exposure += exposure

    individual_exposures = pd.DataFrame(list(individual_exposure.items()), columns=['Description', 'Exposure'])
    individual_exposures['Direction'] = individual_exposures['Exposure'].apply(lambda x: 'Long' if x > 0 else ('Short' if x < 0 else 'Neutral'))
    return individual_exposures, total_exposure