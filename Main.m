url = "https://wttr.in/Moscow?format=j1";
opts = weboptions('ContentType','json','Timeout',15);
j = webread(url, opts);

cc = j.current_condition(1); % текущие условия

% Переменные
tempC         = str2double(cc.temp_C);
feelsLikeC    = str2double(cc.FeelsLikeC);
humidityPct   = str2double(cc.humidity);
pressure_hPa  = str2double(cc.pressure);          % гПа
pressure_mmHg = pressure_hPa * 0.75006156;        % мм рт. ст.
windSpeed_ms  = str2double(cc.windspeedKmph) / 3.6;
windDeg       = str2double(cc.winddirDegree);
cloudinessPct = str2double(cc.cloudcover);
description   = string(cc.weatherDesc(1).value);

% Времени восхода/заката в этом формате может не быть в "current_condition";
% при желании возьмите из j.weather(1).astronomy(1)
astr = j.weather(1).astronomy(1);
sunriseLocal = datetime(string(astr.sunrise), 'InputFormat','hh:mm a', 'TimeZone','Europe/Moscow');
sunsetLocal  = datetime(string(astr.sunset),  'InputFormat','hh:mm a', 'TimeZone','Europe/Moscow');

fprintf("Москва: %s, %.1f°C (ощущается %.1f°C), влажн. %d%%, давл. %.0f мм рт. ст., ветер %.1f м/с, %d°, облачн. %d%%\n", ...
    description, tempC, feelsLikeC, humidityPct, pressure_mmHg, windSpeed_ms, windDeg, cloudinessPct);