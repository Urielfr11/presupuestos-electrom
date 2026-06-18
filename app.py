import streamlit as st
import streamlit.components.v1 as components
import os
import base64

st.set_page_config(page_title="Electro M - Presupuestos", layout="wide")

if 'lista' not in st.session_state: st.session_state.lista = []

st.title("⚡ Electro M - Creador")

col1, col2 = st.columns([1, 1])

with col1:
    cliente = st.text_input("Nombre del Cliente", "Eliana - Ariel")
    dir = st.text_input("Dirección", "Pedro de Mendoza 2254, Paraná")
    fecha = st.date_input("Fecha").strftime("%d/%m/%Y")
    detalle = st.text_area("Observaciones", "Instalación de bocas, cableado y armado de tableros.")
    
    st.write("---")
    d = st.text_input("Servicio")
    c = st.number_input("Cantidad", 1)
    p = st.number_input("Precio Unitario ($)", 0.0)
    
    if st.button("➕ Agregar a Servicios"):
        st.session_state.lista.append({"d": d, "c": c, "s": c*p})
        st.rerun()
        
    if st.button("🗑️ Borrar toda la lista"):
        st.session_state.lista = []
        st.rerun()

filas = "".join([
    f'''<div style="display:flex; padding:8px 0; border-bottom:1px solid #eee; font-size: 11px; align-items: center;">
        <span style="flex: 2; word-break: break-word;">{i["d"]}</span>
        <span style="flex: 0.7; text-align: center;">{i["c"]}</span>
        <span style="flex: 1.3; text-align: right; font-weight: bold;">${i["s"]:,.0f}</span>
    </div>''' 
    for i in st.session_state.lista
])

total = sum(i['s'] for i in st.session_state.lista)

# Cargar Imagen de Encabezado
encabezado_html = ""
if os.path.exists("encabezado.jpg"):
    with open("encabezado.jpg", "rb") as f:
        encabezado_html = f'<img src="data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}" style="width:100%; display:block; border-radius: 4px 4px 0 0;">'

# Cargar Imagen de Pie de Página
pie_html = ""
if os.path.exists("pie.jpg"):
    with open("pie.jpg", "rb") as f:
        pie_html = f'<img src="data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}" style="width:100%; display:block; border-radius: 0 0 4px 4px;">'

if os.path.exists("plantilla.html"):
    with open("plantilla.html", "r", encoding="utf-8") as f:
        html = f.read().replace("__ENCABEZADO__", encabezado_html).replace("__CLIENTE__", cliente)\
            .replace("__DIRECCION__", dir).replace("__FECHA__", fecha)\
            .replace("__TABLA__", filas).replace("__TOTAL__", f"${total:,.0f}")\
            .replace("__DETALLE__", detalle).replace("__PIE__", pie_html)
    
    with col2:
        components.html(html, height=1100, scrolling=True)