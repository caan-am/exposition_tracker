import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import pandas as pd


def equity_profile(current_price, num_shares, fx_exchange, beta_sp500, shocks=None):
    """
    Calcula el perfil de una acción en función de cambios en el SP500.

    Parámetros:
    - precio_actual: Precio actual de la acción.
    - beta_sp500: Beta de la acción con respecto al SP500.
    - shocks_sp500: Lista de variaciones porcentuales en el SP500 (ej. [-5, -2, 0, 2, 5]).

    Retorna:
    - Diccionario con los precios simulados de la acción en función del SP500.
    """
    if shocks is None:
        shocks = np.linspace(-5, 5, 50)  # Porcentajes de cambio en el SP500

    # To-do transform currency
    shocks = np.array(shocks) / 100  # Convertir a proporciones
    value_change = shocks * beta_sp500  # Cambio en la acción
    current_valuation = current_price * num_shares * fx_exchange
    simulated_valuation = current_valuation * (1 + value_change)
    simulated_variaton = simulated_valuation - current_valuation

    # variation in eur
    return simulated_variaton


def option_profile(current_price, beta_sp500, shocks=None):
    return None


def futures_profile(current_price, beta_sp500, shocks=None):
    return None


def portfolio_profile(portfolio, shocks=None):
    """
    Calcula el perfil de una cartera en función de cambios en el SP500 para cada producto.

    Parámetros:
    - portfolio: DataFrame con las columnas 'producto', 'precio_actual', 'beta_sp500'.
                  'producto' es el tipo de producto (e.g., 'accion', 'opcion', 'futuro').
                  'precio_actual' es el precio actual del producto.
                  'beta_sp500' es la beta de ese producto con respecto al SP500.
    - shocks: Lista de variaciones porcentuales en el SP500 (ej. [-5, -2, 0, 2, 5]). Si no se pasa, se usa un rango por defecto.

    Retorna:
    - Diccionario con los perfiles de precios de cada producto y el perfil total.
    """
    # Si no se pasa una lista de shocks, se crea un rango por defecto.
    if shocks is None:
        shocks = np.arange(-10, 10.25, 0.25)

    shocks = np.array(shocks) / 100  # Convertir a proporciones

    # Crear un diccionario para guardar los perfiles individuales
    perfiles_individuales = {}
    perfil_total = np.zeros_like(shocks)

    # Iterar sobre el portfolio
    for _, row in portfolio.iterrows():

        fx_exchange = row["FX_Exchange"]
        instrument = row["AssetClass"]
        name = row["Description"]
        multiplier = row["Multiplier"]
        quantity = row["Quantity"]
        current_price = row["MarkPrice"]
        beta_sp500 = row["Beta"]

        # Llamar a la función correspondiente dependiendo del tipo de producto
        if instrument == "STK":
            simulated_variaton = equity_profile(
                current_price, quantity, fx_exchange, beta_sp500, shocks * 100
            )
        elif instrument == "opcion":
            simulated_variaton = option_profile(current_price, beta_sp500, shocks * 100)
        elif instrument == "futuro":
            simulated_variaton = futures_profile(
                current_price, beta_sp500, shocks * 100
            )
        else:
            raise ValueError(f"Producto {instrument} no reconocido.")

        # Guardar el perfil individual
        perfiles_individuales[name] = simulated_variaton

        # Sumar al perfil total
        perfil_total += simulated_variaton

    return perfiles_individuales, perfil_total


# def option_price(S, K, r, sigma, T, option_type="call"):
#     """
#     Calcula el precio de una opción europea usando Black-Scholes.
#     """
#     d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
#     d2 = d1 - sigma * np.sqrt(T)

#     if option_type == "call":
#         return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
#     elif option_type == "put":
#         return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
#     else:
#         raise ValueError("option_type debe ser 'call' o 'put'")

# def option_profile(current_price, beta_sp500, K, r, sigma, T, option_type="call", shocks=None):
#     """
#     Calcula el perfil de una opción en función de los cambios en el SP500.
#     """
#     if shocks is None:
#         shocks = np.linspace(-5, 5, 50)  # Cambios en el SP500 de -5% a +5%

#     precios_accion = equity_profile(current_price, beta_sp500, shocks)
#     precios_opcion = np.array([option_price(S, K, r, sigma, T, option_type) for S in precios_accion])

#     return shocks, precios_opcion


# current_price = 100
# beta = 1.2
# K = 100
# r = 0.05
# sigma = 0.2
# T = 0.5

# shocks, call_profile = option_profile(current_price, beta, K, r, sigma, T, option_type="call")
# shocks, put_profile = option_profile(current_price, beta, K, r, sigma, T, option_type="put")

# plot_profiles([
#     (shocks, call_profile, "Call Option"),
#     (shocks, put_profile, "Put Option")
# ])
