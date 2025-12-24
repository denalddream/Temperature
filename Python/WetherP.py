import socket
import struct
import time
import requests
import json
import random
import threading
import tkinter as tk
from tkinter import font as tkfont


# --- Логика парсинга координат (без изменений) ---
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


# --- Глобальные переменные настроек ---
api_key = "3befcfd2478967d4a4d281df93942809"
current_lat = 55.7558  # Используем глобальные переменные для доступа из потока
current_lon = 37.6173
units = "metric"
lang = "en"

UDP_HOST = "127.0.0.1"
UDP_PORT = 6501

COORDS_PORT = 6502

# --- Инициализация сокетов ---
tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind(("0.0.0.0", COORDS_PORT))
rx_sock.setblocking(False)

# --- GUI Setup ---
root = tk.Tk()
root.title("Weather UDP Monitor")
root.geometry("400x350")
root.configure(bg="#2b2b2b")

# Стили шрифтов
font_large = tkfont.Font(family="Helvetica", size=48, weight="bold")
font_med = tkfont.Font(family="Helvetica", size=14)
font_small = tkfont.Font(family="Helvetica", size=10)

# Элементы интерфейса (Labels)
lbl_city = tk.Label(root, text="Waiting for data...", font=font_med, fg="#ffffff", bg="#2b2b2b")
lbl_city.pack(pady=(20, 5))

lbl_coords = tk.Label(root, text=f"Lat: {current_lat}, Lon: {current_lon}", font=font_small, fg="#aaaaaa", bg="#2b2b2b")
lbl_coords.pack(pady=0)

lbl_temp = tk.Label(root, text="--.-°C", font=font_large, fg="#ffcc00", bg="#2b2b2b")
lbl_temp.pack(pady=20)

lbl_details = tk.Label(root, text="", font=font_med, fg="#dddddd", bg="#2b2b2b", justify="left")
lbl_details.pack(pady=10)


# Функция обновления GUI (вызывается из главного потока через root.after)
def update_gui_labels(city, lat, lon, temp_c, humidity, pressure, wind_spd, wind_deg, cloudiness):
    lbl_city.config(text=city)
    lbl_coords.config(text=f"Lat: {lat:.4f}, Lon: {lon:.4f}")
    lbl_temp.config(text=f"{temp_c:.1f}°C")

    details_text = (
        f"Humidity:   {humidity:.0f}%\n"
        f"Pressure:   {pressure:.0f} mmHg\n"
        f"Wind:       {wind_spd:.1f} m/s ({wind_deg:.0f}°)\n"
        f"Cloudiness: {cloudiness:.0f}%"
    )
    lbl_details.config(text=details_text)


# --- Основной рабочий поток (Weather Logic) ---
def weather_worker():
    global current_lat, current_lon

    # Храним последние значения (локально для потока)
    last_temp = 20.0
    last_humidity = 50.0
    last_pressure = 1013.0
    last_wind_speed = 3.0
    last_wind_deg = 180.0
    last_cloudiness = 50
    last_city = "-"

    print(f"Sending weather to {UDP_HOST}:{UDP_PORT} (UDP)")
    print(f"Waiting for coordinates on 0.0.0.0:{COORDS_PORT} (UDP)")

    while True:
        try:
            # 1. Проверяем входящие координаты
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
                current_lat, current_lon = updated
                print(f"Coordinates updated: lat={current_lat:.6f}, lon={current_lon:.6f}")

            # 2. Запрос погоды
            url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?lat={current_lat:.6f}&lon={current_lon:.6f}&appid={api_key}&units={units}&lang={lang}"
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

                # генерируем случайные значения
                temp_c = last_temp + random.uniform(-1.5, 1.5)
                humidity_pct = max(0, min(100, last_humidity + random.uniform(-5, 5)))
                pressure_hpa = last_pressure + random.uniform(-2, 2)
                wind_speed_ms = max(0, last_wind_speed + random.uniform(-0.5, 0.5))
                wind_deg = (last_wind_deg + random.uniform(-10, 10)) % 360
                cloudiness_pct = max(0, min(100, last_cloudiness + random.uniform(-10, 10)))
                city = last_city + " (simulated)"

            pressure_mmhg = pressure_hpa * 0.75006156

            # 3. Вывод в консоль
            print(
                f"{city} (lat={current_lat:.4f}, lon={current_lon:.4f}):\n "
                f"Temperature: {temp_c:.1f}°C,\n "
                f"Humidity:    {humidity_pct:.0f}%\n "
                f"Pressure:    {pressure_mmhg:.0f} mmHg,\n "
                f"Wind:        {wind_speed_ms:.1f} m/s, {wind_deg:.0f}°,\n "
                f"Cloudiness:  {cloudiness_pct:.0f}%"
            )

            # 4. Обновление GUI
            # Используем root.after, чтобы безопасно обновить интерфейс из потока
            root.after(0, update_gui_labels,
                       city, current_lat, current_lon, temp_c,
                       humidity_pct, pressure_mmhg, wind_speed_ms, wind_deg, cloudiness_pct)

            # 5. Отправка UDP
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
            print(f"Error in worker loop: {e}")
            time.sleep(5)


# --- Запуск ---
if __name__ == "__main__":
    # Запускаем логику в отдельном потоке (daemon=True, чтобы поток закрылся вместе с окном)
    t = threading.Thread(target=weather_worker, daemon=True)
    t.start()

    # Запускаем главный цикл GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Program closed.")