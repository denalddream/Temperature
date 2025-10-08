import socket
import struct
import time
import requests
import json
import random

def valid_coords(lat, lon):
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

def parse_coords(data):
    try:
        obj = json.loads(data.decode("utf-8").strip())
        if isinstance(obj, dict):
            lat = float(obj.get("lat"))
            lon = float(obj.get("lon", obj.get("lan")))
            if lon is not None:
                lon = float(lon)
                if valid_coords(lat, lon):
                    return lat, lon
    except Exception:
        pass
    try:
        text = data.decode("utf-8").strip()
        if "," in text:
            a, b = text.split(",", 1)
            lat = float(a)
            lon = float(b)
            if valid_coords(lat, lon):
                return lat, lon
    except Exception:
        pass
    try:
        if len(data) >= 16:
            lat, lon = struct.unpack("<2d", data[:16])
            if valid_coords(lat, lon):
                return lat, lon
    except Exception:
        pass
    return None

# Request parameters
api_key = "3befcfd2478967d4a4d281df93942809"
lat = 55.7558
lon = 37.6173
units = "metric"
lang = "en"

# UDP weather sending to host
UDP_HOST = "127.0.0.1"
UDP_PORT = 6501
tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# UDP coordinate receiving
COORDS_PORT = 6502
rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind(("0.0.0.0", COORDS_PORT))
rx_sock.setblocking(False)

print(f"Sending weather to {UDP_HOST}:{UDP_PORT} (UDP)")
print(f"Waiting for coordinates on 0.0.0.0:{COORDS_PORT} (UDP)")

# Храним последние значения
last_temp = 20.0
last_humidity = 50.0
last_pressure = 1013.0
last_wind_speed = 3.0
last_wind_deg = 180.0
last_cloudiness = 50
last_city = "-"

while True:
    try:
        updated = None
        while True:
            try:
                data, addr = rx_sock.recvfrom(1024)
            except BlockingIOError:
                break
            coords = parse_coords(data)
            if coords is not None:
                updated = coords
        if updated is not None:
            lat, lon = updated
            print(f"Coordinates updated: lat={lat:.6f}, lon={lon:.6f}")

        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat:.6f}&lon={lon:.6f}&appid={api_key}&units={units}&lang={lang}"
        )

        try:
            j = requests.get(url, timeout=10).json()

            temp_c = j["main"]["temp"]
            humidity_pct = j["main"]["humidity"]
            pressure_hpa = j["main"]["pressure"]
            wind_speed_ms = j.get("wind", {}).get("speed", 0.0)
            wind_deg = j.get("wind", {}).get("deg", 0)
            cloudiness_pct = j.get("clouds", {}).get("all", 0)
            city = j.get("name", "-")

            # обновляем последние значения
            last_temp = temp_c
            last_humidity = humidity_pct
            last_pressure = pressure_hpa
            last_wind_speed = wind_speed_ms
            last_wind_deg = wind_deg
            last_cloudiness = cloudiness_pct
            last_city = city

        except Exception as e:
            print(f"Weather API error: {e}, using simulated weather")

            # генерируем случайные значения на основе последних
            temp_c = last_temp + random.uniform(-1.5, 1.5)
            humidity_pct = max(0, min(100, last_humidity + random.uniform(-5, 5)))
            pressure_hpa = last_pressure + random.uniform(-2, 2)
            wind_speed_ms = max(0, last_wind_speed + random.uniform(-0.5, 0.5))
            wind_deg = (last_wind_deg + random.uniform(-10, 10)) % 360
            cloudiness_pct = max(0, min(100, last_cloudiness + random.uniform(-10, 10)))
            city = last_city + " (simulated)"

        pressure_mmhg = pressure_hpa * 0.75006156

        print(
            f"{city} (lat={lat:.4f}, lon={lon:.4f}):\n "
            f"Temperature: {temp_c:.1f}°C,\n "
            f"Humidity:    {humidity_pct:.0f}%\n "
            f"Pressure:    {pressure_mmhg:.0f} mmHg,\n "
            f"Wind:        {wind_speed_ms:.1f} m/s, {wind_deg:.0f}°,\n "
            f"Cloudiness:  {cloudiness_pct:.0f}%"
        )

        payload = struct.pack(
            "<5d",
            float(temp_c),
            float(humidity_pct),
            float(pressure_hpa),
            float(wind_speed_ms),
            float(wind_deg),
        )
        tx_sock.sendto(payload, (UDP_HOST, UDP_PORT))

        time.sleep(10)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)