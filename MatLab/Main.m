% Параметры запроса
u = udpport("Datagram","IPV4");
k = 0;
apiKey = '3befcfd2478967d4a4d281df93942809';
lat = 55.7558;
lon = 37.6173;
units = 'metric';
lang = 'ru';
while true
    % URL запрос
    url = sprintf('https://api.openweathermap.org/data/2.5/weather?lat=%.4f&lon=%.4f&appid=%s&units=%s&lang=%s', ...
        lat, lon, apiKey, units, lang);
    j = webread(url);
    
    % Разбир данных
    tempC         = j.main.temp;                    % °C
    humidityPct   = j.main.humidity;                % %
    pressure_hPa  = j.main.pressure;                % гПа
    pressure_mmHg = j.main.pressure * 0.75006156;   % мм рт. ст.
    windSpeed_ms  = j.wind.speed;                   % м/с
    windDeg       = j.wind.deg;                     % градусы
    cloudinessPct = j.clouds.all;                   % %
    city          = j.name;
    sunriseUTC    = datetime(j.sys.sunrise, 'ConvertFrom','posixtime', 'TimeZone','UTC');
    sunsetUTC     = datetime(j.sys.sunset,  'ConvertFrom','posixtime', 'TimeZone','UTC');
    sunriseLocal  = datetime(sunriseUTC, 'TimeZone','Europe/Moscow');
    sunsetLocal   = datetime(sunsetUTC,  'TimeZone','Europe/Moscow');
    
    % Вывод
    fprintf("%s:\n " + ...
        "Температура: %.1f°C,\n " + ...
        "Влажность:   %d%%,\n " + ...
        "Давление:    %.0f мм рт. ст.,\n " + ...
        "Ветер:       %.1f м/с, %d°,\n " + ...
        "Облачность:  %d%%\n", ...
        city, tempC, humidityPct, pressure_mmHg, windSpeed_ms, windDeg, cloudinessPct);
    
    bytes = typecast([tempC humidityPct pressure_hPa windSpeed_ms windDeg], 'uint8');
    write(u, bytes, "127.0.0.1", 6501);
    pause(10)
    k = k + 1
end