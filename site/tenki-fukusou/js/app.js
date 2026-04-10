/* ===== 天気服装 - App Initialization ===== */

const App = {
  _lastModeKey: null,
  _refreshTimer: null,

  init() {
    Storage.initIfEmpty();

    // Set up navigation
    document.querySelectorAll('.bottom-nav__item').forEach(btn => {
      btn.addEventListener('click', () => UI.navigate(btn.dataset.page));
    });

    // Set up FAB
    document.getElementById('fab').addEventListener('click', () => {
      UI._selectedColor = '#FFFFFF';
      UI._selectedColorName = '白';
      UI._selectedWarmth = 2;
      UI._selectedWeather = ['sunny', 'cloudy'];
      UI.openAddModal();
    });

    // Close modal on overlay click
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) UI.closeModal();
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', async () => {
      localStorage.removeItem(Storage.KEYS.WEATHER_CACHE);
      await UI.renderHome();
      UI.toast('天気情報を更新しました');
    });

    // Render immediately (sync)
    const mode = Weather.getTimeMode();
    this._lastModeKey = mode.key;
    UI.renderHomeSync();

    // Start auto-refresh timer
    this._startAutoRefresh();
  },

  _startAutoRefresh() {
    // Check every 60 seconds if we've crossed a mode boundary
    this._refreshTimer = setInterval(() => {
      const mode = Weather.getTimeMode();
      if (mode.key !== this._lastModeKey) {
        this._lastModeKey = mode.key;
        // Clear weather cache so we get fresh data
        localStorage.removeItem(Storage.KEYS.WEATHER_CACHE);
        UI.renderHomeSync();
        if (UI.currentPage === 'home') {
          UI.toast(`${mode.icon} ${mode.label}モードに更新しました`);
        }
      }
    }, 60 * 1000);
  }
};

// Boot immediately
App.init();
