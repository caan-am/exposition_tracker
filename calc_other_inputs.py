import yfinance as yf
import pandas as pd
import numpy as np


def calcular_beta_cov_var(tickers, inicio, fin):
    # Descargar datos históricos del S&P 500 y las acciones
    sp500 = yf.download("^GSPC", start=inicio, end=fin)["Close"]
    acciones = yf.download(tickers, start=inicio, end=fin)["Close"]

    # Calcular los rendimientos diarios (porcentaje de cambio)
    sp500_rendimiento = sp500.pct_change().dropna()
    acciones_rendimiento = acciones.pct_change().dropna()

    # Asegurarse de que ambos DataFrames tengan el mismo índice (fechas)
    datos_combinados = pd.concat([acciones_rendimiento, sp500_rendimiento], axis=1)
    datos_combinados = datos_combinados.dropna()

    # Calcular la beta para cada acción usando Covarianza / Varianza
    betas = []

    for ticker in tickers:
        # Rendimiento de la acción
        y = datos_combinados[ticker]
        # Rendimiento del S&P 500
        X = datos_combinados["^GSPC"]

        # Calcular la covarianza y la varianza
        covarianza = np.cov(y, X)[0, 1]  # Covarianza entre la acción y el S&P 500
        varianza = np.var(X)  # Varianza del S&P 500

        # Calcular la beta
        beta = covarianza / varianza

        # Añadir el resultado al listado de betas
        betas.append({"UnderlyingSymbol": ticker, "Beta": beta})

    # Convertir la lista de diccionarios a un DataFrame
    betas_df = pd.DataFrame(betas)

    return betas_df


def currency_to_eur(currencies):
    """
    Convierte una lista de monedas a EUR usando Yahoo Finance.

    :param divisas: Lista de códigos de monedas (ej. ['USD', 'GBP', 'JPY'])
    :return: DataFrame con las tasas de cambio de cada divisa a EUR.
    """
    resultados = []

    for currency in currencies:
        ticker = f"{currency}EUR=X"  # Formato de Yahoo Finance

        try:
            # Obtener datos de Yahoo Finance
            data = yf.Ticker(ticker)
            tasa_cambio = data.history(period="1d")["Close"].iloc[
                -1
            ]  # Último precio de cierre

            resultados.append({"CurrencyPrimary": currency, "FX_Exchange": tasa_cambio})

        except:
            resultados.append({"CurrencyPrimary": currency, "FX_Exchange": "Error"})

    # Convertir la lista de resultados en un DataFrame
    df_resultados = pd.DataFrame(resultados)

    return df_resultados


def fill_market_price(df):
    """
    Rellena la columna 'MarkPrice' con el último precio de cierre de cada Ticker en la columna 'Ticker'.

    :param df: DataFrame con una columna 'Ticker' y una columna vacía 'MarkPrice'.
    :return: DataFrame con la columna 'MarkPrice' rellena.
    """
    df = df.copy()  # Evitar modificar el original

    for index, row in df.iterrows():
        ticker = row["UnderlyingSymbol"]

        try:
            # Obtener el último precio desde Yahoo Finance
            data = yf.Ticker(ticker)
            last_price = data.history(period="1d")["Close"].iloc[-1]

            df.at[index, "MarkPrice"] = last_price  # Rellenar la columna MarkPrice

        except:
            df.at[index, "MarkPrice"] = "Error"  # Manejo de errores

    return df


# #TO-DO sustituir con IBKR para poder hacer esto automatico y no a mano
# tickers = ['HEIA.AS', 'MC', 'AMZN', 'CNR', 'HHH', 'INTC', 'NVO', 'CRESY']  # Tickers de las acciones que deseas analizar
# inicio = '2020-01-01'  # Fecha de inicio
# fin = '2025-01-01'  # Fecha de fin

# betas = calcular_beta_cov_var(tickers, inicio, fin)
# betas['Symbol'].replace('HEIA.AS','HEIA', inplace=True)
# betas.to_csv("input/betas.csv", index=False)
