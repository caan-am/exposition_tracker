import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from io import StringIO
import pandas as pd
import numpy as np

def download_flex_query():
    # Configuración
    TOKEN = 925271898594596300103158
    FLEX_QUERY_ID = 1134153

    # Calcular la fecha de ayer en formato YYYYMMDD
    # yesterday = (datetime.today()).strftime("%Y%m%d")

    # Definir headers
    headers = {"User-Agent": "Python/3.12.8"}

    # Paso 1: Obtener el Reference Code
    url_request = f"https://ndcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={FLEX_QUERY_ID}&v=3"

    # Hacer la solicitud y revisar la respuesta
    response = requests.get(url_request, headers=headers)

    print("Request Headers:", response.request.headers)  # Ver headers enviados
    print("Response Headers:", response.headers)  # Ver headers de la respuesta
    print("Response Status Code:", response.status_code)  # Ver código de estado

    # Ver respuesta completa
    print("Respuesta Completa:")
    print(response.text)

    # Parsear XML
    root = ET.fromstring(response.text)
    status = root.find("Status").text

    if status != "Success":
        raise Exception(f"Error en la solicitud: {response.text}")

    reference_code = root.find("ReferenceCode").text
    print(f"Reference Code obtenido: {reference_code}")

    # Paso 2: Esperar antes de descargar el reporte
    time.sleep(5)

    # Paso 3: Descargar el reporte usando el Reference Code
    url_download = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?t={TOKEN}&q={reference_code}&v=3"
    response = requests.get(url_download, headers=headers)

    # Ver los headers de la respuesta y el contenido del archivo descargado
    print(
        "Response Status Code for Download:", response.status_code
    )  # Ver código de estado del archivo
    print("Response Headers for Download:", response.headers)
    print("Contenido del archivo descargado:")
    return pd.read_csv(StringIO(response.text))

def download_activity_query():
    # Configuración
    TOKEN = 925271898594596300103158
    FLEX_QUERY_ID = 1156863

    # Calcular la fecha de ayer en formato YYYYMMDD
    # yesterday = (datetime.today()).strftime("%Y%m%d")

    # Definir headers
    headers = {"User-Agent": "Python/3.12.8"}

    # Paso 1: Obtener el Reference Code
    url_request = f"https://ndcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={FLEX_QUERY_ID}&v=3"

    # Hacer la solicitud y revisar la respuesta
    response = requests.get(url_request, headers=headers)

    print("Request Headers:", response.request.headers)  # Ver headers enviados
    print("Response Headers:", response.headers)  # Ver headers de la respuesta
    print("Response Status Code:", response.status_code)  # Ver código de estado

    # Ver respuesta completa
    print("Respuesta Completa:")
    print(response.text)

    # Parsear XML
    root = ET.fromstring(response.text)
    status = root.find("Status").text

    if status != "Success":
        raise Exception(f"Error en la solicitud: {response.text}")

    reference_code = root.find("ReferenceCode").text
    print(f"Reference Code obtenido: {reference_code}")

    # Paso 2: Esperar antes de descargar el reporte
    time.sleep(5)

    # Paso 3: Descargar el reporte usando el Reference Code
    url_download = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?t={TOKEN}&q={reference_code}&v=3"
    response = requests.get(url_download, headers=headers)

    # Ver los headers de la respuesta y el contenido del archivo descargado
    print(
        "Response Status Code for Download:", response.status_code
    )  # Ver código de estado del archivo
    print("Response Headers for Download:", response.headers)
    print("Contenido del archivo descargado:")
    
    # Dividir el contenido en tres partes según las cabeceras de cada tabla
    secciones = response.text.split('"ClientAccountID","AccountAlias","Model"')

    # Añadir la cabecera al inicio de cada sección (excepto la primera que ya la tiene)
    secciones = ['"ClientAccountID","AccountAlias","Model"' + s for s in secciones[1:]]

    # Crear DataFrames para cada tabla
    df_posiciones = pd.read_csv(StringIO(secciones[0]))
    df_transacciones = pd.read_csv(StringIO(secciones[1]))
    df_ordenes = pd.read_csv(StringIO(secciones[2]))

  
    # # Opcional: guardar cada DataFrame en archivos separados
    # df_posiciones.to_excel('posiciones.xlsx', index=False)
    # df_transacciones.to_excel('transacciones.xlsx', index=False)
    # df_ordenes.to_excel('ordenes.xlsx', index=False)

    return df_transacciones, df_posiciones, df_ordenes
    
    # Guardar el archivo descargado
    # file_name = f"trade_confirmation_{yesterday}.csv"
    # with open(file_name, "w", encoding="utf-8") as f:
    #     f.write(response.text)

    # print(f"Archivo descargado con éxito: {file_name}")


def get_current_portfolio():
    # Obtener la fecha de hoy
    todays_date = datetime.today().date()
    #Transacciones tiene todo, órdenes tienes asignaciones y eso...
    daily_trades = download_flex_query()
    trades_today = daily_trades[daily_trades.LevelOfDetail == "ORDER"]
    # Quito los trades que no son de hoy
    trades_today['TradeDate'] = pd.to_datetime(trades_today['TradeDate'].dropna().astype(int).astype(str), format='%Y%m%d')
    trades_today = trades_today[(trades_today['TradeDate'].isna()) | 
                                (trades_today['TradeDate'].dt.date == todays_date)]
    transactions, positions, orders = download_activity_query()
    # Quito las positions caducadas
    positions['Expiry'] = pd.to_datetime(positions['Expiry'].dropna().astype(int).astype(str), format='%Y%m%d')
    
    # Filtrar el DataFrame
    positions = positions[(positions['Expiry'].isna()) | (positions['Expiry'].dt.date >= todays_date)]
    current_positions = pd.concat([positions,trades_today])
    
    # To-do: quitar las posiciones caducadas, ocurre los viernes
    current_positions = (
    current_positions.groupby(by=["Description"])
    .agg(
        {
            "Symbol": "first",
            "CurrencyPrimary": "first",
            "AssetClass": "first",
            "Quantity": "sum",
            "Multiplier": "first",
            "UnderlyingSymbol":"first",
            "ListingExchange": "first",
            "Strike":"first",
            "Expiry":"first",
            "UnderlyingSymbol":"first",
            "Conid": "first",
        }
    )
    .reset_index()
)
    
    return current_positions



