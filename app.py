import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.set_page_config(page_title="Electro M - Presupuestos", layout="wide")

if 'lista' not in st.session_state: st.session_state.lista = []

st.title("⚡ Electro M - Creador de Presupuestos")

col1, col2 = st.columns([1, 1])

with col1:
    cliente = st.text_input("Nombre del Cliente", "Eliana - Ariel")
    dir = st.text_input("Dirección", "Pedro de Mendoza 2254, Paraná")
    fecha = st.date_input("Fecha").strftime("%d/%m/%Y")
    detalle = st.text_area("Detalle del Proyecto", "Instalación de bocas, cableado y armado de tableros.")
    
    st.write("---")
    d = st.text_input("Concepto")
    c = st.number_input("Cantidad", 1)
    p = st.number_input("Precio Unitario ($)", 0.0)
    
    if st.button("➕ Agregar a la Lista"):
        st.session_state.lista.append({"d": d, "c": c, "s": c*p})
        st.rerun()
        
    if st.button("🗑️ Borrar toda la lista"):
        st.session_state.lista = []
        st.rerun()

# Generar filas con Flexbox para alinear
filas = "".join([
    f'''<div style="display:flex; padding:8px 0; border-bottom:1px solid #eee; font-size: 12px;">
        <span style="flex: 2;">{i["d"]}</span>
        <span style="flex: 0.5; text-align: center;">{i["c"]}</span>
        <span style="flex: 1; text-align: right;">${i["s"]:,.0f}</span>
    </div>''' 
    for i in st.session_state.lista
])

total = sum(i['s'] for i in st.session_state.lista)

# Logo
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        logo_html = f'<img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" style="width:125px; display:block;">'

# Rellenar y mostrar
if os.path.exists("plantilla.html"):
    with open("plantilla.html", "r", encoding="utf-8") as f:
        html = f.read().replace("__LOGO__", logo_html).replace("__CLIENTE__", cliente)\
            .replace("__DIRECCION__", dir).replace("__FECHA__", fecha)\
            .replace("__TABLA__", filas).replace("__TOTAL__", f"${total:,.0f}").replace("__DETALLE__", detalle)
    
    with col2:
        components.html(html, height=1000)