import pandas as pd


def valores_contenidos(df1, columna1, df2, columna2):
    """
    Verifica si todos los valores únicos de una columna de df1 están en una columna de df2.

    :param df1: Primer DataFrame
    :param columna1: Nombre de la columna en df1
    :param df2: Segundo DataFrame
    :param columna2: Nombre de la columna en df2
    :return: True si todos los valores únicos de columna1 están en columna2, False si no
    """
    valores_df1 = set(df1[columna1].unique())  # Valores únicos de df1
    valores_df2 = set(df2[columna2].unique())  # Valores únicos de df2

    return valores_df1.issubset(valores_df2)  # Verifica si df1 está contenido en df2
