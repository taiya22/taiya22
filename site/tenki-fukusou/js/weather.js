/* ===== 天気服装 - Weather Module ===== */

const Weather = {
  WEATHER_ICONS: {
    sunny: { icon: '\u2600\uFE0F', label: '\u6674\u308C' },
    cloudy: { icon: '\u26C5', label: '\u66C7\u308A' },
    rainy: { icon: '\u{1F327}\uFE0F', label: '\u96E8' },
    snowy: { icon: '\u2744\uFE0F', label: '\u96EA' },
    stormy: { icon: '\u26C8\uFE0F', label: '\u96F7\u96E8' }
  },

  // Synchronous fetch - uses cache or mock data instantly
  fetchWeatherSync() {
    const settings = Storage.getSettings();
    const cached = Storage.getCachedWeather();
    if (cached) return cached;

    const mock = MockData.getTodayWeather();
    mock.city = settings.city;
    Storage.cacheWeather(mock);
    return mock;
  },

  // Async fetch - tries real API if key exists, falls back to sync
  async fetchWeather() {
    const settings = Storage.getSettings();

    // No API key -> use sync path
    if (!settings.apiKey) return this.fetchWeatherSync();

    // Try cache first
    const cached = Storage.getCachedWeather();
    if (cached) return cached;

    // Try real API
    try {
      const data = await this._fetchFromAPI(settings.apiKey, settings.city);
      Storage.cacheWeather(data);
      return data;
    } catch (e) {
      console.warn('API fetch failed, using mock:', e);
      return this.fetchWeatherSync();
    }
  },

  async _fetchFromAPI(apiKey, city) {
    const geoUrl = `https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(city)}&limit=1&appid=${apiKey}`;
    const geoRes = await fetch(geoUrl);
    const geoData = await geoRes.json();
    if (!geoData.length) throw new Error('City not found');

    const { lat, lon } = geoData[0];
    const url = `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric&lang=ja`;
    const res = await fetch(url);
    const data = await res.json();

    return this._normalizeAPIData(data, city);
  },

  _normalizeAPIData(data, city) {
    const today = new Date().toISOString().split('T')[0];
    const todayForecasts = data.list.filter(item =>
      item.dt_txt.startsWith(today)
    );

    const periodMap = [
      { label: '朝', hours: [6, 9], timeRange: '06:00-09:00' },
      { label: '昼', hours: [9, 15], timeRange: '09:00-15:00' },
      { label: '夕', hours: [15, 18], timeRange: '15:00-18:00' },
      { label: '夜', hours: [18, 23], timeRange: '18:00-23:00' }
    ];

    const periods = periodMap.map(period => {
      const matching = todayForecasts.filter(f => {
        const hour = new Date(f.dt_txt).getHours();
        return hour >= period.hours[0] && hour < period.hours[1];
      });

      if (matching.length === 0) {
        const mock = MockData.getTodayWeather();
        const mockPeriod = mock.periods.find(p => p.label === period.label);
        return mockPeriod;
      }

      const avgTemp = Math.round(matching.reduce((s, f) => s + f.main.temp, 0) / matching.length);
      const mainWeather = this._mapWeatherCondition(matching[0].weather[0].main);
      const maxRain = Math.round(Math.max(...matching.map(f => (f.pop || 0) * 100)));

      return {
        label: period.label,
        timeRange: period.timeRange,
        temp: avgTemp,
        weather: mainWeather,
        humidity: Math.round(matching[0].main.humidity),
        windSpeed: Math.round(matching[0].wind.speed),
        rainProbability: maxRain
      };
    });

    return { city, date: today, periods };
  },

  _mapWeatherCondition(condition) {
    const map = {
      'Clear': 'sunny',
      'Clouds': 'cloudy',
      'Rain': 'rainy',
      'Drizzle': 'rainy',
      'Thunderstorm': 'stormy',
      'Snow': 'snowy',
      'Mist': 'cloudy',
      'Fog': 'cloudy',
      'Haze': 'cloudy'
    };
    return map[condition] || 'cloudy';
  },

  getIcon(weather) {
    return (this.WEATHER_ICONS[weather] || this.WEATHER_ICONS.cloudy).icon;
  },

  getLabel(weather) {
    return (this.WEATHER_ICONS[weather] || this.WEATHER_ICONS.cloudy).label;
  },

  getSummary(weatherData) {
    if (!weatherData || !weatherData.periods) return {};
    const temps = weatherData.periods.map(p => p.temp);
    const minTemp = Math.min(...temps);
    const maxTemp = Math.max(...temps);
    const tempDiff = maxTemp - minTemp;
    const hasRain = weatherData.periods.some(p => p.rainProbability >= 50);
    const hasLightRain = weatherData.periods.some(p => p.rainProbability >= 30);
    const maxWind = Math.max(...weatherData.periods.map(p => p.windSpeed));
    const dominantWeather = this._getDominantWeather(weatherData.periods);

    return { minTemp, maxTemp, tempDiff, hasRain, hasLightRain, maxWind, dominantWeather };
  },

  _getDominantWeather(periods) {
    const counts = {};
    periods.forEach(p => {
      counts[p.weather] = (counts[p.weather] || 0) + 1;
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
  },

  getWeatherCardClass(weather) {
    if (weather === 'rainy' || weather === 'stormy') return 'weather-card--rainy';
    if (weather === 'cloudy') return 'weather-card--cloudy';
    if (weather === 'snowy') return 'weather-card--snowy';
    return '';
  }
};
