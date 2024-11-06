import streamlit as st
import pandas as pd
from io import BytesIO

# Cargar archivos privados de manera segura
@st.cache_data
def load_private_files():
    maestro_moleculas_df = pd.read_excel('Maestro_Moleculas.xlsx')
    inventario_api_df = pd.read_excel('Inventario.xlsx')
    return maestro_moleculas_df, inventario_api_df

# Función para procesar el archivo de faltantes y generar el resultado
def procesar_faltantes(faltantes_df, maestro_moleculas_df, inventario_api_df):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    maestro_moleculas_df.columns = maestro_moleculas_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    # Usando las columnas como vienen en el archivo de faltantes
    cur_faltantes = faltantes_df['cur'].unique()
    faltante_faltantes = faltantes_df['faltante'].unique()

    alternativas_df = maestro_moleculas_df[maestro_moleculas_df['cur'].isin(cur_faltantes)]

    alternativas_inventario_df = pd.merge(
        alternativas_df,
        inventario_api_df,
        on='cur',
        how='inner',
        suffixes=('_alternativas', '_inventario')
    )

    alternativas_disponibles_df = alternativas_inventario_df[
        (alternativas_inventario_df['cantidad'] > 0) &
        (alternativas_inventario_df['codart_alternativas'].isin(faltante_faltantes))
    ]

    columnas_deseadas = [
        'codart_alternativas', 'cur', 'opcion_inventario', 'codart_inventario', 'cantidad', 'bodega'
    ]
    columnas_presentes = [col for col in columnas_deseadas if col in alternativas_disponibles_df.columns]
    alternativas_disponibles_df = alternativas_disponibles_df[columnas_presentes]

    alternativas_disponibles_df.rename(columns={
        'codart_alternativas': 'faltante',
        'opcion_inventario': 'opcion_alternativa',
        'codart_inventario': 'codart_alternativa'
    }, inplace=True)

    resultado_final_df = pd.merge(
        faltantes_df[['cur', 'faltante']],
        alternativas_disponibles_df,
        left_on=['cur', 'faltante'],
        right_on=['cur', 'faltante'],
        how='inner'
    )

    return resultado_final_df

# Streamlit UI
st.title('Generador de Alternativas de Faltantes')

uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type="xlsx")

if uploaded_file:
    faltantes_df = pd.read_excel(uploaded_file)
    maestro_moleculas_df, inventario_api_df = load_private_files()

    resultado_final_df = procesar_faltantes(faltantes_df, maestro_moleculas_df, inventario_api_df)

    if not resultado_final_df.empty:
        st.write("Archivo procesado correctamente.")
        st.dataframe(resultado_final_df)

        # Guardar el archivo generado en memoria para descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado_final_df.to_excel(writer, index=False)
        output.seek(0)

        # Botón para descargar el archivo
        st.download_button(
            label="Descargar archivo de alternativas",
            data=output,
            file_name='alternativas_disponibles.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.warning("No se encontraron alternativas disponibles.")
