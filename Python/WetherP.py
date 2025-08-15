import socket
import struct
import time
import requests
import platform
import subprocess
import json

def valid_coords(lat, lon):
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

def parse_coords(data):
    # 1) JSON: {"lat": 55.7, "lon": 37.6} or "lan" by mistake
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
    # 2) CSV: "55.7,37.6"
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
    # 3) Binary format: 2 x double (little-endian)
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
lat = 55.7558   # starting values (will update via UDP)
lon = 37.6173
units = "metric"
lang = "en"

# UDP weather sending to host
UDP_HOST = "127.0.0.1"
UDP_PORT = 6501
tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# UDP coordinate receiving in container (port forwarded from host)
COORDS_PORT = 6502
rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind(("0.0.0.0", COORDS_PORT))
rx_sock.setblocking(False)

print(f"Sending weather to {UDP_HOST}:{UDP_PORT} (UDP)")
print(f"Waiting for coordinates on 0.0.0.0:{COORDS_PORT} (UDP)")

while True:
    try:
        # Non-blocking check for incoming coordinates (update to last packet)
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

        # OpenWeather request
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat:.6f}&lon={lon:.6f}&appid={api_key}&units={units}&lang={lang}"
        )
        j = requests.get(url, timeout=10).json()

        # Parse data
        temp_c = j["main"]["temp"]                      # °C
        humidity_pct = j["main"]["humidity"]            # %
        pressure_hpa = j["main"]["pressure"]            # hPa
        pressure_mmhg = pressure_hpa * 0.75006156      # mmHg
        wind_speed_ms = j.get("wind", {}).get("speed", 0.0)  # m/s
        wind_deg = j.get("wind", {}).get("deg", 0)           # degrees
        cloudiness_pct = j.get("clouds", {}).get("all", 0)   # %
        city = j.get("name", "-")

        # Output
        print(
            f"{city} (lat={lat:.4f}, lon={lon:.4f}):\n "
            f"Temperature: {temp_c:.1f}°C,\n "
            f"Humidity:    {humidity_pct}%\n "
            f"Pressure:    {pressure_mmhg:.0f} mmHg,\n "
            f"Wind:        {wind_speed_ms:.1f} m/s, {wind_deg}°,\n "
            f"Cloudiness:  {cloudiness_pct}%"
        )

        # Send payload (double, little-endian)
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
