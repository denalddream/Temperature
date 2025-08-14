% Weather request loop with UDP transmission (Octave-compatible)

% Initialize UDP port
u = udpport("Datagram", "IPV4");

% Request parameters
apiKey = '3befcfd2478967d4a4d281df93942809';
lat = 55.7558;
lon = 37.6173;
units = 'metric';
lang = 'en';  % English response

while true
    % Build request URL
    url = sprintf('https://api.openweathermap.org/data/2.5/weather?lat=%.4f&lon=%.4f&appid=%s&units=%s&lang=%s', ...
        lat, lon, apiKey, units, lang);

    % Fetch raw JSON text
    options = weboptions('ContentType', 'text');
    raw = webread(url, options);

    % Extract weather data using regex
    tempC         = str2double(regexp(raw, '"temp":([\d\.\-]+)', 'tokens', 'once'));
    humidityPct   = str2double(regexp(raw, '"humidity":(\d+)', 'tokens', 'once'));
    pressure_hPa  = str2double(regexp(raw, '"pressure":(\d+)', 'tokens', 'once'));
    windSpeed_ms  = str2double(regexp(raw, '"speed":([\d\.]+)', 'tokens', 'once'));
    windDeg       = str2double(regexp(raw, '"deg":(\d+)', 'tokens', 'once'));
    cloudinessPct = str2double(regexp(raw, '"all":(\d+)', 'tokens', 'once'));
    city          = regexp(raw, '"name":"([^"]+)"', 'tokens', 'once'){1};

    % Sunrise and sunset (UTC timestamps)
    sunriseUTC = str2double(regexp(raw, '"sunrise":(\d+)', 'tokens', 'once'));
    sunsetUTC  = str2double(regexp(raw, '"sunset":(\d+)', 'tokens', 'once'));
    moscowOffset = 3 * 3600;
    sunriseLocal = strftime('%H:%M:%S', localtime(sunriseUTC + moscowOffset));
    sunsetLocal  = strftime('%H:%M:%S', localtime(sunsetUTC + moscowOffset));

    % Convert pressure to mmHg
    pressure_mmHg = pressure_hPa * 0.75006156;

    % Display weather info
    fprintf('%s:\nTemperature: %.1f°C\nHumidity: %d%%\nPressure: %.0f mmHg\n', ...
        city, tempC, humidityPct, pressure_mmHg);
    fprintf('Wind: %.1f m/s, %d°\nCloudiness: %d%%\n', windSpeed_ms, windDeg, cloudinessPct);
    fprintf('Sunrise: %s (MSK)\nSunset:  %s (MSK)\n\n', sunriseLocal, sunsetLocal);

    % Prepare and send UDP packet
    data = [tempC, humidityPct, pressure_hPa, windSpeed_ms, windDeg];
    bytes = typecast(single(data), 'uint8');  % use single precision for compactness
    write(u, bytes, "127.0.0.1", 6501);

    % Wait and increment counter
    pause(10);
end

