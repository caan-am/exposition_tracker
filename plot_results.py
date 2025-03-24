import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def plot_portfolio_profiles(perfiles_individuales, perfil_total, shocks=None):
    """
    Pinta los perfiles de cada producto y el perfil total de la cartera.
    
    Parámetros:
    - perfiles_individuales: Diccionario con los perfiles de cada producto.
    - perfil_total: Perfil total de la cartera.
    - shocks: Lista de variaciones porcentuales en el SP500.
    """
    if shocks is None:
        shocks = np.arange(-10, 10.25, 0.25)
    
    # Crear el gráfico
    plt.figure(figsize=(10, 6))
    
    # Graficar cada perfil individual con una línea discontinua
    for producto, perfil in perfiles_individuales.items():
        plt.plot(shocks, perfil, '--', label=f'Perfil de {producto}')
    
    # Graficar el perfil total con una línea más gruesa
    plt.plot(shocks, perfil_total, '-', linewidth=2, color='black', label='Perfil total de la cartera')
    
    # Configuración del gráfico
    plt.title('Perfil de Precios de la Cartera vs. Cambios en el SP500')
    plt.xlabel('Cambio en el SP500 (%)')
    plt.ylabel('Precio Simulado')
    plt.legend()
    plt.grid(True)
    plt.show()

def generate_variation_table(perfil_total, shocks=None):
    """
    Genera una tabla con los valores de `perfil_total` para diferentes cambios porcentuales en el SP500,
    desde -10% hasta +10% con incrementos de 0.25%.
    
    Parámetros:
    - perfil_total: Array con el perfil total de la cartera ya calculado.
    - shocks: Lista de variaciones porcentuales en el SP500 (si no se pasa, se genera automáticamente de -10% a +10% con incrementos de 0.25%).
    
    Retorna:
    - DataFrame con los valores de `perfil_total` para cada uno de los cambios porcentuales solicitados.
    """
    if shocks is None:
        # Generar los shocks en el rango de -10% a +10% con incrementos de 0.25%
        shocks = np.arange(-10, 10.25, 0.25)
    # Crear el DataFrame con los valores
    perfil_total_df = pd.DataFrame([perfil_total], columns=[f'{shock}%' for shock in shocks])
    
    return perfil_total_df