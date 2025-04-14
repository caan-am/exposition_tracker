import tkinter as tk
from tkinter import ttk
import pandas as pd
import yfinance as yf
from calc_exposure import *
from calc_other_inputs import *
from get_portfolio import *

# === Datos base ===
positions = get_current_portfolio()
positions_quintet = pd.read_excel("input/positions_quintet.xlsx")
positions = pd.concat([positions_quintet, positions], ignore_index=True)

positions["UnderlyingSymbol"].replace({
    "HEIA": "HEIA.AS", "BRK B": "BRK-B", "MES": "ES=F", "ESM5": "ES=F", "MC": "MC.PA", "SOI": "SOI.PA",
}, inplace=True)

positions = positions.groupby("Description").agg({
    "Symbol": "first", "CurrencyPrimary": "first", "AssetClass": "first", "Quantity": "sum",
    "MarkPrice": "first", "Multiplier": "first", "UnderlyingSymbol": "first"
}).reset_index()

positions = fill_market_price(positions)
betas = pd.read_csv("input/betas.csv")
positions = add_beta_to_portfolio(positions, betas)
fx_exchange = currency_to_eur(["USD", "EUR"])
positions = positions.merge(fx_exchange, on="CurrencyPrimary", how="left")

positions["Include"] = True
positions["ModifiedQuantity"] = positions["Quantity"]

deltas_temp = pd.read_excel("input/deltas.xlsx")
positions = positions.merge(deltas_temp, on="Description", how="left")

# === GUI ===
root = tk.Tk()
root.title("Cálculo de Exposición del Portfolio")
root.geometry("1200x650")

check_on = tk.PhotoImage(file="input/checkbox_checked.png")
check_off = tk.PhotoImage(file="input/checkbox_unchecked.png")

frame = tk.Frame(root)
frame.pack(expand=True, fill="both", padx=10, pady=10)

tree = ttk.Treeview(
    frame,
    columns=('Description', 'Symbol', 'Currency', 'Quantity', 'ModifiedQuantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'),
    show="tree headings"
)

tree.heading('#0', text='Incluir')
tree.column('#0', width=70, anchor='center')

tree.heading('Description', text='Descripción')
tree.heading('Symbol', text='Símbolo')
tree.heading('Currency', text='Moneda')
tree.heading('Quantity', text='Cantidad')
tree.heading('ModifiedQuantity', text='Cantidad Modificada')
tree.heading('MarkPrice', text='Precio de Mercado')
tree.heading('Multiplier', text='Multiplicador')
tree.heading('Beta', text='Beta')
tree.heading('Delta', text='Delta')

for col in ('Description', 'Symbol', 'Currency', 'Quantity', 'ModifiedQuantity', 'MarkPrice', 'Multiplier', 'Beta', 'Delta'):
    tree.column(col, anchor="center", stretch=True)

style = ttk.Style()
style.configure('TTreeview', font=('Helvetica', 10))
style.configure('TTreeview.Heading', font=('Helvetica', 12, 'bold'))
tree.tag_configure('title', font=('Helvetica', 12, 'bold'))
tree.tag_configure('normal', font=('Helvetica', 10))

tree.pack(expand=True, fill="both")

# Para cerrar Entry activo
current_edit_entry = None

def insert_positions_by_asset_class():
    global current_edit_entry
    if current_edit_entry:
        current_edit_entry.destroy()
        current_edit_entry = None

    tree.delete(*tree.get_children())
    titles = {'FOP': "Opciones sobre futuros", 'OPT': "Opciones", 'FUT': "Futuros", 'STK': "Acciones"}

    for asset_class, title in titles.items():
        tree.insert('', 'end', text=title, values=('', '', '', '', '', '', '', '', ''), tags=("title",))

        for _, row in positions[positions['AssetClass'] == asset_class].iterrows():
            include_img = check_on if row["Include"] else check_off
            tree.insert('', 'end',
                        text='', image=include_img,
                        values=(row['Description'], row['Symbol'], row['CurrencyPrimary'],
                                f"{row['Quantity']:.2f}",
                                f"{row['ModifiedQuantity']:.2f}",
                                f"{row['MarkPrice']:.2f}",
                                f"{row['Multiplier']:.2f}" if pd.notna(row['Multiplier']) else '',
                                f"{row['Beta']:.2f}" if pd.notna(row['Beta']) else '',
                                f"{row['Delta']:.3f}" if pd.notna(row['Delta']) else ''),
                        tags=("normal",))

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

def on_double_click(event):
    global current_edit_entry

    if current_edit_entry:
        current_edit_entry.destroy()
        current_edit_entry = None

    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return

    row_id = tree.identify_row(event.y)
    col_id = tree.identify_column(event.x)
    if not row_id or col_id != "#5":  # ModifiedQuantity
        return

    x, y, width, height = tree.bbox(row_id, col_id)
    values = tree.item(row_id, "values")
    if not values:
        return

    entry = tk.Entry(tree, justify="center", font=('Helvetica', 10))
    entry.place(x=x, y=y, width=width, height=height)
    entry.insert(0, values[4])
    current_edit_entry = entry

    def save_edit(event=None):
        nonlocal entry
        try:
            new_qty = float(entry.get())
            description = values[0]
            idx = positions["Description"] == description
            if idx.any():
                positions.loc[idx, "ModifiedQuantity"] = new_qty
        except ValueError:
            pass
        entry.destroy()
        current_edit_entry = None
        insert_positions_by_asset_class()

    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", save_edit)
    entry.focus()

tree.bind("<Double-1>", on_double_click)

def calculate_exposure():
    global current_edit_entry
    if current_edit_entry:
        current_edit_entry.destroy()
        current_edit_entry = None

    positions.fillna({"ModifiedQuantity": 0}, inplace=True)
    positions_to_use = positions[positions["Include"]].copy()
    positions_to_use["Quantity"] = positions_to_use["ModifiedQuantity"]

    individual_exposures, total_exposure = portfolio_exposure(positions_to_use)

    data = yf.Ticker("ES=F")
    current_price_fut = data.history(period="1d")["Close"].iloc[-1]
    beta = float(betas[betas["UnderlyingSymbol"] == "ES=F"]["Beta"])
    fx_rate = fx_exchange[fx_exchange["CurrencyPrimary"] == "USD"]["FX_Exchange"].values[0]
    MES_exposure = current_price_fut * fx_rate * 5 * beta

    total_abs = individual_exposures["Exposure"].abs().sum()
    grouped = individual_exposures.groupby("Direction").sum().reset_index()
    long_abs = float(abs(grouped[grouped.Direction == "Long"]["Exposure"]))
    short_abs = float(abs(grouped[grouped.Direction == "Short"]["Exposure"]))
    pct_short = 100 * short_abs / total_abs
    pct_long = 100 * long_abs / total_abs

    results_text.set(f"Total exposure: {total_exposure:,.2f} EUR\n"
                     f"Total exposure in MES: {total_exposure / float(MES_exposure):,.2f} MES\n"
                     f"Position short: {pct_short:,.2f} %\n"
                     f"Position long: {pct_long:,.2f} %")

    insert_positions_by_asset_class()

calculate_button = tk.Button(root, text="Calcular", command=calculate_exposure,
                             font=("Helvetica", 12, "bold"), bg="lightblue")
calculate_button.pack(pady=10)

results_text = tk.StringVar()
results_label = tk.Label(root, textvariable=results_text, font=("Helvetica", 12))
results_label.pack(pady=10)

insert_positions_by_asset_class()
root.mainloop()
