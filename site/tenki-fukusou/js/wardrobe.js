/* ===== 天気服装 - Wardrobe Manager ===== */

const Wardrobe = {
  CATEGORIES: {
    tops: { label: 'トップス', icon: '\uD83D\uDC55', subCategories: {
      tshirt: 'Tシャツ', shirt: 'シャツ', knit: 'ニット',
      hoodie: 'パーカー', cardigan: 'カーディガン', tank: 'タンクトップ'
    }},
    bottoms: { label: 'ボトムス', icon: '\uD83D\uDC56', subCategories: {
      jeans: 'ジーンズ', chinos: 'チノパン', slacks: 'スラックス',
      shorts: 'ショートパンツ', skirt: 'スカート'
    }},
    outerwear: { label: 'アウター', icon: '\uD83E\uDDE5', subCategories: {
      jacket: 'ジャケット', coat: 'コート', down: 'ダウン',
      windbreaker: 'ウィンドブレーカー', raincoat: 'レインコート', vest: 'ベスト'
    }},
    shoes: { label: '靴', icon: '\uD83D\uDC5F', subCategories: {
      sneakers: 'スニーカー', leather: 'レザーシューズ', boots: 'ブーツ',
      sandals: 'サンダル', rain_boots: 'レインブーツ'
    }},
    accessories: { label: '小物', icon: '\uD83C\uDFA9', subCategories: {
      umbrella: '傘', hat: '帽子', cap: 'キャップ',
      scarf: 'マフラー', gloves: '手袋', sunglasses: 'サングラス'
    }}
  },

  COLORS: [
    { hex: '#FFFFFF', name: '白' },
    { hex: '#2D3436', name: '黒' },
    { hex: '#808080', name: 'グレー' },
    { hex: '#1E3A5F', name: 'ネイビー' },
    { hex: '#4A90D9', name: '青' },
    { hex: '#6B8E23', name: 'カーキ' },
    { hex: '#D4B896', name: 'ベージュ' },
    { hex: '#8B4513', name: 'ブラウン' },
    { hex: '#C0392B', name: '赤' },
    { hex: '#E91E8C', name: 'ピンク' },
    { hex: '#F5A623', name: 'オレンジ' },
    { hex: '#F1C40F', name: '黄' }
  ],

  getAll() {
    return Storage.getWardrobe();
  },

  getByCategory(category) {
    if (category === 'all') return this.getAll();
    return this.getAll().filter(item => item.category === category);
  },

  add(item) {
    const items = this.getAll();
    const newItem = {
      ...item,
      id: Storage._uuid(),
      createdAt: new Date().toISOString(),
      lastWornAt: null,
      isFavorite: false
    };
    items.push(newItem);
    Storage.saveWardrobe(items);
    return newItem;
  },

  update(id, updates) {
    const items = this.getAll();
    const index = items.findIndex(i => i.id === id);
    if (index === -1) return null;
    items[index] = { ...items[index], ...updates };
    Storage.saveWardrobe(items);
    return items[index];
  },

  remove(id) {
    const items = this.getAll().filter(i => i.id !== id);
    Storage.saveWardrobe(items);
  },

  markWorn(id) {
    this.update(id, { lastWornAt: new Date().toISOString() });
  },

  getCategoryLabel(category) {
    return this.CATEGORIES[category]?.label || category;
  },

  getCategoryIcon(category) {
    return this.CATEGORIES[category]?.icon || '👕';
  },

  getSubCategoryLabel(category, subCategory) {
    return this.CATEGORIES[category]?.subCategories[subCategory] || subCategory;
  },

  getColorName(hex) {
    const color = this.COLORS.find(c => c.hex.toLowerCase() === hex.toLowerCase());
    return color ? color.name : '';
  },

  getWarmthLabel(level) {
    const labels = ['', '薄手', 'やや薄手', '普通', 'やや厚手', '厚手'];
    return labels[level] || '';
  },

  getWarmthStars(level) {
    return '★'.repeat(level) + '☆'.repeat(5 - level);
  }
};
