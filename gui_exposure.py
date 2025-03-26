import tkinter as tk
from tkinter import ttk
import pandas as pd
import yfinance as yf  # Si no lo has importado, asegúrate de que esté disponible
import pandas as pd
from calc_exposure import *
from calc_other_inputs import *
from get_portfolio import *

# Cargar datos del portfolio
positions = get_current_portfolio()
positions_quintet = pd.read_excel("input/positions_quintet.xlsx")
currencies = ["USD", "EUR"]
fx_exchange = currency_to_eur(currencies)  # Esta es la variable global
positions = pd.concat([positions_quintet, positions], ignore_index=True)

# Reemplazos de símbolos
positions["UnderlyingSymbol"].replace({
    "HEIA": "HEIA.AS",
    "BRK B": "BRK-B",
    "MES": "ES=F",
    "ESM5": "ES=F",
    "MC": "MC.PA",
    "SOI": "SOI.PA",
}, inplace=True)

# Agrupar posiciones
positions = (
    positions.groupby(by=["Description"])
    .agg({
        "Symbol": "first",
        "CurrencyPrimary": "first",
        "AssetClass": "first",
        "Quantity": "sum",
        "MarkPrice": "first",
        "Multiplier": "first",
        "UnderlyingSymbol": "first",
    })
    .reset_index()
)

# Añadir Market Price
positions = fill_market_price(positions)

# Añadir Beta
betas = pd.read_csv("input/betas.csv")
positions = add_beta_to_portfolio(positions, betas)

# Añadir tipo de cambio
positions = positions.merge(fx_exchange, on="CurrencyPrimary", how="left")

# Diccionario temporal de deltas
deltas_temp = pd.DataFrame(list({
    'ALPHABET INC-CL A': None,
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
    'SOI 17APR25 57 P': -0.593
}.items()), columns=['Description', 'Delta'])
positions = positions.merge(deltas_temp, on="Description", how="left")


# Función para calcular exposición (usando tu código)
def calculate_exposure():
    global fx_exchange  # Declarar fx_exchange como global si necesitas usarla dentro de la función
    # Aquí va tu lógica para calcular la exposición
    individual_exposures, total_exposure = portfolio_exposure(positions)
    
    # Exposición en términos de MES
    data = yf.Ticker("ES=F")
    current_price_fut = data.history(period="1d")["Close"].iloc[-1]
    beta = float(betas[betas["UnderlyingSymbol"] == "ES=F"]["Beta"])
    
    # Usar fx_exchange directamente sin redefinirla
    fx_exchange_rate = fx_exchange[fx_exchange["CurrencyPrimary"] == "USD"]["FX_Exchange"].values[0]
    MES_exposure = current_price_fut * fx_exchange_rate * 5 * beta
    
    # % Long and short
    total_absolute_exposure = individual_exposures["Exposure"].abs().sum()
    grouped_by_direction = individual_exposures.groupby(by="Direction").sum().reset_index()
    long_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Long"]["Exposure"]))
    short_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Short"]["Exposure"]))
    pct_short = 100 * short_absolute / total_absolute_exposure
    pct_long = 100 * long_absolute / total_absolute_exposure

    # Mostrar los resultados en el cuadro de texto
    results_text.set(f"Total exposure: {total_exposure} EUR\n"
                     f"Total exposure in MES: {total_exposure / float(MES_exposure)} MES\n"
                     f"Position short: {pct_short} %\n"
                     f"Position long: {pct_long} %")


# Crear la ventana principal
root = tk.Tk()
root.title("Cálculo de Exposición del Portfolio")

# Crear el cuadro de tabla
tree = ttk.Treeview(root, columns=('Description', 'Symbol', 'Currency', 'Quantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'), show="headings")

# Configurar las columnas
tree.heading('Description', text='Descripción')
tree.heading('Symbol', text='Símbolo')
tree.heading('Currency', text='Moneda')
tree.heading('Quantity', text='Cantidad')
tree.heading('MarkPrice', text='Precio del subyacente')
tree.heading('Multiplier', text='Multiplicador')
tree.heading('Beta', text='Beta')
tree.heading('Delta', text='Delta')

# Insertar los datos de las posiciones en la tabla
for _, row in positions.iterrows():
    # Asegúrate de insertar los valores correctos en cada columna
    tree.insert('', 'end', values=(row['Description'], row['Symbol'], row['CurrencyPrimary'], row['Quantity'],
                                   row['MarkPrice'], row['Multiplier'], row['Beta'], row['Delta']))

tree.pack(padx=10, pady=10)

# Crear el botón para calcular
calculate_button = tk.Button(root, text="Calcular", command=calculate_exposure)
calculate_button.pack(pady=10)

# Crear un campo para mostrar los resultados
results_text = tk.StringVar()
results_label = tk.Label(root, textvariable=results_text)
results_label.pack(pady=10)

# Ejecutar la interfaz
root.mainloop()
