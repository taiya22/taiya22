/* ===== 天気服装 - Mock Data & Sample Wardrobe ===== */

const MockData = {
  // Seasonal mock weather patterns
  getWeather(month, day) {
    const patterns = this._seasonalPatterns(month);
    const variation = this._dailyVariation(day);
    return {
      city: '東京',
      date: `${new Date().getFullYear()}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,
      periods: [
        {
          label: '朝',
          timeRange: '06:00-09:00',
          temp: Math.round(patterns.morningTemp + variation),
          weather: patterns.morningWeather,
          humidity: patterns.humidity,
          windSpeed: patterns.wind,
          rainProbability: patterns.morningRain
        },
        {
          label: '昼',
          timeRange: '09:00-15:00',
          temp: Math.round(patterns.noonTemp + variation),
          weather: patterns.noonWeather,
          humidity: patterns.humidity - 10,
          windSpeed: patterns.wind + 1,
          rainProbability: patterns.noonRain
        },
        {
          label: '夕',
          timeRange: '15:00-18:00',
          temp: Math.round(patterns.eveningTemp + variation),
          weather: patterns.eveningWeather,
          humidity: patterns.humidity,
          windSpeed: patterns.wind,
          rainProbability: patterns.eveningRain
        },
        {
          label: '夜',
          timeRange: '18:00-23:00',
          temp: Math.round(patterns.nightTemp + variation),
          weather: patterns.nightWeather,
          humidity: patterns.humidity + 5,
          windSpeed: patterns.wind - 1,
          rainProbability: patterns.nightRain
        }
      ]
    };
  },

  getTodayWeather() {
    const now = new Date();
    return this.getWeather(now.getMonth() + 1, now.getDate());
  },

  _dailyVariation(day) {
    return Math.sin(day * 0.7) * 3;
  },

  _seasonalPatterns(month) {
    const base = {
      1:  { morningTemp: 2, noonTemp: 9, eveningTemp: 7, nightTemp: 3, humidity: 45, wind: 4,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 0, noonRain: 10, eveningRain: 15, nightRain: 10 },
      2:  { morningTemp: 3, noonTemp: 10, eveningTemp: 8, nightTemp: 4, humidity: 45, wind: 5,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'sunny', nightWeather: 'cloudy',
            morningRain: 5, noonRain: 10, eveningRain: 10, nightRain: 15 },
      3:  { morningTemp: 7, noonTemp: 15, eveningTemp: 12, nightTemp: 8, humidity: 50, wind: 4,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 10, noonRain: 15, eveningRain: 20, nightRain: 15 },
      4:  { morningTemp: 12, noonTemp: 21, eveningTemp: 18, nightTemp: 14, humidity: 50, wind: 3,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 10, noonRain: 15, eveningRain: 30, nightRain: 20 },
      5:  { morningTemp: 16, noonTemp: 25, eveningTemp: 22, nightTemp: 17, humidity: 55, wind: 3,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'sunny', nightWeather: 'sunny',
            morningRain: 5, noonRain: 10, eveningRain: 15, nightRain: 10 },
      6:  { morningTemp: 20, noonTemp: 26, eveningTemp: 24, nightTemp: 21, humidity: 75, wind: 2,
            morningWeather: 'rainy', noonWeather: 'rainy', eveningWeather: 'cloudy', nightWeather: 'rainy',
            morningRain: 70, noonRain: 60, eveningRain: 50, nightRain: 65 },
      7:  { morningTemp: 25, noonTemp: 33, eveningTemp: 30, nightTemp: 26, humidity: 70, wind: 2,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'sunny', nightWeather: 'sunny',
            morningRain: 10, noonRain: 15, eveningRain: 25, nightRain: 15 },
      8:  { morningTemp: 26, noonTemp: 34, eveningTemp: 31, nightTemp: 27, humidity: 70, wind: 2,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'sunny',
            morningRain: 15, noonRain: 20, eveningRain: 30, nightRain: 15 },
      9:  { morningTemp: 22, noonTemp: 29, eveningTemp: 26, nightTemp: 22, humidity: 65, wind: 3,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 20, noonRain: 25, eveningRain: 30, nightRain: 25 },
      10: { morningTemp: 15, noonTemp: 22, eveningTemp: 19, nightTemp: 15, humidity: 55, wind: 3,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'sunny', nightWeather: 'cloudy',
            morningRain: 10, noonRain: 15, eveningRain: 15, nightRain: 20 },
      11: { morningTemp: 9, noonTemp: 16, eveningTemp: 13, nightTemp: 9, humidity: 50, wind: 3,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 10, noonRain: 10, eveningRain: 15, nightRain: 15 },
      12: { morningTemp: 4, noonTemp: 11, eveningTemp: 8, nightTemp: 4, humidity: 45, wind: 4,
            morningWeather: 'sunny', noonWeather: 'sunny', eveningWeather: 'cloudy', nightWeather: 'cloudy',
            morningRain: 5, noonRain: 10, eveningRain: 10, nightRain: 10 }
    };
    return base[month] || base[4];
  }
};

const SampleWardrobe = [
  // Tops
  { name: '白Tシャツ', category: 'tops', subCategory: 'tshirt', color: '#FFFFFF', colorName: '白', warmthLevel: 1, weatherSuitability: ['sunny', 'cloudy'] },
  { name: 'ボーダーTシャツ', category: 'tops', subCategory: 'tshirt', color: '#1E3A5F', colorName: '紺', warmthLevel: 1, weatherSuitability: ['sunny', 'cloudy'] },
  { name: '白シャツ', category: 'tops', subCategory: 'shirt', color: '#FFFFFF', colorName: '白', warmthLevel: 2, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },
  { name: 'ブルーシャツ', category: 'tops', subCategory: 'shirt', color: '#4A90D9', colorName: '青', warmthLevel: 2, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },
  { name: 'ベージュニット', category: 'tops', subCategory: 'knit', color: '#D4B896', colorName: 'ベージュ', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy', 'rainy', 'snowy'] },
  { name: 'グレーニット', category: 'tops', subCategory: 'knit', color: '#808080', colorName: 'グレー', warmthLevel: 4, weatherSuitability: ['sunny', 'cloudy', 'rainy', 'snowy'] },
  { name: 'ネイビーパーカー', category: 'tops', subCategory: 'hoodie', color: '#1E3A5F', colorName: 'ネイビー', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy'] },
  { name: '黒カーディガン', category: 'tops', subCategory: 'cardigan', color: '#2D3436', colorName: '黒', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },

  // Bottoms
  { name: 'デニムジーンズ', category: 'bottoms', subCategory: 'jeans', color: '#4A6FA5', colorName: 'インディゴ', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },
  { name: 'ベージュチノパン', category: 'bottoms', subCategory: 'chinos', color: '#D4B896', colorName: 'ベージュ', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy'] },
  { name: '黒スラックス', category: 'bottoms', subCategory: 'slacks', color: '#2D3436', colorName: '黒', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy', 'rainy', 'snowy'] },
  { name: 'カーキショートパンツ', category: 'bottoms', subCategory: 'shorts', color: '#6B8E23', colorName: 'カーキ', warmthLevel: 1, weatherSuitability: ['sunny'] },

  // Outerwear
  { name: 'ネイビージャケット', category: 'outerwear', subCategory: 'jacket', color: '#1E3A5F', colorName: 'ネイビー', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy'] },
  { name: 'ベージュトレンチコート', category: 'outerwear', subCategory: 'coat', color: '#D4B896', colorName: 'ベージュ', warmthLevel: 4, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },
  { name: '黒ダウンジャケット', category: 'outerwear', subCategory: 'down', color: '#2D3436', colorName: '黒', warmthLevel: 5, weatherSuitability: ['sunny', 'cloudy', 'snowy'] },
  { name: 'グレーウィンドブレーカー', category: 'outerwear', subCategory: 'windbreaker', color: '#808080', colorName: 'グレー', warmthLevel: 2, weatherSuitability: ['sunny', 'cloudy', 'rainy'] },

  // Shoes
  { name: '白スニーカー', category: 'shoes', subCategory: 'sneakers', color: '#FFFFFF', colorName: '白', warmthLevel: 2, weatherSuitability: ['sunny', 'cloudy'] },
  { name: '黒レザーシューズ', category: 'shoes', subCategory: 'leather', color: '#2D3436', colorName: '黒', warmthLevel: 3, weatherSuitability: ['sunny', 'cloudy'] },
  { name: 'ブラウンブーツ', category: 'shoes', subCategory: 'boots', color: '#8B4513', colorName: 'ブラウン', warmthLevel: 4, weatherSuitability: ['sunny', 'cloudy', 'rainy', 'snowy'] },
  { name: 'レインブーツ', category: 'shoes', subCategory: 'rain_boots', color: '#2D3436', colorName: '黒', warmthLevel: 3, weatherSuitability: ['rainy', 'snowy'] },

  // Accessories
  { name: '折り畳み傘', category: 'accessories', subCategory: 'umbrella', color: '#1E3A5F', colorName: 'ネイビー', warmthLevel: 0, weatherSuitability: ['rainy'] },
  { name: 'ベージュマフラー', category: 'accessories', subCategory: 'scarf', color: '#D4B896', colorName: 'ベージュ', warmthLevel: 4, weatherSuitability: ['sunny', 'cloudy', 'snowy'] },
  { name: 'ニット帽', category: 'accessories', subCategory: 'hat', color: '#808080', colorName: 'グレー', warmthLevel: 4, weatherSuitability: ['sunny', 'cloudy', 'snowy'] },
  { name: 'サングラス', category: 'accessories', subCategory: 'sunglasses', color: '#2D3436', colorName: '黒', warmthLevel: 0, weatherSuitability: ['sunny'] },
  { name: 'キャップ', category: 'accessories', subCategory: 'cap', color: '#2D3436', colorName: '黒', warmthLevel: 1, weatherSuitability: ['sunny', 'cloudy'] },
  { name: '手袋', category: 'accessories', subCategory: 'gloves', color: '#2D3436', colorName: '黒', warmthLevel: 5, weatherSuitability: ['snowy', 'cloudy'] }
];
