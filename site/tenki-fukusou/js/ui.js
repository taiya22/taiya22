/* ===== 天気服装 - UI Renderer ===== */

const UI = {
  currentPage: 'home',
  currentOutfit: null,
  currentWeather: null,
  editingItemId: null,
  wardrobeFilter: 'all',

  // ===== Navigation =====
  navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.bottom-nav__item').forEach(n => n.classList.remove('active'));

    document.getElementById('page-' + page)?.classList.add('active');
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

    this.currentPage = page;

    // Show/hide FAB
    const fab = document.getElementById('fab');
    if (fab) fab.style.display = page === 'wardrobe' ? 'flex' : 'none';

    if (page === 'wardrobe') this.renderWardrobe();
    if (page === 'settings') this.renderSettings();
  },

  // ===== Toast =====
  toast(message) {
    const el = document.getElementById('toast');
    el.textContent = message;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2500);
  },

  // ===== Home Page =====
  // Sync render - instant, no loading state
  renderHomeSync() {
    const weatherData = Weather.fetchWeatherSync();
    this.currentWeather = weatherData;
    this.renderWeatherCard(weatherData);
    this.renderOutfit(weatherData);
  },

  // Async render - for API key users
  async renderHome() {
    const settings = Storage.getSettings();
    if (!settings.apiKey) {
      this.renderHomeSync();
      return;
    }
    const weatherData = await Weather.fetchWeather();
    this.currentWeather = weatherData;
    this.renderWeatherCard(weatherData);
    this.renderOutfit(weatherData);
  },

  renderWeatherCard(data) {
    const mode = Weather.getTimeMode();
    const summary = Weather.getSummaryForMode(data, mode);
    const container = document.getElementById('weather-card');
    const dominant = summary.dominantWeather;
    const cardClass = Weather.getWeatherCardClass(dominant);
    const activePeriods = Weather.getPeriodsForMode(data, mode);

    // Format date
    const now = new Date();
    const dayNames = ['日', '月', '火', '水', '木', '金', '土'];
    const dateStr = `${now.getMonth() + 1}月${now.getDate()}日(${dayNames[now.getDay()]})`;

    // Next refresh time
    const nextRefresh = Weather.getNextRefreshTime();
    const nextH = String(nextRefresh.getHours()).padStart(2, '0');
    const nextM = String(nextRefresh.getMinutes()).padStart(2, '0');

    // Current temp = first active period
    const currentTemp = activePeriods[0]?.temp ?? data.periods[1].temp;

    container.className = 'weather-card ' + cardClass;
    container.innerHTML = `
      <div class="weather-card__location">
        <span>\uD83D\uDCCD</span>
        <span>${data.city}</span>
        <span style="margin-left:auto">${dateStr}</span>
      </div>
      <div class="time-mode-badge">
        <span>${mode.icon} ${mode.label}</span>
        <span class="time-mode-badge__next">\u23F0 次回更新 ${nextH}:${nextM}</span>
      </div>
      <div class="weather-card__main">
        <div>
          <div class="weather-card__temp">${currentTemp}<small>\u00B0C</small></div>
          <div class="weather-card__desc">${mode.desc}</div>
        </div>
        <div class="weather-card__icon">${Weather.getIcon(dominant)}</div>
      </div>
      <div class="weather-card__periods">
        ${data.periods.map((p, i) => {
          const isActive = mode.periodIndices.includes(i);
          return `
            <div class="weather-period ${isActive ? '' : 'weather-period--past'}">
              <div class="weather-period__label">${p.label}</div>
              <div class="weather-period__icon">${Weather.getIcon(p.weather)}</div>
              <div class="weather-period__temp">${p.temp}\u00B0</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  },

  renderOutfit(weatherData) {
    const outfit = Recommend.generate(weatherData);
    this.currentOutfit = outfit;
    const container = document.getElementById('outfit-container');

    if (!outfit) {
      container.innerHTML = `
        <div class="alert-card">
          <span class="alert-card__icon">\uD83D\uDC54</span>
          <div>
            ワードローブに服が登録されていません。<br>
            下のタブから服を追加するか、設定からサンプルデータを読み込んでください。
          </div>
        </div>
      `;
      return;
    }

    // Mark items as worn
    Object.values(outfit.items).flat().filter(Boolean).forEach(item => {
      if (item.id) Wardrobe.markWorn(item.id);
    });

    // Save to history
    Storage.addHistory(outfit);

    container.innerHTML = `
      ${this._renderOutfitLayers(outfit)}
      ${this._renderTimeline(outfit)}
      ${this._renderCarryItems(outfit)}
      ${this._renderMessage(outfit)}
      <div class="outfit-actions">
        <button class="btn btn--primary" onclick="UI.refreshOutfit()">
          \uD83D\uDD04 別のコーデ
        </button>
        <button class="btn btn--secondary" onclick="UI.saveOutfitFavorite()">
          \u2764\uFE0F 保存
        </button>
      </div>
    `;
  },

  _renderOutfitLayers(outfit) {
    const layers = [];

    if (outfit.items.outer) {
      layers.push({ type: 'outer', label: 'アウター', item: outfit.items.outer });
    }
    if (outfit.items.base) {
      layers.push({ type: 'base', label: 'トップス', item: outfit.items.base });
    }
    if (outfit.items.bottoms) {
      layers.push({ type: 'bottom', label: 'ボトムス', item: outfit.items.bottoms });
    }
    if (outfit.items.shoes) {
      layers.push({ type: 'shoes', label: '靴', item: outfit.items.shoes });
    }
    if (outfit.items.accessories?.length) {
      outfit.items.accessories.forEach(acc => {
        layers.push({ type: 'accessory', label: '小物', item: acc });
      });
    }

    const mode = outfit.mode || Weather.getTimeMode();
    const titles = {
      morning: '\uD83D\uDC57 今日の一日コーデ',
      afternoon: '\uD83D\uDC57 午後〜夜のコーデ',
      evening: '\uD83D\uDC57 夕方〜夜のコーデ'
    };

    return `
      <div class="outfit-section">
        <div class="section-title">${titles[mode.key] || titles.morning}</div>
        <div class="outfit-card">
          <div class="outfit-layers">
            ${layers.map(l => `
              <div class="outfit-layer outfit-layer--${l.type}">
                <div class="outfit-layer__icon">${Wardrobe.getCategoryIcon(l.item.category)}</div>
                <div class="outfit-layer__info">
                  <div class="outfit-layer__name">${l.item.name}</div>
                  <div class="outfit-layer__category">${l.label} / ${Wardrobe.getSubCategoryLabel(l.item.category, l.item.subCategory)}</div>
                </div>
                <div class="outfit-layer__color" style="background:${l.item.color}"></div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  },

  _renderTimeline(outfit) {
    if (!outfit.timeline || outfit.timeline.length === 0) return '';
    const timelineTitle = (outfit.mode?.key === 'evening') ? '\uD83D\uDD50 これからの着こなし'
                        : (outfit.mode?.key === 'afternoon') ? '\uD83D\uDD50 午後の着こなし'
                        : '\uD83D\uDD50 一日の着こなし';
    return `
      <div class="outfit-section">
        <div class="section-title">${timelineTitle}</div>
        <div class="timeline">
          <ul class="timeline__list">
            ${outfit.timeline.map(t => `
              <li class="timeline__item">
                <span class="timeline__period">${t.period} ${t.temp}\u00B0C</span>
                ${t.action}
              </li>
            `).join('')}
          </ul>
        </div>
      </div>
    `;
  },

  _renderCarryItems(outfit) {
    if (!outfit.carryItems || outfit.carryItems.length === 0) return '';
    return `
      <div class="outfit-section">
        <div class="section-title">\uD83C\uDF92 持ち物</div>
        <div class="carry-items">
          <ul class="carry-items__list">
            ${outfit.carryItems.map(item => `
              <li class="carry-item">
                <span>${item.name}</span>
                <span style="color:var(--mid-gray);font-size:0.75rem">（${item.reason}）</span>
              </li>
            `).join('')}
          </ul>
        </div>
      </div>
    `;
  },

  _renderMessage(outfit) {
    if (!outfit.message) return '';
    return `
      <div class="alert-card" style="background:#EBF3FC;border-color:var(--sky-blue)">
        <span class="alert-card__icon">\uD83D\uDCA1</span>
        <div>${outfit.message}</div>
      </div>
    `;
  },

  refreshOutfit() {
    if (!this.currentWeather) return;
    const alt = Recommend.generateAlternative(this.currentWeather, this.currentOutfit);
    if (alt) {
      this.currentOutfit = alt;
      const container = document.getElementById('outfit-container');
      container.innerHTML = '';
      // Re-render inline
      Storage.addHistory(alt);
      container.innerHTML = `
        ${this._renderOutfitLayers(alt)}
        ${this._renderTimeline(alt)}
        ${this._renderCarryItems(alt)}
        ${this._renderMessage(alt)}
        <div class="outfit-actions">
          <button class="btn btn--primary" onclick="UI.refreshOutfit()">
            \uD83D\uDD04 別のコーデ
          </button>
          <button class="btn btn--secondary" onclick="UI.saveOutfitFavorite()">
            \u2764\uFE0F 保存
          </button>
        </div>
      `;
    }
    this.toast('別のコーデを提案しました');
  },

  saveOutfitFavorite() {
    if (this.currentOutfit) {
      Storage.addFavorite(this.currentOutfit);
      this.toast('お気に入りに保存しました');
    }
  },

  // ===== Wardrobe Page =====
  renderWardrobe() {
    this._renderWardrobeTabs();
    this._renderWardrobeGrid();
  },

  _renderWardrobeTabs() {
    const container = document.getElementById('wardrobe-tabs');
    const categories = [
      { key: 'all', label: 'すべて' },
      ...Object.entries(Wardrobe.CATEGORIES).map(([key, val]) => ({ key, label: val.icon + ' ' + val.label }))
    ];

    container.innerHTML = categories.map(cat => `
      <button class="wardrobe-tab ${cat.key === this.wardrobeFilter ? 'active' : ''}"
              onclick="UI.filterWardrobe('${cat.key}')">
        ${cat.label}
      </button>
    `).join('');
  },

  _renderWardrobeGrid() {
    const container = document.getElementById('wardrobe-grid');
    const items = Wardrobe.getByCategory(this.wardrobeFilter);

    if (items.length === 0) {
      container.innerHTML = `
        <div class="wardrobe-empty" style="grid-column: 1/-1">
          <div class="wardrobe-empty__icon">\uD83D\uDC5A</div>
          <p>服がまだ登録されていません</p>
          <p style="font-size:0.8rem;color:var(--mid-gray);margin-top:8px">
            右下の + ボタンから追加できます
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="wardrobe-item" onclick="UI.editItem('${item.id}')">
        <div class="wardrobe-item__color" style="background:${item.color}"></div>
        <div class="wardrobe-item__name">${item.name}</div>
        <div class="wardrobe-item__sub">${Wardrobe.getSubCategoryLabel(item.category, item.subCategory)}</div>
        <div class="wardrobe-item__warmth">${Wardrobe.getWarmthStars(item.warmthLevel)}</div>
        <button class="wardrobe-item__delete" onclick="event.stopPropagation(); UI.deleteItem('${item.id}', '${item.name}')">
          \u2715
        </button>
      </div>
    `).join('');
  },

  filterWardrobe(category) {
    this.wardrobeFilter = category;
    this.renderWardrobe();
  },

  // ===== Modal =====
  openAddModal() {
    this.editingItemId = null;
    this._renderModal({
      name: '', category: 'tops', subCategory: '',
      color: '#FFFFFF', warmthLevel: 2,
      weatherSuitability: ['sunny', 'cloudy']
    });
    document.getElementById('modal-overlay').classList.add('active');
  },

  editItem(id) {
    const item = Wardrobe.getAll().find(i => i.id === id);
    if (!item) return;
    this.editingItemId = id;
    this._renderModal(item);
    document.getElementById('modal-overlay').classList.add('active');
  },

  closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    this.editingItemId = null;
  },

  _renderModal(item) {
    const modal = document.getElementById('modal-content');
    const isEdit = !!this.editingItemId;
    const currentCat = item.category || 'tops';
    const subCats = Wardrobe.CATEGORIES[currentCat]?.subCategories || {};

    modal.innerHTML = `
      <div class="modal__header">
        <div class="modal__title">${isEdit ? '服を編集' : '服を追加'}</div>
        <button class="modal__close" onclick="UI.closeModal()">\u2715</button>
      </div>

      <div class="form-group">
        <label class="form-label">名前</label>
        <input class="form-input" id="item-name" value="${item.name}" placeholder="例: 白シャツ">
      </div>

      <div class="form-group">
        <label class="form-label">カテゴリ</label>
        <select class="form-select" id="item-category" onchange="UI.onCategoryChange()">
          ${Object.entries(Wardrobe.CATEGORIES).map(([key, val]) =>
            `<option value="${key}" ${key === currentCat ? 'selected' : ''}>${val.icon} ${val.label}</option>`
          ).join('')}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">サブカテゴリ</label>
        <select class="form-select" id="item-subcategory">
          ${Object.entries(subCats).map(([key, val]) =>
            `<option value="${key}" ${key === item.subCategory ? 'selected' : ''}>${val}</option>`
          ).join('')}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">色</label>
        <div class="color-options" id="color-options">
          ${Wardrobe.COLORS.map(c => `
            <div class="color-option ${c.hex === item.color ? 'selected' : ''}"
                 style="background:${c.hex};${c.hex === '#FFFFFF' ? 'border:1px solid #DFE6E9' : ''}"
                 data-color="${c.hex}" data-name="${c.name}"
                 onclick="UI.selectColor('${c.hex}', '${c.name}')">
            </div>
          `).join('')}
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">暖かさ</label>
        <div class="warmth-options">
          ${[1,2,3,4,5].map(w => `
            <button class="warmth-option ${w === item.warmthLevel ? 'selected' : ''}"
                    data-warmth="${w}" onclick="UI.selectWarmth(${w})">
              ${w}<br><span style="font-size:0.65rem">${Wardrobe.getWarmthLabel(w)}</span>
            </button>
          `).join('')}
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">天気適性</label>
        <div class="weather-options">
          ${[
            { key: 'sunny', label: '\u2600\uFE0F 晴' },
            { key: 'cloudy', label: '\u26C5 曇' },
            { key: 'rainy', label: '\uD83C\uDF27\uFE0F 雨' },
            { key: 'snowy', label: '\u2744\uFE0F 雪' }
          ].map(w => `
            <button class="weather-option ${(item.weatherSuitability || []).includes(w.key) ? 'selected' : ''}"
                    data-weather="${w.key}" onclick="UI.toggleWeather('${w.key}')">
              ${w.label}
            </button>
          `).join('')}
        </div>
      </div>

      <button class="btn btn--primary btn--full" onclick="UI.saveItem()" style="margin-top:8px">
        ${isEdit ? '更新する' : '追加する'}
      </button>

      ${isEdit ? `
        <button class="btn btn--danger btn--full" onclick="UI.deleteItem('${item.id}', '${item.name}')" style="margin-top:8px">
          削除する
        </button>
      ` : ''}
    `;
  },

  // Modal interaction helpers
  _selectedColor: '#FFFFFF',
  _selectedColorName: '白',
  _selectedWarmth: 2,
  _selectedWeather: ['sunny', 'cloudy'],

  selectColor(hex, name) {
    this._selectedColor = hex;
    this._selectedColorName = name;
    document.querySelectorAll('.color-option').forEach(el => {
      el.classList.toggle('selected', el.dataset.color === hex);
    });
  },

  selectWarmth(level) {
    this._selectedWarmth = level;
    document.querySelectorAll('.warmth-option').forEach(el => {
      el.classList.toggle('selected', parseInt(el.dataset.warmth) === level);
    });
  },

  toggleWeather(weather) {
    const idx = this._selectedWeather.indexOf(weather);
    if (idx >= 0) {
      if (this._selectedWeather.length > 1) this._selectedWeather.splice(idx, 1);
    } else {
      this._selectedWeather.push(weather);
    }
    document.querySelectorAll('.weather-option').forEach(el => {
      el.classList.toggle('selected', this._selectedWeather.includes(el.dataset.weather));
    });
  },

  onCategoryChange() {
    const cat = document.getElementById('item-category').value;
    const subCats = Wardrobe.CATEGORIES[cat]?.subCategories || {};
    const subSelect = document.getElementById('item-subcategory');
    subSelect.innerHTML = Object.entries(subCats)
      .map(([key, val]) => `<option value="${key}">${val}</option>`)
      .join('');
  },

  saveItem() {
    const name = document.getElementById('item-name').value.trim();
    if (!name) {
      this.toast('名前を入力してください');
      return;
    }

    const data = {
      name,
      category: document.getElementById('item-category').value,
      subCategory: document.getElementById('item-subcategory').value,
      color: this._selectedColor,
      colorName: this._selectedColorName,
      warmthLevel: this._selectedWarmth,
      weatherSuitability: [...this._selectedWeather]
    };

    if (this.editingItemId) {
      Wardrobe.update(this.editingItemId, data);
      this.toast('更新しました');
    } else {
      Wardrobe.add(data);
      this.toast('追加しました');
    }

    this.closeModal();
    this.renderWardrobe();
  },

  deleteItem(id, name) {
    if (confirm(`「${name}」を削除しますか？`)) {
      Wardrobe.remove(id);
      this.closeModal();
      this.renderWardrobe();
      this.toast('削除しました');
    }
  },

  // ===== Settings Page =====
  renderSettings() {
    const container = document.getElementById('page-settings');
    const settings = Storage.getSettings();
    const wardrobeCount = Wardrobe.getAll().length;

    container.innerHTML = `
      <div class="settings-section">
        <div class="settings-section__title">\uD83C\uDF21\uFE0F 体感温度</div>
        <div class="sensitivity-options">
          ${[
            { key: 'hot', label: '暑がり', desc: '+2\u00B0C補正' },
            { key: 'normal', label: '普通', desc: '補正なし' },
            { key: 'cold', label: '寒がり', desc: '-2\u00B0C補正' }
          ].map(opt => `
            <button class="sensitivity-option ${settings.sensitivity === opt.key ? 'selected' : ''}"
                    onclick="UI.setSensitivity('${opt.key}')">
              ${opt.label}<br><span style="font-size:0.65rem;opacity:0.7">${opt.desc}</span>
            </button>
          `).join('')}
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section__title">\uD83D\uDCCD 都市設定</div>
        <div class="form-group" style="margin-bottom:0">
          <input class="form-input" id="settings-city" value="${settings.city}" placeholder="都市名">
          <button class="btn btn--primary btn--small" onclick="UI.saveCity()" style="margin-top:8px">保存</button>
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section__title">\uD83D\uDD11 天気API</div>
        <div class="form-group" style="margin-bottom:4px">
          <input class="form-input" id="settings-apikey" value="${settings.apiKey}" placeholder="OpenWeatherMap APIキー（任意）">
        </div>
        <p style="font-size:0.75rem;color:var(--mid-gray)">未入力時はデモデータを使用します</p>
        <button class="btn btn--primary btn--small" onclick="UI.saveApiKey()" style="margin-top:8px">保存</button>
      </div>

      <div class="settings-section">
        <div class="settings-section__title">\uD83D\uDCE6 データ管理</div>
        <p style="font-size:0.85rem;color:var(--mid-gray);margin-bottom:12px">
          ワードローブ: ${wardrobeCount}件
        </p>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button class="btn btn--secondary btn--small" onclick="UI.loadSampleData()">
            \uD83D\uDC55 サンプル服を読み込む
          </button>
          <button class="btn btn--secondary btn--small" onclick="UI.exportData()">
            \uD83D\uDCE4 エクスポート
          </button>
          <button class="btn btn--secondary btn--small" onclick="document.getElementById('import-file').click()">
            \uD83D\uDCE5 インポート
          </button>
          <input type="file" id="import-file" accept=".json" style="display:none" onchange="UI.importData(event)">
          <button class="btn btn--danger btn--small" onclick="UI.resetAll()">
            \uD83D\uDDD1\uFE0F 全データリセット
          </button>
        </div>
      </div>
    `;
  },

  setSensitivity(value) {
    const settings = Storage.getSettings();
    settings.sensitivity = value;
    Storage.saveSettings(settings);
    this.renderSettings();
    this.toast('体感温度設定を保存しました');
  },

  saveCity() {
    const city = document.getElementById('settings-city').value.trim();
    if (!city) return;
    const settings = Storage.getSettings();
    settings.city = city;
    Storage.saveSettings(settings);
    // Clear weather cache for new city
    localStorage.removeItem(Storage.KEYS.WEATHER_CACHE);
    this.toast(`都市を「${city}」に設定しました`);
  },

  saveApiKey() {
    const key = document.getElementById('settings-apikey').value.trim();
    const settings = Storage.getSettings();
    settings.apiKey = key;
    Storage.saveSettings(settings);
    localStorage.removeItem(Storage.KEYS.WEATHER_CACHE);
    this.toast(key ? 'APIキーを保存しました' : 'デモモードに設定しました');
  },

  loadSampleData() {
    if (confirm('サンプルデータを読み込みますか？\n既存のワードローブに追加されます。')) {
      const samples = SampleWardrobe.map(item => ({
        ...item,
        id: Storage._uuid(),
        createdAt: new Date().toISOString(),
        lastWornAt: null,
        isFavorite: false
      }));
      const existing = Wardrobe.getAll();
      Storage.saveWardrobe([...existing, ...samples]);
      this.renderSettings();
      this.toast(`${samples.length}件のサンプルを追加しました`);
    }
  },

  exportData() {
    const json = Storage.exportData();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tenki-fukusou-backup-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.toast('エクスポートしました');
  },

  importData(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      if (Storage.importData(e.target.result)) {
        this.renderSettings();
        this.toast('インポートしました');
      } else {
        this.toast('インポートに失敗しました');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  },

  resetAll() {
    if (confirm('全てのデータを削除しますか？\nこの操作は取り消せません。')) {
      Storage.clearAll();
      this.renderSettings();
      this.toast('全データをリセットしました');
    }
  }
};
