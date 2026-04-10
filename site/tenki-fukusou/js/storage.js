/* ===== 天気服装 - LocalStorage Manager ===== */

const Storage = {
  KEYS: {
    WARDROBE: 'tf_wardrobe',
    SETTINGS: 'tf_settings',
    HISTORY: 'tf_history',
    FAVORITES: 'tf_favorites',
    WEATHER_CACHE: 'tf_weather_cache'
  },

  get(key) {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('Storage read error:', e);
      return null;
    }
  },

  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error('Storage write error:', e);
      return false;
    }
  },

  // Wardrobe
  getWardrobe() {
    return this.get(this.KEYS.WARDROBE) || [];
  },

  saveWardrobe(items) {
    return this.set(this.KEYS.WARDROBE, items);
  },

  // Settings
  getSettings() {
    return this.get(this.KEYS.SETTINGS) || {
      city: '東京',
      sensitivity: 'normal', // hot, normal, cold
      apiKey: '',
      unit: 'celsius'
    };
  },

  saveSettings(settings) {
    return this.set(this.KEYS.SETTINGS, settings);
  },

  // History (last 7 days of outfit recommendations)
  getHistory() {
    return this.get(this.KEYS.HISTORY) || [];
  },

  addHistory(outfit) {
    const history = this.getHistory();
    history.unshift({ ...outfit, savedAt: new Date().toISOString() });
    if (history.length > 7) history.pop();
    return this.set(this.KEYS.HISTORY, history);
  },

  // Favorites
  getFavorites() {
    return this.get(this.KEYS.FAVORITES) || [];
  },

  addFavorite(outfit) {
    const favorites = this.getFavorites();
    favorites.unshift({ ...outfit, savedAt: new Date().toISOString() });
    return this.set(this.KEYS.FAVORITES, favorites);
  },

  removeFavorite(index) {
    const favorites = this.getFavorites();
    favorites.splice(index, 1);
    return this.set(this.KEYS.FAVORITES, favorites);
  },

  // Weather cache
  getCachedWeather() {
    const cache = this.get(this.KEYS.WEATHER_CACHE);
    if (!cache) return null;
    const age = Date.now() - new Date(cache.fetchedAt).getTime();
    if (age > 30 * 60 * 1000) return null; // 30 min expiry
    return cache.data;
  },

  cacheWeather(data) {
    return this.set(this.KEYS.WEATHER_CACHE, {
      data,
      fetchedAt: new Date().toISOString()
    });
  },

  _uuid() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  },

  // Init with sample data if first time
  initIfEmpty() {
    if (this.getWardrobe().length === 0) {
      this.loadSampleWardrobe();
    }
  },

  loadSampleWardrobe() {
    const items = SampleWardrobe.map(item => ({
      ...item,
      id: this._uuid(),
      createdAt: new Date().toISOString(),
      lastWornAt: null,
      isFavorite: false
    }));
    this.saveWardrobe(items);
    return items;
  },

  // Export / Import
  exportData() {
    return JSON.stringify({
      wardrobe: this.getWardrobe(),
      settings: this.getSettings(),
      exportedAt: new Date().toISOString()
    }, null, 2);
  },

  importData(jsonString) {
    try {
      const data = JSON.parse(jsonString);
      if (data.wardrobe) this.saveWardrobe(data.wardrobe);
      if (data.settings) this.saveSettings(data.settings);
      return true;
    } catch (e) {
      console.error('Import error:', e);
      return false;
    }
  },

  clearAll() {
    Object.values(this.KEYS).forEach(key => localStorage.removeItem(key));
  }
};
