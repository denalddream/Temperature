import socket
import struct
import time
import requests
import platform
import subprocess
import json

#
"""
def detect_host_ip():
    system = platform.system().lower()

    # Windows / Mac (Docker Desktop)
    if system in ("windows", "darwin"):
        return "host.docker.internal"

    # Linux
    try:
        # Если сеть host — используем localhost
        result = subprocess.check_output("ip route", shell=True).decode()
        for line in result.splitlines():
            if " src " in line and line.startswith("local"):
                return "127.0.0.1"
            if line.startswith("default via"):
                return line.split()[2]
    except Exception:
        pass

    # Попробуем дефолтный gateway (часто 172.17.0.1 в bridge)
    try:
        with open("/proc/net/route") as f:
            for line in f:
                parts = line.strip().split()
                if parts[1] != "00000000" or not int(parts[3], 16) & 2:
                    continue
                gateway_hex = parts[2]
                gateway_ip = ".".join(str(int(gateway_hex[i:i + 2], 16)) for i in (6, 4, 2, 0))
                return gateway_ip
    except Exception:
        pass

    return "127.0.0.1"
"""
def valid_coords(lat, lon):
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

def parse_coords(data):
    # 1) JSON: {"lat": 55.7, "lon": 37.6} или "lan" по ошибке
    try:
        obj = json.loads(data.decode("utf-8").strip())
        if isinstance(obj, dict):
            lat = float(obj.get("lat"))
            lon = obj.get("lon", obj.get("lan"))
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
    # 3) Двоичный формат: 2 x double (little-endian)
    try:
        if len(data) >= 16:
            lat, lon = struct.unpack("<2d", data[:16])
            if valid_coords(lat, lon):
                return lat, lon
    except Exception:
        pass
    return None

# Параметры запроса
api_key = "3befcfd2478967d4a4d281df93942809"
lat = 55.7558   # стартовые значения (обновятся по UDP)
lon = 37.6173
units = "metric"
lang = "ru"

# UDP отправка погоды на хост
UDP_HOST = "127.0.0.1"#detect_host_ip()
UDP_PORT = 6501
tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# UDP приём координат в контейнере (пробрось порт с хоста)
COORDS_PORT = 6502
rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind(("0.0.0.0", COORDS_PORT))
rx_sock.setblocking(False)

print(f"➡ Отправка погоды на {UDP_HOST}:{UDP_PORT} (UDP)")
print(f"⬅ Ожидаю координаты на 0.0.0.0:{COORDS_PORT} (UDP)")

while True:
    try:
        # Неблокирующий опрос входящих координат (обновляем до последнего пакета)
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
            print(f"📍 Обновлены координаты: lat={lat:.6f}, lon={lon:.6f}")

        # Запрос к OpenWeather
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat:.6f}&lon={lon:.6f}&appid={api_key}&units={units}&lang={lang}"
        )
        j = requests.get(url, timeout=10).json()

        # Разбор данных
        temp_c = j["main"]["temp"]                      # °C
        humidity_pct = j["main"]["humidity"]            # %
        pressure_hpa = j["main"]["pressure"]            # гПа
        pressure_mmhg = pressure_hpa * 0.75006156       # мм рт. ст.
        wind_speed_ms = j.get("wind", {}).get("speed", 0.0)  # м/с
        wind_deg = j.get("wind", {}).get("deg", 0)           # градусы
        cloudiness_pct = j.get("clouds", {}).get("all", 0)   # %
        city = j.get("name", "—")

        # Вывод
        print(
            f"{city} (lat={lat:.4f}, lon={lon:.4f}):\n "
            f"Температура: {temp_c:.1f}°C,\n "
            f"Влажность:   {humidity_pct}%\n "
            f"Давление:    {pressure_mmhg:.0f} мм рт. ст.,\n "
            f"Ветер:       {wind_speed_ms:.1f} м/с, {wind_deg}°,\n "
            f"Облачность:  {cloudiness_pct}%"
        )

        # Отправка полезной нагрузки (double, little-endian)
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
        print(f"Ошибка: {e}")
        time.sleep(5)
