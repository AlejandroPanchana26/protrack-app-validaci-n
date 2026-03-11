import streamlit as st
import requests
import hashlib
import time
import pandas as pd

st.title("🚗 Consulta de Vehículos - Protrack")

# ==========================
# FUNCIONES
# ==========================

def login(account, password):

    timestamp = str(int(time.time()))

    md5_password = hashlib.md5(password.encode()).hexdigest()
    signature = hashlib.md5((md5_password + timestamp).encode()).hexdigest()

    url = "https://api.protrack365.com/api/authorization"

    params = {
        "account": account,
        "time": timestamp,
        "signature": signature
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("code") != 0:
        return None

    return data["record"]["access_token"]


def obtener_dispositivos(token, account):

    url = "https://api.protrack365.com/api/device/list"

    params = {
        "access_token": token,
        "account": account
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("records", [])


def obtener_posiciones(token, imeis):

    url = "https://api.protrack365.com/api/track"

    params = {
        "access_token": token,
        "imeis": ",".join(imeis)
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("records", [])


# ==========================
# INTERFAZ
# ==========================

account = st.text_input("Usuario Protrack")
password = st.text_input("Password", type="password")

if st.button("Consultar vehículos"):

    if not account or not password:
        st.warning("Debes ingresar usuario y contraseña")
        st.stop()

    st.info("Consultando datos...")

    token = login(account, password)

    if not token:
        st.error("Credenciales incorrectas")
        st.stop()

    dispositivos = obtener_dispositivos(token, account)

    if not dispositivos:
        st.warning("No hay dispositivos en la cuenta")
        st.stop()

    imeis = []
    placas = {}

    for d in dispositivos:

        imei = d.get("imei")
        plate = d.get("platenumber")

        if imei:
            imeis.append(imei)
            placas[imei] = plate

    posiciones = obtener_posiciones(token, imeis)

    tabla = []

    for p in posiciones:

        imei = p.get("imei")

        fila = {
            "IMEI": imei,
            "Placa": placas.get(imei),
            "Latitud": p.get("latitude"),
            "Longitud": p.get("longitude"),
            "Velocidad": p.get("speed"),
            "Fecha GPS": p.get("gpstime")
        }

        tabla.append(fila)

    df = pd.DataFrame(tabla)

    # ==========================
    # FILTRO
    # ==========================

    filtro = st.text_input("Filtrar por placa")

    if filtro:
        df = df[df["Placa"].str.contains(filtro.upper(), na=False)]

    # ==========================
    # ORDENAR
    # ==========================

    df = df.sort_values("Fecha GPS", ascending=False)

    st.success(f"Vehículos encontrados: {len(df)}")

    # ==========================
    # TABLA
    # ==========================

    st.dataframe(df, use_container_width=True)

    # ==========================
    # DESCARGA
    # ==========================

    csv = df.to_csv(index=False)

    st.download_button(
        "📥 Descargar CSV",
        csv,
        "vehiculos_protrack.csv",
        "text/csv"
    )