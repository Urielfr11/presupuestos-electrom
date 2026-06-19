import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import os
import base64
import time
from datetime import datetime

st.set_page_config(page_title="Electro M - Sistema", layout="wide")

# ==========================================
# SISTEMA DE CONTROL DE ACCESO (LOGIN)
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.markdown("""
        <style>
        .login-box {
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔒 Acceso Seguro - Electro M")
    st.write("Por favor, ingresá tus credenciales para administrar los presupuestos.")
    
    col_login, _ = st.columns([1, 1.5])
    
    with col_login:
        user_input = st.text_input("Usuario", placeholder="Ingresá tu usuario")
        pass_input = st.text_input("Contraseña", type="password", placeholder="Ingresá tu contraseña")
        
        if st.button("🚀 Iniciar Sesión", type="primary"):
            if user_input == "ElectroM" and pass_input == "ElectroM":
                st.session_state.autenticado = True
                st.success("¡Acceso concedido!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos. Intentá de nuevo.")

# Si no está autenticado, frena la ejecución acá y muestra la pantalla de login
if not st.session_state.autenticado:
    login()
else:
    # ==========================================
    # CONFIGURACIÓN DE ENLACES (MÓDULO DE TRABAJO)
    # ==========================================
    SPREADSHEET_ID = "1nejjCKHxaBr-_mxZQjqi2UvuD5erGPljR78ZyeWvuUA"
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyNLQ1TvOP3xZ24nN9zAHyVWHedBRuNsbky_XdW5xkZ41uFUHEOmzj9WHOj6KJtG3fm/exec"

    def leer_datos():
        columnas_p = ["id", "cliente", "direccion", "fecha", "observaciones", "total", "estado", "telefono"]
        columnas_i = ["id", "presupuesto_id", "servicio", "cantidad", "precio_unitario", "subtotal"]
        
        t = int(time.time())
        url_p = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=presupuestos&v={t}"
        url_i = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=items&v={t}"
        
        try:
            df_p = pd.read_csv(url_p)
            df_i = pd.read_csv(url_i)
            
            if not df_p.empty:
                df_p.columns = [str(c).strip().lower() for c in df_p.columns]
            if not df_i.empty:
                df_i.columns = [str(c).strip().lower() for c in df_i.columns]

            df_p = df_p.dropna(how="all")
            df_i = df_i.dropna(how="all")
            
            for col in columnas_p:
                if col not in df_p.columns: df_p[col] = ""
            for col in columnas_i:
                if col not in df_i.columns: df_i[col] = ""
                
            if not df_p.empty: 
                df_p['id'] = pd.to_numeric(df_p['id'], errors='coerce').fillna(0).astype(int)
            if not df_i.empty: 
                df_i['id'] = pd.to_numeric(df_i['id'], errors='coerce').fillna(0).astype(int)
                df_i['presupuesto_id'] = pd.to_numeric(df_i['presupuesto_id'], errors='coerce').fillna(0).astype(int)
                
        except Exception:
            df_p = pd.DataFrame(columns=columnas_p)
            df_i = pd.DataFrame(columns=columnas_i)
        return df_p, df_i

    # --- BOTÓN DE CERRAR SESIÓN EN LA BARRA LATERAL ---
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # --- MANEJO DE ESTADOS ---
    if 'lista' not in st.session_state: st.session_state.lista = []
    if 'editando_id' not in st.session_state: st.session_state.editando_id = None
    if 'cliente_val' not in st.session_state: st.session_state.cliente_val = ""
    if 'dir_val' not in st.session_state: st.session_state.dir_val = ""
    if 'tel_val' not in st.session_state: st.session_state.tel_val = ""
    if 'obs_val' not in st.session_state: st.session_state.obs_val = ""
    
    if 'index_servicio_editando' not in st.session_state: st.session_state.index_servicio_editando = None
    if 'servicio_input_val' not in st.session_state: st.session_state.servicio_input_val = ""
    if 'cantidad_input_val' not in st.session_state: st.session_state.cantidad_input_val = 1
    if 'precio_input_val' not in st.session_state: st.session_state.precio_input_val = 0

    # --- CONTROLADOR DEL MENÚ ---
    opciones_menu = ["⚡ Creador", "📂 Historial"]
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = "⚡ Creador"

    menu = st.sidebar.radio("Ir a:", opciones_menu, index=opciones_menu.index(st.session_state.pagina_actual))
    st.session_state.pagina_actual = menu

    # ==========================================
    # PANTALLA: CREADOR
    # ==========================================
    if st.session_state.pagina_actual == "⚡ Creador":
        st.title("⚡ Creador de Presupuestos")
        
        if st.session_state.editando_id:
            st.warning(f"⚠️ Estás editando el Presupuesto ID: {st.session_state.editando_id}")
            if st.button("❌ Cancelar Edición del Presupuesto (Limpiar)"):
                st.session_state.editando_id = None
                st.session_state.lista = []
                st.session_state.cliente_val = ""
                st.session_state.dir_val = ""
                st.session_state.tel_val = ""
                st.session_state.obs_val = ""
                st.session_state.index_servicio_editando = None
                st.session_state.servicio_input_val = ""
                st.session_state.cantidad_input_val = 1
                st.session_state.precio_input_val = 0
                st.rerun()

        col1, col2 = st.columns([1, 1])

        with col1:
            sufijo_key = f"edit_{st.session_state.editando_id}" if st.session_state.editando_id else "nuevo"
            
            cliente = st.text_input("Nombre del Cliente", value=st.session_state.cliente_val, key=f"inp_cli_{sufijo_key}")
            dir = st.text_input("Dirección", value=st.session_state.dir_val, key=f"inp_dir_{sufijo_key}")
            tel = st.text_input("Teléfono / WhatsApp", value=st.session_state.tel_val, key=f"inp_tel_{sufijo_key}", placeholder="Ej: 3434567890")
            fecha = st.date_input("Fecha").strftime("%d/%m/%Y")
            detalle = st.text_area("Observaciones", value=st.session_state.obs_val, key=f"inp_obs_{sufijo_key}")
            
            st.session_state.cliente_val = cliente
            st.session_state.dir_val = dir
            st.session_state.tel_val = tel
            st.session_state.obs_val = detalle
            
            st.write("---")
            
            if st.session_state.index_servicio_editando is not None:
                st.info(f"✍️ Editando servicio en la lista (Ítem {st.session_state.index_servicio_editando + 1})")
            
            d = st.text_input("Servicio", value=st.session_state.servicio_input_val)
            c = st.number_input("Cantidad", min_value=1, value=st.session_state.cantidad_input_val)
            p = st.number_input("Precio Unitario ($)", min_value=0, value=st.session_state.precio_input_val)
            
            st.session_state.servicio_input_val = d
            st.session_state.cantidad_input_val = c
            st.session_state.precio_input_val = p

            col_btn_agregar, col_btn_cancelar_ser = st.columns([1, 1])
            
            with col_btn_agregar:
                if st.session_state.index_servicio_editando is not None:
                    if st.button("💾 Actualizar Servicio", type="secondary"):
                        idx = st.session_state.index_servicio_editando
                        st.session_state.lista[idx] = {"d": d, "c": c, "p": p, "s": c*p}
                        st.session_state.index_servicio_editando = None
                        st.session_state.servicio_input_val = ""
                        st.session_state.cantidad_input_val = 1
                        st.session_state.precio_input_val = 0
                        st.rerun()
                else:
                    if st.button("➕ Agregar a Servicios"):
                        st.session_state.lista.append({"d": d, "c": c, "p": p, "s": c*p})
                        st.session_state.servicio_input_val = ""
                        st.session_state.cantidad_input_val = 1
                        st.session_state.precio_input_val = 0
                        st.rerun()
            
            with col_btn_cancelar_ser:
                if st.session_state.index_servicio_editando is not None:
                    if st.button("❌ Cancelar Modificación"):
                        st.session_state.index_servicio_editando = None
                        st.session_state.servicio_input_val = ""
                        st.session_state.cantidad_input_val = 1
                        st.session_state.precio_input_val = 0
                        st.rerun()
                        
            st.write("### 🛠️ Lista de Servicios Cargados")
            if len(st.session_state.lista) == 0:
                st.write("*No hay servicios cargados aún.*")
            else:
                for index, item in enumerate(st.session_state.lista):
                    col_item, col_btn_edit, col_btn_del = st.columns([0.70, 0.15, 0.15])
                    with col_item:
                        texto_item = f"**{item['d']}** ({item['c']} x ${item['p']:,.0f}) = ${item['s']:,.0f}"
                        st.write(texto_item.replace(",", "."))
                    with col_btn_edit:
                        if st.button("✏️", key=f"editar_item_{index}"):
                            st.session_state.index_servicio_editando = index
                            st.session_state.servicio_input_val = item['d']
                            st.session_state.cantidad_input_val = item['c']
                            st.session_state.precio_input_val = item['p']
                            st.rerun()
                    with col_btn_del:
                        if st.button("❌", key=f"borrar_{index}"):
                            st.session_state.lista.pop(index)
                            if st.session_state.index_servicio_editando == index:
                                st.session_state.index_servicio_editando = None
                                st.session_state.servicio_input_val = ""
                                st.session_state.cantidad_input_val = 1
                                st.session_state.precio_input_val = 0
                            st.rerun()

            st.write("---")
            col_guardar, col_borrar = st.columns([1, 1])
            
            with col_guardar:
                if st.button("💾 Guardar Presupuesto", type="primary"):
                    if not cliente:
                        st.error("Por favor, ingresá al menos el nombre del cliente.")
                    elif len(st.session_state.lista) == 0:
                        st.error("Agregá al menos un servicio antes de guardar.")
                    else:
                        with st.spinner("Sincronizando con la nube..."):
                            df_p, df_i = leer_datos()
                            total_p = sum(i['s'] for i in st.session_state.lista)
                            
                            is_edit = st.session_state.editando_id is not None
                            p_id = int(st.session_state.editando_id) if is_edit else (int(df_p['id'].max() + 1) if len(df_p) > 0 else 1)
                            estado_actual = st.session_state.get('estado_edicion_temp', '⏳ Pendiente')

                            paquete_presupuesto = {
                                "id": p_id, "cliente": cliente, "direccion": dir, "telefono": tel,
                                "fecha": fecha, "observaciones": detalle, "total": total_p, "estado": estado_actual
                            }
                            
                            paquete_items = []
                            base_item_id = int(df_i['id'].max() + 1) if len(df_i) > 0 else 1
                            for idx, i in enumerate(st.session_state.lista):
                                paquete_items.append({
                                    "id": base_item_id + idx, "presupuesto_id": p_id, "servicio": i['d'],
                                    "cantidad": i['c'], "precio_unitario": i['p'], "subtotal": i['s']
                                })
                            
                            payload = {
                                "tipo": "guardar",
                                "editando": is_edit,
                                "presupuesto": paquete_presupuesto,
                                "items": paquete_items
                            }
                            
                            respuesta = requests.post(WEBAPP_URL, data=json.dumps(payload))
                            
                            if respuesta.status_code == 200:
                                st.success("¡Presupuesto guardado en la nube con éxito!")
                                st.session_state.editando_id = None
                                st.session_state.lista = []
                                st.session_state.cliente_val = ""
                                st.session_state.dir_val = ""
                                st.session_state.tel_val = ""
                                st.session_state.obs_val = ""
                                st.session_state.index_servicio_editando = None
                                st.session_state.servicio_input_val = ""
                                st.session_state.cantidad_input_val = 1
                                st.session_state.precio_input_val = 0
                                st.rerun()
                            else:
                                st.error("Hubo un error de conexión con la Web App de Google.")
                        
            with col_borrar:
                if st.button("🗑️ Borrar toda la lista"):
                    st.session_state.lista = []
                    st.session_state.index_servicio_editando = None
                    st.session_state.servicio_input_val = ""
                    st.session_state.cantidad_input_val = 1
                    st.session_state.precio_input_val = 0
                    st.rerun()

        # --- PREVISUALIZACIÓN DE LA PLANTILLA CON ALINEACIONES Y ANCHOS CORRECTOS ---
        filas = "".join([
            f'''<div style="display:flex; padding:8px 0; border-bottom:1px solid #eee; font-size: 11px; align-items: center;">
                <span style="flex: 2.3; word-break: break-word; text-align: left;">{i["d"]}</span>
                <span style="flex: 0.4; text-align: center;">{i["c"]}</span>
                <span style="flex: 0.7; text-align: right;">${i["p"]:,.0f}</span>
                <span style="flex: 0.8; text-align: right; font-weight: bold;">${i["s"]:,.0f}</span>
            </div>'''.replace(",", ".") 
            for i in st.session_state.lista
        ])

        total = sum(i['s'] for i in st.session_state.lista)
        total_formateado = f"${total:,.0f}".replace(",", ".")

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
                    .replace("__TABLA__", filas).replace("__TOTAL__", total_formateado)\
                    .replace("__DETALLE__", detalle).replace("__PIE__", pie_html)
            
            with col2:
                components.html(html, height=1100, scrolling=True)

    # ==========================================
    # PANTALLA: HISTORIAL
    # ==========================================
    elif st.session_state.pagina_actual == "📂 Historial":
        st.title("📂 Historial Sincronizado (Google Sheets)")
        
        with st.spinner("Cargando datos desde la nube..."):
            df_presupuestos, df_items = leer_datos()
        
        filtro_estado = st.segmented_control(
            "Filtrar por estado:",
            options=["Todos", "⏳ Pendiente", "✅ Aprobado", "💵 Cobrado"],
            default="Todos"
        )
        st.write("---")

        if df_presupuestos.empty or 'cliente' not in df_presupuestos.columns:
            st.write("*No se encontraron presupuestos en la nube todavía. ¡Cargá el primero desde el creador!*")
        else:
            df_presupuestos = df_presupuestos.sort_values(by="id", ascending=False)
            
            for _, row in df_presupuestos.iterrows():
                p_id = int(row['id']) if pd.notna(row['id']) and str(row['id']).isdigit() else 0
                if p_id == 0: continue
                
                p_cliente = str(row['cliente'])
                p_dir = str(row['direccion']) if pd.notna(row['direccion']) else ""
                p_fecha = str(row['fecha']) if pd.notna(row['fecha']) else ""
                p_total = float(row['total']) if pd.notna(row['total']) and str(row['total']).replace('.','',1).isdigit() else 0.0
                p_obs = str(row['observaciones']) if pd.notna(row['observaciones']) else ""
                p_estado = str(row['estado']) if pd.notna(row['estado']) else "⏳ Pendiente"
                
                p_tel = ""
                if 'telefono' in row and pd.notna(row['telefono']):
                    p_tel = str(row['telefono']).strip()
                    if p_tel.endswith('.0'):
                        p_tel = p_tel[:-2]
                
                if filtro_estado != "Todos" and p_estado != filtro_estado:
                    continue

                with st.container():
                    col_info, col_acciones = st.columns([0.65, 0.35])
                    
                    with col_info:
                        color_estado = "orange" if "Pendiente" in p_estado else ("green" if "Aprobado" in p_estado else "blue")
                        
                        texto_titulo = f"### {p_cliente} — Total: **${p_total:,.0f}**"
                        st.write(texto_titulo.replace(",", "."))
                        
                        st.markdown(f"**Estado:** :{color_estado}[**{p_estado}**]")
                        
                        info_contacto = f"**Fecha:** {p_fecha}"
                        if p_dir: info_contacto += f"  |  **Dirección:** {p_dir}"
                        if p_tel: info_contacto += f"  |  **Teléfono:** {p_tel}"
                        st.write(info_contacto)
                        
                        if p_obs:
                            st.text(f"📝 Obs: {p_obs}")
                    
                    with col_acciones:
                        st.write("**Cambiar Estado:**")
                        c_pend, c_aprob, c_cobr = st.columns(3)
                        
                        def cambiar_estado_cloud(id_target, nuevo_estado):
                            requests.post(WEBAPP_URL, data=json.dumps({"tipo": "cambiar_estado", "id": id_target, "nuevo_estado": nuevo_estado}))
                            st.rerun()

                        with c_pend:
                            if st.button("⏳", key=f"st_pend_{p_id}"):
                                cambiar_estado_cloud(p_id, '⏳ Pendiente')
                        with c_aprob:
                            if st.button("✅", key=f"st_aprob_{p_id}"):
                                cambiar_estado_cloud(p_id, '✅ Aprobado')
                        with c_cobr:
                            if st.button("💵", key=f"st_cobr_{p_id}"):
                                cambiar_estado_cloud(p_id, '💵 Cobrado')
                        
                        st.write("---")
                        c_edit, c_del = st.columns(2)
                        
                        with c_edit:
                            if st.button("✏️ Editar", key=f"edit_db_{p_id}"):
                                st.session_state.editando_id = p_id
                                st.session_state.cliente_val = p_cliente
                                st.session_state.dir_val = p_dir
                                st.session_state.tel_val = p_tel
                                st.session_state.obs_val = p_obs
                                st.session_state.estado_edicion_temp = p_estado
                                
                                if not df_items.empty and 'presupuesto_id' in df_items.columns:
                                    items_p = df_items[df_items['presupuesto_id'] == p_id]
                                    st.session_state.lista = []
                                    for _, it in items_p.iterrows():
                                        st.session_state.lista.append({
                                            "d": str(it['servicio']) if 'servicio' in df_items.columns else "", 
                                            "c": int(it['cantidad']) if 'cantidad' in df_items.columns else 1, 
                                            "p": float(it['precio_unitario']) if 'precio_unitario' in df_items.columns else 0.0, 
                                            "s": float(it['subtotal']) if 'subtotal' in df_items.columns else 0.0
                                        })
                                st.session_state.pagina_actual = "⚡ Creador"
                                st.rerun()
                                
                        with c_del:
                            if st.button("🗑️ Eliminar", key=f"del_db_{p_id}"):
                                requests.post(WEBAPP_URL, data=json.dumps({"tipo": "eliminar", "id": p_id}))
                                st.rerun()
                st.write("---")