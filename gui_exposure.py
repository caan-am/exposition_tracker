import tkinter as tk
from tkinter import ttk
import pandas as pd
import yfinance as yf
from calc_exposure import *
from calc_other_inputs import *
from get_portfolio import *

# Cargar datos del portfolio
positions = get_current_portfolio()
positions_quintet = pd.read_excel("input/positions_quintet.xlsx")
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
currencies = ["USD", "EUR"]
fx_exchange = currency_to_eur(currencies)
positions = positions.merge(fx_exchange, on="CurrencyPrimary", how="left")

# Diccionario temporal de deltas
deltas_temp = pd.DataFrame(list({
    'ALPHABET INC-CL A': None,
    'AMAZON.COM INC': None, 
    'BRK B 28MAR25 515 P': -0.028, 
    'CORE NATURAL RESOURCES INC': None, 
    'CRESUD S.A.-SPONS ADR': None, 
    'ES 17APR25 5480 P': -0.155,
    'ES 17APR25 5670 P': -0.351,
    'GOOGL 28MAR25 157.5 P': -0.061, 
    'HEINEKEN NV': None,
    'HOWARD HUGHES HOLDINGS INC': None,
    'INTEL CORP': None, 
    'LVMH MOET HENNESSY LOUIS VUI': None,
    'MES 20JUN25': None, 
    'MSFT 28MAR25 375 P': -0.044, 
    'NOVO-NORDISK A/S-SPONS ADR': None, 
    'NVO 28MAR25 73 P': -0.661, 
    'PAYPAL HOLDINGS INC': None, 
    'VET 20JUN25 10 P': -0.837,
    'HEIA 28MAR25 74 P': -0.288,
    'SOI 17APR25 57 P': -0.593
}.items()), columns=['Description', 'Delta'])

positions = positions.merge(deltas_temp, on="Description", how="left")

# Función para calcular exposición
def calculate_exposure():
    global fx_exchange
    individual_exposures, total_exposure = portfolio_exposure(positions)

    # Precio actual del MES
    data = yf.Ticker("ES=F")
    current_price_fut = data.history(period="1d")["Close"].iloc[-1]
    beta = float(betas[betas["UnderlyingSymbol"] == "ES=F"]["Beta"])

    fx_exchange_rate = fx_exchange[fx_exchange["CurrencyPrimary"] == "USD"]["FX_Exchange"].values[0]
    MES_exposure = current_price_fut * fx_exchange_rate * 5 * beta

    # % Long y Short
    total_absolute_exposure = individual_exposures["Exposure"].abs().sum()
    grouped_by_direction = individual_exposures.groupby(by="Direction").sum().reset_index()
    long_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Long"]["Exposure"]))
    short_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Short"]["Exposure"]))
    pct_short = 100 * short_absolute / total_absolute_exposure
    pct_long = 100 * long_absolute / total_absolute_exposure

    # Formatear los resultados con , como decimal y . como separador de miles
    results_text.set(f"Total exposure: {total_exposure:,.2f} EUR\n"
                     f"Total exposure in MES: {total_exposure / float(MES_exposure):,.2f} MES\n"
                     f"Position short: {pct_short:,.2f} %\n"
                     f"Position long: {pct_long:,.2f} %")

# Crear ventana principal
root = tk.Tk()
root.title("Cálculo de Exposición del Portfolio")
root.geometry("900x600")  # Ajusta el tamaño inicial de la ventana

# Crear frame principal
frame = tk.Frame(root)
frame.pack(expand=True, fill="both", padx=10, pady=10)

# Crear el cuadro de tabla
tree = ttk.Treeview(frame, columns=('Description', 'Symbol', 'Currency', 'Quantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'), show="headings")

# Configurar las columnas
tree.heading('Description', text='Descripción')
tree.heading('Symbol', text='Símbolo')
tree.heading('Currency', text='Moneda')
tree.heading('Quantity', text='Cantidad')
tree.heading('MarkPrice', text='Precio de Mercado')
tree.heading('Multiplier', text='Multiplicador')
tree.heading('Beta', text='Beta')
tree.heading('Delta', text='Delta')

# Hacer que las columnas se expandan
for col in ('Description', 'Symbol', 'Currency', 'Quantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'):
    tree.column(col, anchor="center", stretch=True)

# Función para insertar datos diferenciando AssetClass
def insert_positions_by_asset_class():
    asset_class_titles = {
        'FOP': "Opciones sobre futuros",
        'OPT': "Opciones",
        'FUT': "Futuros",
        'STK': "Acciones"
    }

    for asset_class, title in asset_class_titles.items():
        tree.insert('', 'end', values=(title, '', '', '', '', '', '', ''), tags=("title",))

        for _, row in positions[positions['AssetClass'] == asset_class].iterrows():
            tree.insert('', 'end', values=(row['Description'], row['Symbol'], row['CurrencyPrimary'], 
                                           f"{row['Quantity']:.2f}", 
                                           f"{row['MarkPrice']:.2f}", 
                                           f"{row['Multiplier']:.2f}" if pd.notna(row['Multiplier']) else '', 
                                           f"{row['Beta']:.2f}" if pd.notna(row['Beta']) else '',
                                           f"{row['Delta']:.3f}" if pd.notna(row['Delta']) else ''), 
                        tags=("normal",))

insert_positions_by_asset_class()

# Configurar estilos
style = ttk.Style()
style.configure('TTreeview', font=('Helvetica', 10))
style.configure('TTreeview.Heading', font=('Helvetica', 12, 'bold'))

tree.tag_configure('title', font=('Helvetica', 12, 'bold'))
tree.tag_configure('normal', font=('Helvetica', 10))

# Hacer que el cuadro se expanda
tree.pack(expand=True, fill="both")

# Botón para calcular
calculate_button = tk.Button(root, text="Calcular", command=calculate_exposure, font=("Helvetica", 12, "bold"), bg="lightblue")
calculate_button.pack(pady=10)

# Etiqueta para resultados
results_text = tk.StringVar()
results_label = tk.Label(root, textvariable=results_text, font=("Helvetica", 12))
results_label.pack(pady=10)

# Ejecutar la interfaz
root.mainloop()
