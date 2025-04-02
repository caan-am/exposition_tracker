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

# Añadir precio de mercado
positions = fill_market_price(positions)

# Añadir Beta
betas = pd.read_csv("input/betas.csv")
positions = add_beta_to_portfolio(positions, betas)

# Tipo de cambio
currencies = ["USD", "EUR"]
fx_exchange = currency_to_eur(currencies)
positions = positions.merge(fx_exchange, on="CurrencyPrimary", how="left")

# Añadir columna Include para checkboxes
positions["Include"] = True

# Añadir deltas
deltas_temp = pd.DataFrame(list({
    'ALPHABET INC-CL A': None,
    'AMAZON.COM INC': None, 
    'CORE NATURAL RESOURCES INC': None, 
    'CRESUD S.A.-SPONS ADR': None, 
    'ES 17APR25 5480 P': -0.252,
    'ES 17APR25 5670 P': -0.509,
    'HEINEKEN NV': None,
    'HOWARD HUGHES HOLDINGS INC': None,
    'INTEL CORP': None, 
    'LVMH MOET HENNESSY LOUIS VUI': None,
    'MES 20JUN25': None, 
    'NOVO-NORDISK A/S-SPONS ADR': None, 
    'PAYPAL HOLDINGS INC': None, 
    'VET 20JUN25 10 P': -0.887,
    'HEIA 04APR25 74 P': -0.337,
    'SOI 17APR25 57 P': -0.900,
    'YPF 17APR25 37 P': -0.618,
    'GLNG 17APR25 34 P': -0.215,
}.items()), columns=['Description', 'Delta'])

positions = positions.merge(deltas_temp, on="Description", how="left")

# === Crear ventana principal ===
root = tk.Tk()
root.title("Cálculo de Exposición del Portfolio")
root.geometry("1100x600")

# === Cargar imágenes para checkboxes ===
check_on = tk.PhotoImage(file="input/checkbox_checked.png")
check_off = tk.PhotoImage(file="input/checkbox_unchecked.png")

# === Crear el frame principal ===
frame = tk.Frame(root)
frame.pack(expand=True, fill="both", padx=10, pady=10)

# === Crear el Treeview ===
tree = ttk.Treeview(
    frame,
    columns=('Description', 'Symbol', 'Currency', 'Quantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'),
    show="tree headings"  # Mostrar columna árbol + encabezados
)

# Encabezados
tree.heading('#0', text='Incluir')
tree.column('#0', width=70, anchor='center')

tree.heading('Description', text='Descripción')
tree.heading('Symbol', text='Símbolo')
tree.heading('Currency', text='Moneda')
tree.heading('Quantity', text='Cantidad')
tree.heading('MarkPrice', text='Precio de Mercado')
tree.heading('Multiplier', text='Multiplicador')
tree.heading('Beta', text='Beta')
tree.heading('Delta', text='Delta')

# Configurar columnas
for col in ('Description', 'Symbol', 'Currency', 'Quantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'):
    tree.column(col, anchor="center", stretch=True)

# Estilos
style = ttk.Style()
style.configure('TTreeview', font=('Helvetica', 10))
style.configure('TTreeview.Heading', font=('Helvetica', 12, 'bold'))
tree.tag_configure('title', font=('Helvetica', 12, 'bold'))
tree.tag_configure('normal', font=('Helvetica', 10))

tree.pack(expand=True, fill="both")

# === Insertar posiciones en tabla ===
def insert_positions_by_asset_class():
    tree.delete(*tree.get_children())

    asset_class_titles = {
        'FOP': "Opciones sobre futuros",
        'OPT': "Opciones",
        'FUT': "Futuros",
        'STK': "Acciones"
    }

    for asset_class, title in asset_class_titles.items():
        tree.insert('', 'end', text=title, values=('', '', '', '', '', '', '', ''), tags=("title",))

        for _, row in positions[positions['AssetClass'] == asset_class].iterrows():
            include_img = check_on if row["Include"] else check_off
            tree.insert('', 'end',
                        text='',  # columna #0
                        image=include_img,
                        values=(row['Description'], row['Symbol'], row['CurrencyPrimary'],
                                f"{row['Quantity']:.2f}", f"{row['MarkPrice']:.2f}",
                                f"{row['Multiplier']:.2f}" if pd.notna(row['Multiplier']) else '',
                                f"{row['Beta']:.2f}" if pd.notna(row['Beta']) else '',
                                f"{row['Delta']:.3f}" if pd.notna(row['Delta']) else ''),
                        tags=("normal",))

# === Función para alternar inclusión ===
def toggle_include(event):
    item_id = tree.identify_row(event.y)
    col = tree.identify_column(event.x)
    if not item_id or col != "#0":
        return
    values = tree.item(item_id, "values")
    if not values or not values[0]:
        return
    description = values[0]
    idx = positions["Description"] == description
    if idx.any():
        positions.loc[idx, "Include"] = ~positions.loc[idx, "Include"].values
        insert_positions_by_asset_class()

tree.bind("<Button-1>", toggle_include)

# === Cálculo de exposición ===
def calculate_exposure():
    global fx_exchange
    global positions

    positions = fill_market_price(positions)
    positions_to_use = positions[positions["Include"]]

    individual_exposures, total_exposure = portfolio_exposure(positions_to_use)

    data = yf.Ticker("ES=F")
    current_price_fut = data.history(period="1d")["Close"].iloc[-1]
    beta = float(betas[betas["UnderlyingSymbol"] == "ES=F"]["Beta"])
    fx_exchange_rate = fx_exchange[fx_exchange["CurrencyPrimary"] == "USD"]["FX_Exchange"].values[0]
    MES_exposure = current_price_fut * fx_exchange_rate * 5 * beta

    total_absolute_exposure = individual_exposures["Exposure"].abs().sum()
    grouped_by_direction = individual_exposures.groupby(by="Direction").sum().reset_index()
    long_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Long"]["Exposure"]))
    short_absolute = float(abs(grouped_by_direction[grouped_by_direction.Direction == "Short"]["Exposure"]))
    pct_short = 100 * short_absolute / total_absolute_exposure
    pct_long = 100 * long_absolute / total_absolute_exposure

    results_text.set(f"Total exposure: {total_exposure:,.2f} EUR\n"
                     f"Total exposure in MES: {total_exposure / float(MES_exposure):,.2f} MES\n"
                     f"Position short: {pct_short:,.2f} %\n"
                     f"Position long: {pct_long:,.2f} %")

    insert_positions_by_asset_class()

# === Botón de cálculo ===
calculate_button = tk.Button(root, text="Calcular", command=calculate_exposure,
                             font=("Helvetica", 12, "bold"), bg="lightblue")
calculate_button.pack(pady=10)

# === Etiqueta de resultados ===
results_text = tk.StringVar()
results_label = tk.Label(root, textvariable=results_text, font=("Helvetica", 12))
results_label.pack(pady=10)

# Mostrar tabla inicial
insert_positions_by_asset_class()

# Iniciar GUI
root.mainloop()
