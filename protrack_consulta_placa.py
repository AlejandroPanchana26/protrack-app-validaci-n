import streamlit as st
import requests
import hashlib
import time

st.title("Consulta de Vehículo - Protrack")

# ==========================
# INGRESO DE DATOS
# ==========================
account = st.text_input("Usuario Protrack")
password = st.text_input("Password", type="password")
plate_to_search = st.text_input("Placa del vehículo")

if st.button("Consultar vehículo"):

    if not account or not password or not plate_to_search:
        st.warning("Debes completar todos los campos")
        st.stop()

    # ==========================
    # GENERAR TIMESTAMP
    # ==========================
    timestamp = str(int(time.time()))

    # ==========================
    # GENERAR SIGNATURE
    # ==========================
    md5_password = hashlib.md5(password.encode()).hexdigest()
    signature = hashlib.md5((md5_password + timestamp).encode()).hexdigest()

    # ==========================
    # LOGIN API
    # ==========================
    auth_url = "https://api.protrack365.com/api/authorization"

    auth_params = {
        "account": account,
        "time": timestamp,
        "signature": signature
    }

    auth_response = requests.get(auth_url, params=auth_params)
    auth_data = auth_response.json()

    if auth_data.get("code") != 0:
        st.error("Credenciales incorrectas")
        st.stop()

    token = auth_data["record"]["access_token"]

    # ==========================
    # OBTENER DISPOSITIVOS
    # ==========================
    device_url = "https://api.protrack365.com/api/device/list"

    device_params = {
        "access_token": token,
        "account": account
    }

    device_response = requests.get(device_url, params=device_params)
    device_data = device_response.json()

    devices = device_data.get("records", [])

    imei_found = None

    for device in devices:
        plate = device.get("platenumber")

        if plate and plate.upper() == plate_to_search.upper():
            imei_found = device.get("imei")
            break

    if not imei_found:
        st.error("No se encontró la placa en la cuenta")
        st.stop()

    # ==========================
    # CONSULTAR POSICIÓN
    # ==========================
    track_url = "https://api.protrack365.com/api/track"

    track_params = {
        "access_token": token,
        "imeis": imei_found
    }

    track_response = requests.get(track_url, params=track_params)
    track_data = track_response.json()

    records = track_data.get("records", [])

    if records:
        data = records[0]

        lat = data.get("latitude")
        lon = data.get("longitude")
        speed = data.get("speed")
        gps_time = data.get("gpstime")

        st.success("Vehículo encontrado")

        st.write("Latitud:", lat)
        st.write("Longitud:", lon)
        st.write("Velocidad:", speed)
        st.write("Hora GPS:", gps_time)

        st.map([{"lat": lat, "lon": lon}])

    else:
        st.warning("No hay datos de posición")