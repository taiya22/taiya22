/* ===== 天気服装 - App Initialization ===== */

const App = {
  async init() {
    // Initialize storage with sample data if empty
    Storage.initIfEmpty();

    // Set up navigation
    document.querySelectorAll('.bottom-nav__item').forEach(btn => {
      btn.addEventListener('click', () => {
        UI.navigate(btn.dataset.page);
      });
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

    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', async () => {
      localStorage.removeItem(Storage.KEYS.WEATHER_CACHE);
      await UI.renderHome();
      UI.toast('天気情報を更新しました');
    });

    // Load home
    UI.navigate('home');
    await UI.renderHome();
  }
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
