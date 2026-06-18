import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Electro M - Sistema", layout="wide")

# --- CONFIGURACIÓN DE BASE DE DATOS (SQLite) ---
def conectar_db():
    conn = sqlite3.connect("presupuestos.db")
    cursor = conn.cursor()
    # Tabla principal de presupuestos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            direccion TEXT,
            fecha TEXT,
            observaciones TEXT,
            total REAL
        )
    ''')
    # Tabla secundaria para los ítems de cada presupuesto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items_presupuesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presupuesto_id INTEGER,
            servicio TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            subtotal REAL,
            FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = conectar_db()

# --- MANEJO DE ESTADOS EN STREAMLIT ---
if 'lista' not in st.session_state: st.session_state.lista = []
if 'editando_id' not in st.session_state: st.session_state.editando_id = None
if 'cliente_val' not in st.session_state: st.session_state.cliente_val = ""
if 'dir_val' not in st.session_state: st.session_state.dir_val = ""
if 'obs_val' not in st.session_state: st.session_state.obs_val = ""

# --- CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["⚡ Creador de Presupuestos", "📂 Historial y Base de Datos"])

# ==========================================
# PESTAÑA 1: CREADOR
# ==========================================
with tab1:
    if st.session_state.editando_id:
        st.warning(f"⚠️ Estás editando el Presupuesto ID: {st.session_state.editando_id}")
        if st.button("❌ Cancelar Edición (Limpiar)"):
            st.session_state.editando_id = None
            st.session_state.lista = []
            st.session_state.cliente_val = ""
            st.session_state.dir_val = ""
            st.session_state.obs_val = ""
            st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        cliente = st.text_input("Nombre del Cliente", value=st.session_state.cliente_val, key="input_cliente")
        dir = st.text_input("Dirección", value=st.session_state.dir_val, key="input_dir")
        fecha = st.date_input("Fecha").strftime("%d/%m/%Y")
        detalle = st.text_area("Observaciones", value=st.session_state.obs_val, key="input_obs")
        
        st.write("---")
        d = st.text_input("Servicio")
        c = st.number_input("Cantidad", min_value=1, value=1)
        p = st.number_input("Precio Unitario ($)", min_value=0, value=0)
        
        if st.button("➕ Agregar a Servicios"):
            st.session_state.lista.append({"d": d, "c": c, "p": p, "s": c*p})
            st.rerun()
            
        st.write("### 🛠️ Lista de Servicios Cargados")
        if len(st.session_state.lista) == 0:
            st.write("*No hay servicios cargados aún.*")
        else:
            for index, item in enumerate(st.session_state.lista):
                col_item, col_btn = st.columns([0.85, 0.15])
                with col_item:
                    st.write(f"**{item['d']}** ({item['c']} x ${item['p']:,.0f}) = ${item['s']:,.0f}")
                with col_btn:
                    if st.button("❌", key=f"borrar_{index}"):
                        st.session_state.lista.pop(index)
                        st.rerun()

        st.write("---")
        col_guardar, col_borrar = st.columns([1, 1])
        
        with col_guardar:
            # BOTÓN PARA GUARDAR EN LA BASE DE DATOS
            if st.button("💾 Guardar en Base de Datos", type="primary"):
                if not cliente:
                    st.error("Por favor, ingresá al menos el nombre del cliente.")
                elif len(st.session_state.lista) == 0:
                    st.error("Agregá al menos un servicio antes de guardar.")
                else:
                    total_p = sum(i['s'] for i in st.session_state.lista)
                    
                    if st.session_state.editando_id:
                        # Modo Edición: Actualizar registro existente
                        cursor.execute('''
                            UPDATE presupuestos SET cliente=?, direccion=?, fecha=?, observaciones=?, total=? WHERE id=?
                        ''', (cliente, dir, fecha, detalle, total_p, st.session_state.editando_id))
                        
                        # Borrar items viejos y meter los nuevos
                        cursor.execute('DELETE FROM items_presupuesto WHERE presupuesto_id=?', (st.session_state.editando_id,))
                        p_id = st.session_state.editando_id
                    else:
                        # Modo Nuevo: Insertar de cero
                        cursor.execute('''
                            INSERT INTO presupuestos (cliente, direccion, fecha, observaciones, total) VALUES (?, ?, ?, ?, ?)
                        ''', (cliente, dir, fecha, detalle, total_p))
                        p_id = cursor.lastrowid
                    
                    # Insertar los ítems de la lista
                    for i in st.session_state.lista:
                        cursor.execute('''
                            INSERT INTO items_presupuesto (presupuesto_id, servicio, cantidad, precio_unitario, subtotal)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (p_id, i['d'], i['c'], i['p'], i['s']))
                    
                    conn.commit()
                    st.success("¡Presupuesto guardado con éxito en el Historial!")
                    
                    # Limpiar todo después de guardar
                    st.session_state.editando_id = None
                    st.session_state.lista = []
                    st.session_state.cliente_val = ""
                    st.session_state.dir_val = ""
                    st.session_state.obs_val = ""
                    st.rerun()
                    
        with col_borrar:
            if st.button("🗑️ Borrar toda la lista"):
                st.session_state.lista = []
                st.rerun()

    # Renderizado HTML para la Tarjeta de Vista Previa
    filas = "".join([
        f'''<div style="display:flex; padding:8px 0; border-bottom:1px solid #eee; font-size: 11px; align-items: center;">
            <span style="flex: 1.8; word-break: break-word;">{i["d"]}</span>
            <span style="flex: 0.5; text-align: center;">{i["c"]}</span>
            <span style="flex: 0.9; text-align: right;">${i["p"]:,.0f}</span>
            <span style="flex: 1; text-align: right; font-weight: bold;">${i["s"]:,.0f}</span>
        </div>''' 
        for i in st.session_state.lista
    ])

    total = sum(i['s'] for i in st.session_state.lista)

    encabezado_html = ""
    if os.path.exists("encabezado.jpg"):
        with open("encabezado.jpg", "rb") as f:
            encabezado_html = f'<img src="data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}" style="width:100%; display:block; border-radius: 4px 4px 0 0;">'

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

# ==========================================
# PESTAÑA 2: HISTORIAL Y BASE DE DATOS
# ==========================================
with tab2:
    st.write("### 📂 Presupuestos Guardados")
    
    # Traer todos los presupuestos ordenados por el último guardado
    cursor.execute("SELECT id, cliente, direccion, fecha, total, observaciones FROM presupuestos ORDER BY id DESC")
    db_presupuestos = cursor.fetchall()
    
    if len(db_presupuestos) == 0:
        st.write("*No hay ningún presupuesto registrado en la base de datos todavía.*")
    else:
        for p in db_presupuestos:
            p_id, p_cliente, p_dir, p_fecha, p_total, p_obs = p
            
            # Formato estético para cada registro en el historial
            with st.container():
                col_info, col_acciones = st.columns([0.7, 0.3])
                
                with col_info:
                    st.write(f"### 👤 {p_cliente} — Total: **${p_total:,.0f}**")
                    st.write(f"📅 **Fecha:** {p_fecha} | 📍 **Dirección:** {p_dir if p_dir else 'No especificada'}")
                    if p_obs:
                        st.text(f"📝 Obs: {p_obs}")
                
                with col_acciones:
                    st.write("") # Espaciador visual
                    c_edit, c_del = st.columns(2)
                    
                    with c_edit:
                        # ACCIÓN: EDITAR Y TRAER DE VUELTA
                        if st.button("✏️ Editar", key=f"edit_db_{p_id}"):
                            # Cargar datos del cliente al session_state
                            st.session_state.editando_id = p_id
                            st.session_state.cliente_val = p_cliente
                            st.session_state.dir_val = p_dir
                            st.session_state.obs_val = p_obs
                            
                            # Traer los servicios de la subtabla
                            cursor.execute("SELECT servicio, cantidad, precio_unitario, subtotal FROM items_presupuesto WHERE presupuesto_id=?", (p_id,))
                            items_db = cursor.fetchall()
                            
                            st.session_state.lista = []
                            for row in items_db:
                                st.session_state.lista.append({"d": row[0], "c": row[1], "p": row[2], "s": row[3]})
                            
                            st.success("¡Cargado en el creador! Volvé a la pestaña de arriba para modificarlo.")
                            st.rerun()
                            
                    with c_del:
                        # ACCIÓN: ELIMINAR REGISTRO
                        if st.button("🗑️ Eliminar", key=f"del_db_{p_id}"):
                            # Al usar ON DELETE CASCADE, borra también sus ítems automáticamente
                            cursor.execute("DELETE FROM presupuestos WHERE id=?", (p_id,))
                            conn.commit()
                            st.error(f"Presupuesto de {p_cliente} eliminado.")
                            st.rerun()
            st.write("---")

conn.close()