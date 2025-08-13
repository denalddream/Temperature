function W = WetherML(lat, lon)

% Параметры запроса
apiKey = '3befcfd2478967d4a4d281df93942809';
units = 'metric';
lang = 'ru';

% URL запрос
url = sprintf('https://api.openweathermap.org/data/2.5/weather?lat=%.4f&lon=%.4f&appid=%s&units=%s&lang=%s', ...
    lat, lon, apiKey, units, lang);
j = webread(url);

% Разбор данных
W.tempC         = j.main.temp;                    % °C
W.humidityPct   = j.main.humidity;                % %
W.pressure_hPa  = j.main.pressure;                % гПа
W.pressure_mmHg = j.main.pressure * 0.75006156;   % мм рт. ст.
W.windSpeed_ms  = j.wind.speed;                   % м/с
W.windDeg       = j.wind.deg;                     % градусы
W.cloudinessPct = j.clouds.all;                   % %
W.city          = j.name;
W.sunriseUTC    = datetime(j.sys.sunrise, 'ConvertFrom','posixtime', 'TimeZone','UTC');
W.sunsetUTC     = datetime(j.sys.sunset,  'ConvertFrom','posixtime', 'TimeZone','UTC');
W.sunriseLocal  = datetime(j.sys.sunrise, 'ConvertFrom','posixtime', 'TimeZone','Europe/Moscow');
W.sunsetLocal   = datetime(j.sys.sunset,  'ConvertFrom','posixtime', 'TimeZone','Europe/Moscow');