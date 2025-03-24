import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import mplcursors
import numpy as np
import matplotlib.pyplot as plt

def plot_portfolio_profiles(perfiles_individuales, perfil_total, sp500_current, shocks=None):
    """
    Pinta los perfiles de cada producto y el perfil total de la cartera con doble eje X.

    Parámetros:
    - perfiles_individuales: Diccionario con los perfiles de cada producto.
    - perfil_total: Perfil total de la cartera.
    - shocks: Lista de variaciones porcentuales en el SP500 (opcional).
    - sp500_ref: Valor inicial de referencia del SP500 (para el segundo eje X).
    """
    if shocks is None:
        shocks = np.arange(-10, 10.25, 0.25)  # Valores de shock en porcentaje
    
    # Convertir los shocks porcentuales en valores absolutos
    sp500_niveles = sp500_current * (1 + np.array(shocks)  / 100)

    # Crear la figura y el eje primario
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Graficar cada perfil individual con una línea discontinua
    for producto, perfil in perfiles_individuales.items():
        ax1.plot(shocks, perfil, '--', label=f'Perfil de {producto}')
        
    
    # Graficar el perfil total con una línea más gruesa
    ax1.plot(shocks, perfil_total, '-', linewidth=2, color='black', label='Perfil total de la cartera')

    # Configuración del eje primario (shocks en %)
    ax1.set_xlabel('Cambio en el SP500 (%)')
    ax1.set_ylabel('Precio Simulado')
    ax1.set_title('Perfil de Precios de la Cartera vs. Cambios en el SP500')
    ax1.set_yticks(np.linspace(min(perfil_total), max(perfil_total), num=15))
    ax1.set_xticks(np.arange(min(shocks), max(shocks) + 0.5, 0.5))
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)  # Mejora el grid con líneas punteadas

    # Crear el segundo eje X (valores absolutos del SP500)
    ax2 = ax1.twiny()
    ax2.set_xlim(ax1.get_xlim())  # Hacer coincidir los límites de los ejes X
    ax2.set_xticks(shocks)  # Usar los mismos ticks del primer eje
    ax2.set_xticklabels([f'{int(v)}' for v in sp500_niveles])  # Etiquetas en valores absolutos

    ax2.set_xlabel('Nivel Absoluto del SP500')



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